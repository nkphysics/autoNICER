from .autonicer import get_caldb_ver
import subprocess as sp
import os
import gzip
import tarfile as tar
from astropy.io import fits
from termcolor import colored
from .autonicer import AutoNICER


class Reprocess:
    def __init__(self):
        self.curr_caldb = get_caldb_ver()
        self.base_dir = os.getcwd()
        self.last_caldb = None
        self.calstate = None
        self.src = None
        self.obsid = None
        self.ra = None
        self.dec = None
        self.clevts = self.get_clevts()

    def get_clevts(self):
        """
        Gets all cl.evt files associated with an existing NICER dataset
        """
        os.chdir(f"xti/event_cl/")
        files = sp.run("ls *cl.evt", shell=True, capture_output=True, encoding="utf-8")
        filelist = []
        for i in str(files.stdout).split("\n"):
            if i != "":
                filelist.append(i)
                if self.src == None:
                    self.get_meta(i)
        os.chdir(self.base_dir)
        return filelist

    def get_meta(self, infile):
        """
        Gets relevant metadata for reprocessing from NICER dataset
        """
        hdul = fits.open(infile)
        self.src = hdul[0].header["OBJECT"]
        self.obsid = hdul[0].header["OBS_ID"]
        self.ra = hdul[0].header["RA_OBJ"]
        self.dec = hdul[0].header["DEC_OBJ"]
        hdul.close()
        return True

    def checkcal(self):
        """
        Checks the status of an existing obsid's calibrations
        """
        print(f"Latest NICER CALDB: {self.curr_caldb}")
        print("")
        for i in self.clevts:
            os.chdir(f"{base_dir}/xti/event_cl/")
            hdul = fits.open(i)
            self.last_caldb = hdul[0].header["CALDBVER"]
            print(f"CALDB for {i}: {self.last_caldb}")

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
        
    def uncompress(self):
        """
        Extracts/uncompresses all files in xti/event_cl in .gz or .tar.gz formats
        """

    def reprocess(self):
        """
        Reprocesses an existing dataset with latest calibrations
        """
        an = autonicer.AutoNICER(src=self.src)
        # Extract/Decompress everything
        # Run nicerl2
        # Run barycorr if option selected or existing bc*mpu7_cl.evt file
        # Compress if compressed before or option selected
