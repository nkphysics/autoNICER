from .autonicer import get_caldb_ver
import subprocess as sp
import os
from astropy.io import fits
from termcolor import colored
from .autonicer import AutoNICER


class Reprocess:
    def __init__(self):
        self.curr_caldb = get_caldb_ver()
        self.last_caldb = None
        self.calstate = None
        self.src = None
        self.clevts = self.get_clevts()
        
    def get_clevts(self):
        base_dir = os.getcwd()
        os.chdir(f"xti/event_cl/")
        files = sp.run("ls *cl.evt", shell=True, capture_output=True, encoding="utf-8")
        filelist = []
        for i in str(files.stdout).split("\n"):
            if i != "":
                filelist.append(i)
        os.chdir(base_dir)
        return filelist

    def checkcal(self):
        """
        Checks the status of an existing obsid's calibrations
        """
        print(f"Latest NICER CALDB: {self.curr_caldb}")
        print("")
        base_dir = os.getcwd()
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
        os.chdir(base_dir)
        return self.calstate
       
    def reprocess(self):
        """
        Reprocesses an existing dataset with latest calibrations
        """
        an = autonicer.AutoNICER()
        
