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
import asyncio
import aiohttp
from pathlib import Path
from tqdm import tqdm


AUTONICER = os.path.basename(sys.argv[0])
VERSION = version('autonicer')
logger = logging.getLogger(AUTONICER)


def get_caldb_ver():
    """
    Gets most up to nicer caldb version
    """
    caldb = sp.run("nicaldbver", shell=True,
                   capture_output=True, encoding="utf-8")
    convo = str(caldb.stdout).split("\n")
    return convo[0]


async def download_file(url: str) -> None:
    """
    Downloads data file from a specified url

    Parameters:
    url: str, url to fetch data from
    """
    split_url = url.split("/")
    file = '/'.join(split_url[7:])
    file = Path(file)
    file.parent.mkdir(exist_ok=True, parents=True)
    file_path = file.resolve()
    file_name = file.name
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                file_size = int(resp.headers['Content-Length'])
                with open(file_path, 'wb') as fd:
                    progress = tqdm(total=file_size, desc=file_name,
                                    unit="B", unit_scale=True, leave=False)
                    while True:
                        try:
                            chunk = await resp.content.read(1024)
                        except (asyncio.CancelledError,
                                aiohttp.ClientResponseError) as e:
                            logger.error(f"ERROR: Chunk read error: {e}\n")
                            break
                        if not chunk:
                            progress.close()
                            break
                        fd.write(chunk)
                        progress.update(len(chunk))
                    progress.close()
            else:
                logger.info(f"Download: {file_name} failed "
                            f"with code: {resp.status}\n")


async def download_obsid(urls: list) -> None:
    """
    Downloads all files from urls to make up an entire obsid dataset

    Parameters:
    urls: list, urls to all files that make up an entire obsid dataset
    """
    sem = asyncio.Semaphore(4)
    async with sem:
        tasks = []
        for url in urls:
            task = asyncio.create_task(download_file(url))
            tasks.append(task)
        await asyncio.gather(*tasks)


