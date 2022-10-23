from .autonicer import get_caldb_ver
import subprocess as sp
import os
from astropy.io import fits
from termcolor import colored


class Reprocess:
    def __init__(self):
        self.curr_caldb = get_caldb_ver()
        self.last_caldb = None
        self.calstate = None

    def checkcal(self):
        """
        Checks the status of an existing obsid's calibrations
        """
        print(f"Latest NICER CALDB: {self.curr_caldb}")
        base_dir = os.getcwd()
        os.chdir(f"xti/event_cl/")
        files = sp.run("ls *cl.evt", shell=True, capture_output=True, encoding="utf-8")
        for i in str(files.stdout).split("\n"):
            if i == "":
                break
            print(f"Detected mpu7_cl.evt files: {i}")
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
            hdul.close()
        return self.calstate       
        
