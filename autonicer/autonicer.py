#! /usr/bin/env python3

# AutoNICER
# Copyright 2022-2023 Nicholas Kuechel
# License Apache 2.0

import subprocess as sp
import os
import pandas as pd
import time
import numpy as np
from astroquery.heasarc import Heasarc
from astroquery import exceptions
from astropy.table import Table
from astropy.time import Time
from termcolor import colored
import datetime
import gzip
import shutil
import warnings
import glob
import concurrent.futures
from astropy.utils.exceptions import AstropyWarning


def get_caldb_ver():
    """
    Gets most up to nicer caldb version
    """
    caldb = sp.run("nicaldbver", shell=True, capture_output=True, encoding="utf-8")
    convo = str(caldb.stdout).split("\n")
    return convo[0]


class AutoNICER(object):
    def __init__(self, src=None, bc=None, comp=None):
        self.st = True
        self.xti = 0
        self.observations = []
        self.years = []
        self.months = []
        self.ras = []
        self.decs = []
        self.caldb_ver = ""

        print(colored("##############  Auto NICER  ##############", "cyan"))
        print()
        self.obj = src
        self.bc_sel = bc
        self.q_set = "n"
        self.tar_sel = comp
        self.q_path = 0
        self.q_name = 0
        self.startup()

    def startup(self):
        """
        Prompted setting for if autonicer is just called w/ no paramerters set
        """

        def null_parse(var):
            if var == "" or var is True:
                var = "y"
            else:
                var = "n"
            return var

        logq = False
        if self.obj is None and self.bc_sel is None and self.tar_sel is None:
            logq = True
        if self.obj is None:
            self.obj = str(input("Target: "))
        if self.bc_sel is None:
            self.bc_sel = str(input("Apply Bary-Center Correction: [y] "))
        if self.tar_sel is None:
            self.tar_sel = str(input("Compress XTI files (.gz): [y] "))
        if logq is True:
            self.q_set = str(input("Write Output Log: [n] "))
            self.q_set = self.q_set.lower()
            if self.q_set == "y":
                ne = str(input("New or Add to existing Log: "))
                if ne.lower() == "add":
                    self.q_path = str(input("Input Que: "))
                    if self.q_path[0] == r"'" or self.que_path[0] == r'"':
                        self.q_path = self.q_path.replace("'", "")
                        self.q_path = self.q_path.replace(" ", "")
                        self.q_path = self.q_path.replace('"', "")
                elif ne.lower() == "new":
                    self.q_name = str(input("Name of output log file (no .csv): "))

                else:
                    self.q_set = "n"
        self.bc_sel = null_parse(self.bc_sel)
        self.tar_sel = null_parse(self.tar_sel)

    def call_nicer(self):
        """
        Querys the nicermastr catalog for all observations of the specified source(self.obj)
        """
        heasarc = Heasarc()
        try:
            warnings.simplefilter("ignore", category=AstropyWarning)
            xti = heasarc.query_object(
                self.obj, mission="nicermastr"
            )  # calls NICER master catalogue for an input object
        except exceptions.InvalidQueryError:
            print(colored(f"UNABLE TO RESOLVE {self.obj} in HEASARC!", "red"))
            print(colored(f"Exiting ...", "red"))
            exit()
        else:
            xti = Table(xti).to_pandas()
            cnt = 0
            for i in xti["OBSID"]:  # converts the form of the NICER obsid's to strings
                i = i.decode()
                xti.loc[cnt, "OBSID"] = str(i).replace(" ", "")
                cnt = cnt + 1
            xti["TIME"] = Time(xti["TIME"], format="mjd").to_datetime()
            self.xti = xti

    def make_cycle(self):
        """
        Makes a Cycle# column in resulting query table from obsid table
        """
        cycle = []
        for i in self.xti["OBSID"]:
            convo = np.floor(float(i) * 10 ** (-9))
            cycle.append(int(convo))
        self.xti["Cycle#"] = cycle
        return self.xti

    def sel_obs(self, enter):
        """
        Selects and queues up the obsid desired
        """
        selstate = True
        dup_cnt = self.observations.count(enter)
        if dup_cnt != 0:
            print(f"{enter} is already queued up... ignoring")
        else:
            try:
                row = self.xti.loc[self.xti["OBSID"] == enter]
                print(f"Adding {enter}")
                self.observations.append(enter)
                dt = row["TIME"]
                row.reset_index(drop=True, inplace=True)
                dt.reset_index(drop=True, inplace=True)
                year = str(dt[0].year)
                self.years.append(year)
                month = dt[0].month
                # basic if else statement to fix single digit months not having a zero out front
                if month < 10:
                    month = "0" + str(month)
                else:
                    month = str(month)
                self.months.append(month)
                self.ras.append(row["RA"][0])
                self.decs.append(row["DEC"][0])
                return selstate
            except KeyError:
                print(colored("OBSID NOT FOUND!", "red"))
                del self.observations[-1]
                selstate = False
                return selstate

    def rm_obs(self, cmd):
        """
        Manages the removal command types
        """
        if cmd == "all":
            self.observations.clear()
            self.years.clear()
            self.months.clear()
            self.ras.clear()
            self.decs.clear()
        else:
            n = 0
            if cmd == "back":
                n = -1
            else:
                n = self.observations.index(cmd)
            del self.observations[n]
            del self.years[n]
            del self.months[n]
            del self.ras[n]
            del self.decs[n]

    def commands(self, enter):
        if enter[0].lower() == "done":
            # Command to finish selection of obs.
            self.st = False
            self.pull_reduce()

        elif enter[0].lower() == "sel":
            # displays all selected observations in the cmd line
            print("Observations Selected:")
            for i in self.observations:
                print(i)
            return True

        elif enter[0] == None or enter[0] == "":
            # Error message for nothing entered in the prompt
            print("Nothing entered...")
            print("!!!ENTER SOMETHING!!!")
            return True

        elif enter[0].lower() == "back":
            # Deletes the previously entered obsid
            try:
                print(f"Removing {self.observations[-1]}")
            except IndexError:
                print(colored("Nothing found to Remove!", "red"))
            else:
                self.rm_obs("back")
            return True

        elif enter[0].lower() == "cycle":
            row = self.make_cycle().loc[self.make_cycle()["Cycle#"] == float(enter[1])]
            for i in row["OBSID"]:
                self.sel_obs(i)
            return True

        elif enter[0].lower() == "rm":
            try:
                self.rm_obs(enter[1])
            except ValueError:
                print(colored("Nothing found to Remove!", "red"))
            return True

        elif enter[0] == "settings":
            print(f"Target: {self.obj}")
            print(f"Barycenter Correction: {self.bc_sel}")
            if self.q_set == "y":
                print(f"Log Name: {q_name}")
                print(f"Output Log: {self.q_set}")
            print(f".gz compresion: {self.tar_sel}")

        elif enter[0] == "exit":
            exit()

        else:
            try:
                if int(enter[0]) > (10**8):
                    obsst = self.sel_obs(enter[0])
                    return obsst
                else:
                    raise ValueError
            except ValueError:
                print("Unknown Entry")
                return False

    def command_center(self, enter=None):
        """
        Function to manage all the commands
        """
        # prompts the user to select obs to be pulled and reduced
        orig_in = enter
        cmdstate = None
        self.st = True
        while self.st == True:
            if orig_in != None:
                cmdstate = self.commands(enter.split(" "))
                self.st = False
            else:
                cmdstate = enter = str(
                    input(colored("autoNICER", "blue") + " > ")
                ).split(" ")
                self.commands(enter)
        return cmdstate

    def nicer_compress(self):
        """
        compresses .evt files
        """
        print(colored("##########  .gz compression  ##########", "green"))

        def gz_comp(file):
            """
            .gz compression of a single file and removal of original file after compression
            """
            if file == "":
                pass
            else:
                with open(file, "rb") as f_in:
                    with gzip.open(f"{file}.gz", "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(file)
                return f"{file} -> {file}.gz"

        print("Compressing ufa.evt files")
        print("----------------------------------------------------------")
        # files and loop to compress the ufa files
        files = glob.glob("*ufa.evt")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            comps = [executor.submit(gz_comp, i) for i in files]

            for j in concurrent.futures.as_completed(comps):
                print(j.result())

        # compression of the non-bc mpu7_cl.evt file if barycenter correction is selected
        if self.bc_sel.lower() == "y":
            print("Compressing cl.evt files")
            print("----------------------------------------------------------")
            cl_file = glob.glob("ni*cl.evt")
            for i in cl_file:
                print(gz_comp(i))
        print()

    def add2q(self, q, base_dir, obsid):
        """
        Adds processed data to existing log
        """
        newline = pd.DataFrame(
            {
                "Input": [f"{base_dir}/{obsid}/xti/event_cl/bc{obsid}_0mpu7_cl.evt"],
                "OBSID": [f"NI{obsid}"],
                "CALDB": [f"{self.caldb_ver}"],
                "DateTime": [f"{datetime.datetime.now()}"],
            },
        )
        q = pd.concat([q, newline])
        q.to_csv(self.q_path, index=False)

    def reduce(self, obsid):
        """
        Performs standardized data reduction scheme calling nicerl2 and barycorr if set
        """
        sp.call(f"nicerl2 indir={obsid}/ clobber=yes", shell=True)
        obsindex = self.observations.index(obsid)
        if self.bc_sel.lower() == "y":
            sp.call(
                f"barycorr infile={obsid}/xti/event_cl/ni{obsid}_0mpu7_cl.evt outfile={obsid}/xti/event_cl/bc{obsid}_0mpu7_cl.evt orbitfiles={obsid}/auxil/ni{obsid}.orb refframe=ICRS ra={self.ras[obsindex]} dec={self.decs[obsindex]} ephem=JPLEPH.430 clobber=yes",
                shell=True,
            )

    def pull_reduce(self):
        """
        Downloads the NICER data
        Puts the retrieved data through a standardized data reduction scheme
        """
        downCommand = (
            "wget -q -nH --no-check-certificate --cut-dirs=5 -r -l0 -c -N -np -R "
            + "'index*'"
            + " -erobots=off --retr-symlinks https://heasarc.gsfc.nasa.gov/FTP/nicer/data/obs/"
        )

        for obsid in self.observations:
            qindex = self.observations.index(obsid)
            print("")
            print("--------------------------------------------------------------")
            print("             Prosessing OBSID: " + colored(str(obsid), "cyan"))
            print("--------------------------------------------------------------")
            pull_templ = (
                f"{downCommand}{self.years[qindex]}_{self.months[qindex]}//{obsid}"
            )
            end_args = f"--show-progress --progress=bar:force"
            print(colored("Downloading xti data...", "green"))
            sp.call(f"{pull_templ}/xti/ {end_args}", shell=True)
            print(colored("Downloadng log data...", "green"))
            sp.call(f"{pull_templ}/log/ {end_args}", shell=True)
            print(colored("Downloading auxil data...", "green"))
            sp.call(f"{pull_templ}/auxil/ {end_args}", shell=True)
            self.caldb_ver = get_caldb_ver()
            self.reduce(obsid)

            base_dir = os.getcwd()
            os.chdir(f"{obsid}/xti/event_cl/")
            if self.tar_sel == "n" or self.tar_sel == "N":
                pass
            else:
                self.nicer_compress()
            os.chdir(base_dir)
            if self.q_set == "y" and self.q_path != 0:
                read_q = pd.read_csv(self.q_path)
                self.add2q(read_q, base_dir, obsid)
            elif self.q_set == "y" and self.q_path == 0:
                q = pd.DataFrame(
                    {"Input": [], "OBSID": [], "CALDB": [], "DateTime": []}
                )
                self.q_path = f"{base_dir}/{self.q_name}.csv"
                self.add2q(q, base_dir, obsid)
            else:
                pass
