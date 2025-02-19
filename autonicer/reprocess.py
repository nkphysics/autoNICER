# AutoNICER
# Copyright 2022-2023 Nicholas Kuechel
# License Apache 2.0

import autonicer
import os
import logging
import shutil
import gzip
import tarfile
import pandas as pd
from astropy.io import fits
from termcolor import colored
import sys
import glob
import concurrent.futures

AUTONICER = os.path.basename(sys.argv[0])
logger = logging.getLogger(AUTONICER)


def extract_gz(file) -> str:
    with gzip.open(file, "rb") as gz_in:
        fname = str(file).split(".gz")
        with open(fname[0], "wb") as orig_out:
            shutil.copyfileobj(gz_in, orig_out)
    os.remove(file)
    return f"{file} -> {fname[0]}"


def extract_tar(file) -> str:
    with tarfile.open(file, "r:gz") as tfile:
        tfile.extractall()
    os.remove(file)
    return f"{file} extracted"


class Reprocess:
    def __init__(self, cals=None):
        if cals is None:
            self.curr_caldb = autonicer.get_caldb_ver()
        else:
            self.curr_caldb = cals
        self.base_dir = os.getcwd()
        self.last_caldb = None
        self.calstate = None
        self.src = False
        self.obsid = None
        self.ra = None
        self.dec = None
        self.bc_det = False
        self.comp_det = False
        self.reprocess_err = None
        self.clevts = self.get_clevts()

    def get_clevts(self):
        """
        Gets all cl.evt files associated with an existing NICER dataset
        """
        os.chdir("xti/event_cl/")
        files = glob.glob("*cl.evt")
        for i in files:
            self.get_meta(i)
        if f"bc{self.obsid}_0mpu7_cl.evt" in files:
            self.bc_det = True
        os.chdir(self.base_dir)
        return files

    def get_meta(self, infile):
        """
        Gets relevant metadata for reprocessing from NICER dataset
        """
        hdul = fits.open(infile)
        try:
            self.obsid = hdul[0].header["OBS_ID"]
        except KeyError:
            try:
                self.obsid = hdul[1].header["OBS_ID"]
            except KeyError:
                logger.info(colored("Unable to idenify OBSID", "red"))
                self.reprocess_err = True
        try:
            self.ra = hdul[0].header["RA_OBJ"]
            self.dec = hdul[0].header["DEC_OBJ"]

        except KeyError:
            logger.info(colored("Unable to identify required metadata.",
                                "red"))
            logger.info("Consider Re-downloading and reducing this dataset")
            logger.info("OR")
            logger.info("Try nicerl2 manually")
            self.reprocess_err = True
        return self.reprocess_err

    def checkcal(self):
        """
        Checks the status of an existing obsid's calibrations
        """
        logger.info(f"Latest NICER CALDB: {self.curr_caldb}")
        logger.info("")
        for i in self.clevts:
            os.chdir(f"{self.base_dir}/xti/event_cl/")
            hdul = fits.open(i)
            try:
                self.last_caldb = hdul[1].header["CALDBVER"]
                logger.info(f"CALDB for {i}: {self.last_caldb}")
            except KeyError:
                logger.info(colored("!!!!! CANNOT IDENTIFY CALDB !!!!!",
                                    "red"))
                break

            premessage = ""
            color = "red"
            if self.last_caldb == self.curr_caldb:
                self.calstate = True
                color = "green"
            else:
                self.calstate = False
                premessage = "NOT"
            logger.info(colored((f"{premessage} Up to date "
                                 "with latest NICER CALDB\n"),
                        color))
            hdul.close()
        os.chdir(self.base_dir)
        return self.calstate

    def decompress(self):
        """
        Extracts/decompresses all files in xti/event_cl
        in .gz or .tar.gz formats
        """
        logger.info(colored(f"######## Decompressing {self.obsid} ########",
                            "green"))
        os.chdir(f"{self.base_dir}/xti/event_cl/")
        gzs = glob.glob("*.evt.gz")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            exts_gz = [executor.submit(extract_gz, i) for i in gzs]
            for j in concurrent.futures.as_completed(exts_gz):
                logger.info(j.result())

        tars = glob.glob("*.tar.gz")
        with concurrent.futures.ThreadPoolExecutor() as executor:
            ext_tar = [executor.submit(extract_tar, i) for i in tars]
            for j in concurrent.futures.as_completed(ext_tar):
                logger.info(j.result())
        if len(gzs) > 0 or len(tars) > 0:
            self.comp_det = True
        os.chdir(self.base_dir)
        return self.comp_det

    def reprocess(self, bc=None, compress=None):
        """
        Reprocesses an existing dataset with latest calibrations
        """
        if self.calstate is True:
            logger.info(f"Passing Reprocess of {self.obsid}\n")
        elif self.reprocess_err is True:
            logger.info(colored("!!!!! CANNOT REPROCESS !!!!!"), "red")
        else:
            self.decompress()
            if bc is True:
                self.bc_det = bc
            an = autonicer.AutoNICER(src=self.src, bc=self.bc_det, comp=False)
            reprocess_dict = {"OBSID": self.obsid,
                              "ra": self.ra,
                              "dec": self.dec}
            an.queue.append(reprocess_dict)
            proc_dir = self.base_dir.split(f"{self.obsid}")
            os.chdir(proc_dir[0])
            an.reduce(reprocess_dict)
            os.chdir(f"{self.base_dir}/xti/event_cl/")
            if compress is True or self.comp_det is True:
                an.nicer_compress()


def reprocess_check(argp, cals=None):
    """
    Parses and Runs --reprocess and --checkcal
    """
    check = Reprocess(cals)
    if argp.checkcal is True:
        check.checkcal()
    if argp.reprocess is True:
        check.reprocess(argp.bc, argp.compress)


def inlist(argp):
    """
    Runs --reprocess and/or checkcal for an input file
    with paths to NICER OBSID dirs or .evt files
    """
    cwd = os.getcwd()
    curr_cals = autonicer.get_caldb_ver()
    try:
        if len(argp.inlist) == 1:
            try:
                df = pd.read_csv(f"{argp.inlist[0]}")
                for i in df["Input"]:
                    path_sep = i.split("/xti/event_cl/")
                    os.chdir(path_sep[0])
                    if argp.checkcal is True or argp.reprocess is True:
                        reprocess_check(argp, curr_cals)
                    os.chdir(cwd)
            except IsADirectoryError:
                raise FileNotFoundError
        else:
            raise FileNotFoundError

    except FileNotFoundError:
        dirs = argp.inlist
        if len(argp.inlist) == 1:
            dirs = glob.glob(f"{argp.inlist[0]}")
        if len(dirs) != 0:
            for i in dirs:
                try:
                    os.chdir(i)
                    logger.info(f"Migrating to {colored(i, 'cyan')}")
                    if argp.checkcal is True or argp.reprocess is True:
                        reprocess_check(argp, curr_cals)
                    os.chdir(cwd)
                except NotADirectoryError:
                    logger.info(f"{i} is not a directory! Passing...")
        else:
            logger.info(colored("DATASETS NOT FOUND", "red"))
    except pd.errors.ParserError:
        logger.info(colored(f"Unable to resolve --inlist {argp.inlist[0]}",
                            "red"))
    except KeyError:
        logger.info(colored(f"{argp.inlist[0]} format not readable", "red"))
        logger.info("Format must be csv with Input column for inlist files.")