class AutoNICER(object):
    def __init__(self, src=None, bc=None, comp=None):
        self.st = True
        self.xti = 0
        self.queue = []
        self.caldb_ver = ""
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

        logger.info("\nCompressing ufa.evt files")
        logger.info("-" * 50)
        # files and loop to compress the ufa files
        files = glob.glob("*ufa.evt")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            comps = [executor.submit(gz_comp, i) for i in files]

            for j in concurrent.futures.as_completed(comps):
                logger.info(j.result())

        # compression of the non-bc mpu7_cl.evt file
        # if barycenter correction is selected
        if self.bc_sel.lower() == "y":
            logger.info("\nCompressing cl.evt files")
            logger.info("-" * 50)
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

    def _make_download_links(self, info: dict) -> dict:
        """
        Makes all the download links for each file of an OBSID

        Parameters:
        info: dict, information from AutoNICER.queue
                    required to make all download links
                    (OSBID, year, month, ra, dec)

        Returns:
        list, all links as str for the given OBSID dataset
        """
        base_url = "https://nasa-heasarc.s3.amazonaws.com/nicer/data/obs/"
        base_url = f"{base_url}{info['year']}_{info['month']}/{info['OBSID']}"
        file_urls = {
            "small": [f"/log/ni{info['OBSID']}_errlog.html",
                      f"/log/ni{info['OBSID']}_joblog.html",
                      f"/auxil/ni{info['OBSID']}.orb.gz",
                      f"/auxil/ni{info['OBSID']}.cat",
                      f"/xti/hk/ni{info['OBSID']}_0mpu0.hk.gz",
                      f"/xti/hk/ni{info['OBSID']}_0mpu1.hk.gz",
                      f"/xti/hk/ni{info['OBSID']}_0mpu2.hk.gz",
                      f"/xti/hk/ni{info['OBSID']}_0mpu3.hk.gz",
                      f"/xti/hk/ni{info['OBSID']}_0mpu4.hk.gz",
                      f"/xti/hk/ni{info['OBSID']}_0mpu5.hk.gz",
                      f"/xti/hk/ni{info['OBSID']}_0mpu6.hk.gz",
                      f"/xti/products/ni{info['OBSID']}_lc.png",
                      f"/xti/products/ni{info['OBSID']}_pi.png",
                      f"/xti/products/ni{info['OBSID']}mpu7_load.xcm.gz",
                      f"/xti/products/ni{info['OBSID']}mpu7_sr.lc.gz",
                      f"/xti/products/ni{info['OBSID']}mpu7_sr.pha.gz",
                      f"/xti/products/ni{info['OBSID']}mpu7_bg.pha.gz"],
            "big": [f"/auxil/ni{info['OBSID']}.mkf.gz",
                    f"/auxil/ni{info['OBSID']}.att.gz",
                    f"/xti/event_cl/ni{info['OBSID']}_0mpu7_cl.evt.gz",
                    f"/xti/event_cl/ni{info['OBSID']}_0mpu7_ufa.evt.gz",
                    f"/xti/event_uf/ni{info['OBSID']}_0mpu0_uf.evt.gz",
                    f"/xti/event_uf/ni{info['OBSID']}_0mpu1_uf.evt.gz",
                    f"/xti/event_uf/ni{info['OBSID']}_0mpu2_uf.evt.gz",
                    f"/xti/event_uf/ni{info['OBSID']}_0mpu3_uf.evt.gz",
                    f"/xti/event_uf/ni{info['OBSID']}_0mpu4_uf.evt.gz",
                    f"/xti/event_uf/ni{info['OBSID']}_0mpu5_uf.evt.gz",
                    f"/xti/event_uf/ni{info['OBSID']}_0mpu6_uf.evt.gz",
                    f"/xti/products/ni{info['OBSID']}mpu7.arf.gz",
                    f"/xti/products/ni{info['OBSID']}mpu7.rmf.gz",
                    f"/xti/products/ni{info['OBSID']}mpu7_bg.pha.gz",
                    f"/xti/products/ni{info['OBSID']}mpu7_sk.arf.gz"]
        }
        return {"small": [f"{base_url}{url}" for url in file_urls["small"]],
                "big": [f"{base_url}{url}" for url in file_urls["big"]]}

    def reduce(self, data):
        """
        Performs standardized data reduction scheme calling
        nicerl2 and barycorr if set
        """
        logger.info("\nStarting Data Reduction... \n")
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

        for data in self.queue:
            logger.info("")
            logger.info("-" * 60)
            logger.info((" " * 14) + "Prosessing OBSID: " +
                        colored(str(data["OBSID"]), "cyan"))
            logger.info("-" * 60)
            # Download dataset
            urls = self._make_download_links(data)
            # Download big
            logger.info("\nDownloading large files\n")
            for url in urls["big"]:
                asyncio.run(download_file(url))
            # Download small
            logger.info("\nDownloading small files\n")
            asyncio.run(download_obsid(urls["small"]))

            self.caldb_ver = get_caldb_ver()
            self.reduce(data)

            base_dir = os.getcwd()
            os.chdir(f"{data['OBSID']}/xti/event_cl/")
            if self.tar_sel.lower() == "y":
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
        "--inlist",
        dest="inlist",
        help=(".csv or Unix style pathname pattern whhich lists paths "
              "to OBSID dirs or mpu7_cl.evt "
              "files for use with --reprocess and/or --checkcal"),
        default=None,
        nargs="+",
    )

    p.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}"
    )

    argp = p.parse_args(args)

    level = logging.INFO
    logging.basicConfig(stream=sys.stdout,
                        level=level,
                        format="")

    if argp.checkcal is True or argp.reprocess is True:
        if argp.inlist is None:
            reprocess_check(argp)
        else:
            inlist(argp)
    else:
        logger.info(colored("##########  Auto NICER  ##########\n",
                    "cyan"))
        an = AutoNICER(argp.src, argp.bc, argp.compress)
        an.call_nicer()
        an.command_center()
