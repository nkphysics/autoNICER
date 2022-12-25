import autonicer
import subprocess as sp
import os
import shutil
import gzip
import tarfile
import pandas as pd
from astropy.io import fits
from termcolor import colored
import sys
import glob


class Reprocess:
    def __init__(self, cals=None):
        if cals is None:
            self.curr_caldb = autonicer.get_caldb_ver()
        else:
            self.curr_caldb = cals
        self.base_dir = os.getcwd()
        self.last_caldb = None
        self.calstate = None
        self.src = None
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
        os.chdir(f"xti/event_cl/")
        files = glob.glob("*cl.evt")
        for i in files:
            if self.src == None:
                self.get_meta(i)
            if i == f"bc{self.obsid}_0mpu7_cl.evt":
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
            self.ra = hdul[0].header["RA_OBJ"]
            self.dec = hdul[0].header["DEC_OBJ"]
        except KeyError:
            print(colored("Unable to identify required metadata.", "red"))
            print("Consider Re-downloading and reducing this dataset")
            print("OR")
            print("Try nicerl2 manually")
            self.reprocess_err = True
        try:
            self.src = hdul[0].header["OBJECT"]
        except KeyError:
            print("Unable to identify Object -> IS OK")
            print("Proceeding with Reduction...")
            self.src = False
        return self.src, self.reprocess_err

    def checkcal(self):
        """
        Checks the status of an existing obsid's calibrations
        """
        print(f"Latest NICER CALDB: {self.curr_caldb}")
        print("")
        for i in self.clevts:
            os.chdir(f"{self.base_dir}/xti/event_cl/")
            hdul = fits.open(i)
            try:
                self.last_caldb = hdul[0].header["CALDBVER"]
                print(f"CALDB for {i}: {self.last_caldb}")
            except KeyError:
                print(colored("!!!!! CANNOT IDENTIFY CALDB !!!!!", "red"))
                break

            premessage = ""
            color = "red"
            if self.last_caldb == self.curr_caldb:
                self.calstate = True
                color = "green"
            else:
                self.calstate = False
                premessage = "NOT"
            print(colored(f"{premessage} Up to date with latest NICER CALDB", color))
            print("")
            hdul.close()
        os.chdir(self.base_dir)
        return self.calstate

    def decompress(self):
        """
        Extracts/decompresses all files in xti/event_cl in .gz or .tar.gz formats
        """
        print(colored(f"######## Decompressing {self.obsid} ########", "green"))
        os.chdir(f"{self.base_dir}/xti/event_cl/")
        gzs = glob.glob("*.evt.gz")
        for i in gzs:
            with gzip.open(i, "rb") as gz_in:
                fname = str(i).split(".gz")
                with open(fname[0], "wb") as orig_out:
                    print(f"{i} -> {fname[0]}")
                    shutil.copyfileobj(gz_in, orig_out)
            os.remove(i)
        tars = glob.glob("*.tar.gz")
        for i in tars:
            tfile = tarfile.open(i, "r:gz")
            print(f"Extracting {i}")
            tfile.extractall()
            tfile.close()
            os.remove(i)
        if len(gzs) > 0 or len(tars) > 0:
            self.comp_det = True
        os.chdir(self.base_dir)
        return self.comp_det

    def reprocess(self, bc=None, compress=None):
        """
        Reprocesses an existing dataset with latest calibrations
        """
        if self.calstate is True:
            print(f"----------  Passing Reprocess of {self.obsid}  ----------")
        elif self.reprocess_err is True:
            print(colored("!!!!! CANNOT REPROCESS !!!!!"), "red")
        else:
            self.decompress()
            if bc is True:
                self.bc_det = bc
            an = autonicer.AutoNICER(src=self.src, bc=self.bc_det, comp=False)
            an.observations.append(self.obsid)
            an.ras.append(self.ra)
            an.decs.append(self.dec)
            proc_dir = self.base_dir.split(f"{self.obsid}")
            os.chdir(proc_dir[0])
            an.reduce(self.obsid)
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
    Runs --reprocess and/or checkcal for an input file with paths to NICER OBSID dirs
    or .evt files
    """
    cwd = os.getcwd()
    curr_cals = autonicer.get_caldb_ver()
    try:
        if len(argp.inlist) == 1:
            df = pd.read_csv(f"{argp.inlist[0]}")
            for i in df["Input"]:
                path_sep = i.split("/xti/event_cl/")
                os.chdir(path_sep[0])
                if argp.checkcal is True or argp.reprocess is True:
                    reprocess_check(argp, curr_cals)
                os.chdir(cwd)
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
                    print(f"Migrating to {i}")
                    if argp.checkcal is True or argp.reprocess is True:
                        reprocess_check(argp, curr_cals)
                    os.chdir(cwd)
                except NotADirectoryError:
                    print(f"{i} is not a directory! Passing...")
        else:
            print(colored(f"DATASETS NOT FOUND", "red"))
    except pd.errors.ParserError:
        print(colored(f"Unable to resolve --inlist {argp.inlist[0]}", "red"))
    except KeyError:
        print(colored(f"{argp.inlist[0]} format not readable", "red"))
        print("Format must be csv with Input column for inlist files...")
