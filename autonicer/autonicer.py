# AutoNICER
# Copyright 2022-2025 Nicholas Kuechel
# License Apache 2.0

import subprocess as sp
import os
import sys
import pandas as pd
import numpy as np
from astroquery.heasarc import Heasarc
from astropy.coordinates import SkyCoord
from astroquery import exceptions
from astropy.time import Time
from termcolor import colored
import datetime
import gzip
import shutil
import glob
import concurrent.futures
import logging
import argparse as ap
from .reprocess import reprocess_check
from .reprocess import inlist
from importlib.metadata import version


AUTONICER = os.path.basename(sys.argv[0])
VERSION = version('autonicer')
logger = logging.getLogger(AUTONICER)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


def get_caldb_ver():
    """
    Gets most up to nicer caldb version
    """
    caldb = sp.run("nicaldbver", shell=True,
                   capture_output=True, encoding="utf-8")
    convo = str(caldb.stdout).split("\n")
    return convo[0]


class AutoNICER(object):
    def __init__(self, src=None, bc=None, comp=None):
        self.st = True
        self.xti = 0
        self.queue = []
        self.caldb_ver = ""

        logger.info(colored("##########  Auto NICER  ##########\n",
                    "cyan"))
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
                    self.q_name = str(input("Name of log file (no .csv): "))

                else:
                    self.q_set = "n"
        self.bc_sel = null_parse(self.bc_sel)
        self.tar_sel = null_parse(self.tar_sel)

    def call_nicer(self):
        """
        Querys the nicermastr catalog for all observations
        of the specified source(self.obj)
        """
        heasarc = Heasarc()
        try:
            Heasarc.clear_cache()
            position = SkyCoord.from_name(self.obj)
            xti = heasarc.query_region(
                position, catalog="nicermastr"
            )  # calls NICER master catalogue for an input object
        except exceptions.InvalidQueryError:
            logger.info(colored(f"UNABLE TO RESOLVE {self.obj} in HEASARC!",
                                "red"))
            logger.info(colored("Exiting ...", "red"))
            exit()
        else:
            xti = xti.to_pandas()
            xti.columns = [name.upper() for name in xti.columns]
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
        queued_obsids = [i["OBSID"] for i in self.queue]
        if enter in queued_obsids:
            logger.info(f"{enter} is already queued up... ignoring")
        else:
            try:
                row = self.xti.loc[self.xti["OBSID"] == enter]
                dt = row["TIME"]
                row.reset_index(drop=True, inplace=True)
                dt.reset_index(drop=True, inplace=True)
                year = str(dt[0].year)
                month = dt[0].month
                # basic if else statement to fix single digit months
                # not having a zero out front
                if month < 10:
                    month = "0" + str(month)
                else:
                    month = str(month)
                sel_dict = {"OBSID": enter,
                            "month": month,
                            "year": year,
                            "ra": row["RA"][0],
                            "dec": row["DEC"][0]
                            }
                logger.info(f"Adding {enter}")
                self.queue.append(sel_dict)
                return selstate
            except KeyError:
                logger.info(colored("OBSID NOT FOUND!", "red"))
                selstate = False
                return selstate

    def rm_obs(self, cmd):
        """
        Manages the removal command types
        """
        if cmd.lower() == "all":
            self.queue.clear()
        else:
            n = 0
            if cmd.lower() == "back":
                n = -1
            else:
                sel_obsids = [i["OBSID"] for i in self.queue]
                n = sel_obsids.index(cmd)
            del self.queue[n]

    def commands(self, enter):
        if enter[0].lower() == "done":
            # Command to finish selection of obs.
            self.st = False
            self.pull_reduce()

        elif enter[0].lower() == "sel":
            # displays all selected observations in the cmd line
            logger.info("Observations Selected:")
            for i in self.queue:
                logger.info(i["OBSID"])
            return True

        elif enter[0] is None or enter[0] == "":
            # Error message for nothing entered in the prompt
            logger.info("Nothing entered...")
            logger.info("!!!ENTER SOMETHING!!!")
            return True

        elif enter[0].lower() == "back":
            # Deletes the previously entered obsid
            try:
                logger.info(f"Removing {self.queue[-1]['OBSID']}")
            except IndexError:
                logger.info(colored("Nothing found to Remove!", "red"))
            else:
                self.rm_obs("back")
            return True

        elif enter[0].lower() == "cycle":
            row = self.make_cycle().loc[
                self.make_cycle()["Cycle#"] == float(enter[1])
            ]
            for i in row["OBSID"]:
                self.sel_obs(i)
            return True

        elif enter[0].lower() == "rm":
            try:
                self.rm_obs(enter[1])
            except ValueError:
                logger.info(colored("Nothing found to Remove!", "red"))
            return True

        elif enter[0] == "settings":
            logger.info(f"Target: {self.obj}")
            logger.info(f"Barycenter Correction: {self.bc_sel}")
            if self.q_set == "y":
                logger.info(f"Log Name: {self.q_name}")
                logger.info(f"Output Log: {self.q_set}")
            logger.info(f".gz compresion: {self.tar_sel}")

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
                logger.info("Unknown Entry")
                return False

    def command_center(self, enter=None):
        """
        Function to manage all the commands
        """
        # prompts the user to select obs to be pulled and reduced
        orig_in = enter
        cmdstate = None
        self.st = True
        while self.st is True:
            if orig_in is not None:
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
        logger.info(colored("##########  .gz compression  ##########",
                    "green"))

        def gz_comp(file):
            """
            .gz compression of a single file and
            removal of original file after compression
            """
            if file == "":
                pass
            else:
                with open(file, "rb") as f_in:
                    with gzip.open(f"{file}.gz", "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(file)
                return f"{file} -> {file}.gz"

        logger.info("Compressing ufa.evt files")
        logger.info(("-" * 50) + "\n")
        # files and loop to compress the ufa files
        files = glob.glob("*ufa.evt")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            comps = [executor.submit(gz_comp, i) for i in files]

            for j in concurrent.futures.as_completed(comps):
                logger.info(j.result())

        # compression of the non-bc mpu7_cl.evt file
        # if barycenter correction is selected
        if self.bc_sel.lower() == "y":
            logger.info("Compressing cl.evt files")
            logger.info(("-" * 50) + "\n")
            cl_file = glob.glob("ni*cl.evt")
            for i in cl_file:
                logger.info(gz_comp(i))

    def add2q(self, q, base_dir, obsid):
        """
        Adds processed data to existing log
        """
        newline = pd.DataFrame(
            {
                "Input": [(f"{base_dir}/{obsid}/xti/"
                           f"event_cl/bc{obsid}_0mpu7_cl.evt")],
                "OBSID": [f"NI{obsid}"],
                "CALDB": [f"{self.caldb_ver}"],
                "DateTime": [f"{datetime.datetime.now()}"],
            },
        )
        q = pd.concat([q, newline])
        q.to_csv(self.q_path, index=False)

    def reduce(self, data):
        """
        Performs standardized data reduction scheme calling
        nicerl2 and barycorr if set
        """
        sp.call(f"nicerl2 indir={data['OBSID']}/ clobber=yes", shell=True)
        if self.bc_sel.lower() == "y":
            sp.call(
                (f"barycorr infile={data['OBSID']}/xti/event_cl/"
                 f"ni{data['OBSID']}_0mpu7_cl.evt outfile={data['OBSID']}"
                 f"/xti/event_cl/bc{data['OBSID']}_0mpu7_cl.evt "
                 f"orbitfiles={data['OBSID']}/auxil/ni{data['OBSID']}.orb "
                 f"refframe=ICRS ra={data['ra']} "
                 f"dec={data['dec']} ephem=JPLEPH.430 clobber=yes"),
                shell=True,
            )

    def pull_reduce(self):
        """
        Downloads the NICER data
        Puts the retrieved data through a standardized data reduction scheme
        """
        downCommand = (
            "wget -q -nH --no-check-certificate "
            "--cut-dirs=5 -r -l0 -c -N -np -R "
            "'index*'"
            " -erobots=off --retr-symlinks "
            "https://heasarc.gsfc.nasa.gov/FTP/nicer/data/obs/"
        )

        for data in self.queue:
            logger.info("")
            logger.info("-" * 60)
            logger.info((" " * 10) + "Prosessing OBSID: " +
                        colored(str(data["OBSID"]), "cyan"))
            logger.info("-" * 60)
            pull_templ = (
                f"{downCommand}{data['year']}_"
                f"{data['month']}//{data['OBSID']}"
            )
            end_args = "--show-progress --progress=bar:force"
            logger.info(colored("Downloading xti data...", "green"))
            sp.call(f"{pull_templ}/xti/ {end_args}", shell=True)
            logger.info(colored("Downloadng log data...", "green"))
            sp.call(f"{pull_templ}/log/ {end_args}", shell=True)
            logger.info(colored("Downloading auxil data...", "green"))
            sp.call(f"{pull_templ}/auxil/ {end_args}", shell=True)
            self.caldb_ver = get_caldb_ver()
            self.reduce(data)

            base_dir = os.getcwd()
            os.chdir(f"{data['OBSID']}/xti/event_cl/")
            if self.tar_sel.lower() == "n":
                pass
            else:
                self.nicer_compress()
            os.chdir(base_dir)
            if self.q_set == "y" and self.q_path != 0:
                read_q = pd.read_csv(self.q_path)
                self.add2q(read_q, base_dir, data['OBSID'])
            elif self.q_set == "y" and self.q_path == 0:
                q = pd.DataFrame(
                    {"Input": [], "OBSID": [], "CALDB": [], "DateTime": []}
                )
                self.q_path = f"{base_dir}/{self.q_name}.csv"
                self.add2q(q, base_dir, data['OBSID'])
            else:
                pass


def run(args=None):
    p = ap.ArgumentParser(
        description=("A program for piplining NICER data reduction. "
                     "Run by just typing autonicer.")
    )

    p.add_argument(
        "-src",
        "--src",
        help="Set the src from the command line",
        type=str,
    )

    p.add_argument(
        "-checkcal",
        "--checkcal",
        help=("Checks if mpu7_cl.evt are up to date "
              "with latest NICER calibrations"),
        action="store_true",
        default=False,
    )

    p.add_argument(
        "-reprocess",
        "--reprocess",
        help="Engages a reprocessing of calibrations ",
        action="store_true",
        default=False,
    )

    p.add_argument(
        "-bc",
        "--bc",
        help=("Engages option for a barycenter correction "
              "in data reduction procedure"),
        action="store_true",
        default=None,
    )

    p.add_argument(
        "-compress",
        "--compress",
        help="Engages option for .gz compression of ufa.evt files",
        action="store_true",
        default=None,
    )

    p.add_argument(
        "-i",
        "-inlist",
        "--inlist",
        help=("Input .csv list with path to OBSID dirs or mpu7_cl.evt "
              "files for use with --reprocess and/or --checkcal"),
        default=None,
        nargs="+",
    )

    argp = p.parse_args(args)
    if argp.checkcal is True or argp.reprocess is True:
        if argp.inlist is None:
            reprocess_check(argp)
        else:
            inlist(argp)
    else:
        an = AutoNICER(argp.src, argp.bc, argp.compress)
        an.call_nicer()
        an.command_center()
