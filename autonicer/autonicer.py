#! /usr/bin/env python3

# AutoNICER
# Copyright 2021 Nicholas Kuechel
# License Apache 2.0

import subprocess as sp
import os
import pandas as pd
import time
import numpy as np
from astroquery.heasarc import Heasarc
from astropy.table import Table
from astropy.visualization import time_support
from astropy.visualization import quantity_support
from astropy.time import Time
import datetime


class AutoNICER(object):
    def __init__(self):
        self.st = True
        self.xti = 0
        self.observations = []
        self.years = []
        self.months = []
        self.ras = []
        self.decs = []

        print("##############  Auto NICER  ##############")
        print()
        self.obj = str(input("Target: "))
        self.bc_sel = str(input("Apply Bary-Center Correction: [y] "))
        self.q_set = str(input("Write Output Que: [n] "))
        self.tar_sel = str(input("Compress XTI files (.tar.gz): [y] "))
        self.q_path = 0
        self.q_name = 0
        if self.q_set == "y":
            self.q_path = str(input("Input Que: "))
            if self.q_path[0] == r"'" or self.que_path[0] == r'"':
                self.q_path = self.q_path.replace("'", "")
                self.q_path = self.q_path.replace(" ", "")
                self.q_path = self.q_path.replace('"', "")
            else:
                pass
        else:
            pass

    def call_nicer(self):
        """
        Querys the nicermastr catalog for all observations of the specified source(self.obj)
        """
        heasarc = Heasarc()
        quantity_support()
        time_support()
        xti = heasarc.query_object(
            self.obj, mission="nicermastr"
        )  # calls NICER master catalogue for an input object
        xti = Table(xti).to_pandas()
        cnt = 0
        for i in xti["OBSID"]:  # converts the form of the NICER obsid's to strings
            i = i.decode()
            xti.loc[cnt, "OBSID"] = str(i)
            cnt = cnt + 1
        cnt = 0
        for i in xti["TIME"]:  # converts times from mjd to datetime format
            t0 = Time(i, format="mjd").to_datetime()
            xti.loc[cnt, "TIME"] = t0
            cnt = cnt + 1
        self.xti = xti

    def make_cycle(self):
        cycle = []
        for i in self.xti["OBSID"]:
            cycle.append(np.floor(float(i) * 10 ** (-9)))
        self.xti["Cycle#"] = cycle
        return self.xti

    def sel_obs(self, enter):
        self.observations.append(enter)
        row = self.xti.loc[self.xti["OBSID"] == enter]
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

    def rm_obs(self, cmd):
        if cmd == "all":
            self.observations.clear()
            self.years.clear()
            self.months.clear()
            self.ras.clear()
            self.decs.clear()
        else:
            n = self.observations.index(cmd)
            del self.observations[n]
            del self.years[n]
            del self.months[n]
            del self.ras[n]
            del self.decs[n]

    def command_center(self):
        # prompts the user to select obs to be pulled and reduced
        while self.st == True:
            enter = str(input("autoNICER > ")).split(" ")
            if enter[0] == "done" or enter[0] == "Done":
                # Command to finish selection of obs.
                self.st = False
            elif enter[0] == "sel" or enter[0] == "Sel" or enter[0] == "SEL":
                # displays all selected observations in the cmd line
                print("Observations Selected:")
                for i in self.observations:
                    print(i)
            elif enter[0] == None or enter[0] == "":
                # Error message for nothing entered in the prompt
                print("Nothing entered...")
                print("!!!ENTER SOMETHING!!!")
            elif enter[0] == "back" or enter[0] == "Back" or enter[0] == "BACK":
                # Deletes the previously entered obsid
                print("Old Que: " + str(self.observations))
                del self.observations[-1]
                print("New Que: " + str(self.observations))
            elif enter[0] == "cycle":
                row = self.make_cycle().loc[
                    self.make_cycle()["Cycle#"] == float(enter[1])
                ]
                for i in row["OBSID"]:
                    self.sel_obs(i)
            elif enter[0] == "rm":
                self.rm_obs(enter[1])
            elif enter[0] == "exit":
                exit()
            else:
                try:
                    if int(enter[0]) > (10 ** 8):
                        self.sel_obs(enter[0])
                except:
                    print("Unknown Entry")

    def nicer_compress(self):
        """
        compresses .evt files
        """
        print("##########  .tar.gz compression  ##########")

        def tar_compr(file):
            """
            commands for a .tar.gz compression of a single file and removal of original file after compression is complete
            """
            if file == "":
                pass
            else:
                sp.call(f"tar czvf {file}.tar.gz {file}", shell=True)
                sp.call(f"rm -r {file}", shell=True)

        print("Compressing ufa.evt files")
        print("----------------------------------------------------------")
        # files and loop to compress the ufa files
        files = sp.run("ls *ufa.evt", shell=True, capture_output=True, encoding="utf-8")
        for i in str(files.stdout).split("\n"):
            tar_compr(i)

        # compression of the non-bc mpu7_cl.evt file if barycenter correction is selected
        if self.bc_sel.lower() == "n":
            pass
        else:
            print("")
            print("Compressing cl.evt files")
            print("----------------------------------------------------------")
            # files and liip to compress the cl files
            cl_file = sp.run(
                "ls ni*cl.evt", shell=True, capture_output=True, encoding="utf-8"
            )
            for i in str(cl_file.stdout).split("\n"):
                tar_compr(i)

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

        count = 0
        for obsid in self.observations:
            print("")
            print("--------------------------------------------------------------")
            print("               Prosessing OBSID: " + str(obsid))
            print("--------------------------------------------------------------")
            pull_templ = (
                f"{downCommand}{self.years[count]}_{self.months[count]}//{obsid}"
            )
            end_args = f"--show-progress --progress=bar:force"
            print("Downloading xti data...")
            sp.call(f"{pull_templ}/xti/ {end_args}", shell=True)
            print("Downloadng log data...")
            sp.call(f"{pull_templ}/log/ {end_args}", shell=True)
            print("Downloading auxil data...")
            sp.call(f"{pull_templ}/auxil/ {end_args}", shell=True)
            sp.call(f"nicerl2 indir={obsid}/ clobber=yes", shell=True)
            if self.bc_sel.lower() == "n":
                pass
            else:
                sp.call(
                    f"barycorr infile={obsid}/xti/event_cl/ni{obsid}_0mpu7_cl.evt outfile={obsid}/xti/event_cl/bc{obsid}_0mpu7_cl.evt orbitfiles={obsid}/auxil/ni{obsid}.orb refframe=ICRS ra={self.ras[count]} dec={self.decs[count]} ephem=JPLEPH.430",
                    shell=True,
                )

            base_dir = os.getcwd()
            os.chdir(f"{obsid}/xti/event_cl/")
            if self.tar_sel == "n" or self.tar_sel == "N":
                pass
            else:
                self.nicer_compress()
            os.chdir(base_dir)
            if self.q_set == "y":
                read_q = pd.read_csv(self.q_path)
                newline = pd.Series(
                    data=[
                        f"{base_dir}/{obsid}/xti/event_cl/bc{obsid}_0mpu7_cl.evt",
                        f"NI{obsid}",
                    ],
                    index=["Input", "Name"],
                )
                read_q = read_q.append(newline, ignore_index=True)
                read_q.to_csv(self.q_path, index=False)
            else:
                pass

            count = count + 1

    def main(self):
        self.call_nicer()
        self.command_center()
        self.pull_reduce()