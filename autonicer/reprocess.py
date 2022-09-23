from .autonicer import get_caldb_ver
import subprocess as sp
import os
from astropy.io import fits

def checkcal():
    """
    Routine to check the status of an existing obsid's calibrations
    """
    calstate = False
    curr_caldb = get_caldb_ver()
    print(f"Latest NICER CALDB: {curr_caldb}")
    base_dir = os.getcwd()
    os.chdir(f"xti/event_cl/")
    files = sp.run("ls *cl.evt", shell=True, capture_output=True, encoding="utf-8")
    last_caldb = 0
    for i in str(files.stdout).split("\n"):
        if i == "":
            break
        print(f"Detected: {i}")
        hdul = fits.open(i)
        last_caldb = hdul[0].header["CALDBVER"]
        print(f"CALDB for {i}: {last_caldb}")
        if last_caldb == curr_caldb:
            calstate = True
    return calstate
