#! /usr/bin/env python3

# Auto NICER V2.0
# By: Nicholas Kuechel
# Lisense

import subprocess as sp
import os
import pandas as pd
import time
from astroquery.heasarc import Heasarc
from astropy.table import Table
from astropy.visualization import time_support
from astropy.visualization import quantity_support
from astropy.time import Time
import datetime

# Arrays for storing the observation values
st = True
observations = []
years = []
months = []
ras = []
decs = []

print("########################################################################")
print("############               Auto NICER V2.0                  ############")
print("########################################################################")
print()

obj = str(input("Target: "))

q_set = str(input("Write Output Que: [n] "))
tar_sel = str(input("Compress XTI files (.tar.gz): [y] "))
q_path = 0
q_name = 0
if q_set == "y":
    q_path = str(input("Input Que: "))
    if q_path[0] == r"'" or que_path[0] == r'"':
        q_path = q_path.replace("'", "")
        q_path = q_path.replace(" ", "")
        q_path = q_path.replace('"', "")
    else:
        pass
else:
    pass

heasarc = Heasarc()
quantity_support()
time_support()
xti = heasarc.query_object(
    obj, mission="nicermastr"
)  # calls NICER master catalogue for crab
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

downCommand = (
    "wget -q -nH --no-check-certificate --cut-dirs=5 -r -l0 -c -N -np -R "
    + "'index*'"
    + " -erobots=off --retr-symlinks https://heasarc.gsfc.nasa.gov/FTP/nicer/data/obs/"
)
# beginning of obsid inputs
while st == True:
    enter = str(input("Enter Observation ID or Command: "))
    if enter == "done" or enter == "Done":
        st = False
    elif enter == "sel" or enter == "Sel" or enter == "SEL":
        print("Observations Selected:")
        for i in observations:
            print(i)
    elif enter == None or enter == "":
        print("Nothing entered...")
        print("!!!ENTER SOMETHING!!!")
    elif enter == "back" or enter == "Back" or enter == "BACK":
        print("Old Que: " + str(observations))
        del observations[-1]
        print("New Que: " + str(observations))
    else:
        observations.append(enter)
        row = xti.loc[xti["OBSID"] == enter]
        dt = row["TIME"]
        row.reset_index(drop=True, inplace=True)
        dt.reset_index(drop=True, inplace=True)
        year = str(dt[0].year)
        years.append(year)
        month = dt[0].month
        # basic if else statement to fix single digit months not having a zero out front
        if month < 10:
            month = "0" + str(month)
        else:
            month = str(month)
        months.append(month)
        ras.append(row["RA"][0])
        decs.append(row["DEC"][0])


def nicer_compress():
    print("##########################################################")
    print("               Auto .tar.gz compression tool")
    print("##########################################################")
    print("Compressing ufa.evt files")
    print("----------------------------------------------------------")
    files = sp.run("ls *ufa.evt", shell=True, capture_output=True, encoding="utf-8")
    for i in str(files.stdout).split("\n"):
        if i == "":
            pass
        else:
            sp.call("tar czvf " + str(i) + ".tar.gz " + str(i), shell=True)
            sp.call("rm -r " + str(i), shell=True)
    print("")
    print("Compressing cl.evt files")
    print("----------------------------------------------------------")
    cl_file = sp.run("ls ni*cl.evt", shell=True, capture_output=True, encoding="utf-8")
    for i in str(cl_file.stdout).split("\n"):
        if i == "":
            pass
        else:
            sp.call("tar czvf " + str(i) + ".tar.gz " + str(i), shell=True)
            sp.call("rm -r " + str(i), shell=True)


count = 0
for obsid in observations:
    print("")
    print("--------------------------------------------------------------")
    print("             Prosessing OBSID: " + str(obsid))
    print("--------------------------------------------------------------")
    print("Downloading xti data...")
    sp.call(
        str(downCommand)
        + str(years[count])
        + "_"
        + str(months[count])
        + "//"
        + str(obsid)
        + "/xti/ --show-progress --progress=bar:force",
        shell=True,
    )
    print("Downloadng log data...")
    sp.call(
        str(downCommand)
        + str(years[count])
        + "_"
        + str(months[count])
        + "//"
        + str(obsid)
        + "/log/ --show-progress --progress=bar:force",
        shell=True,
    )
    print("Downloading auxil data...")
    sp.call(
        str(downCommand)
        + str(years[count])
        + "_"
        + str(months[count])
        + "//"
        + str(obsid)
        + "/auxil/ --show-progress --progress=bar:force",
        shell=True,
    )
    sp.call("nicerl2 indir=" + str(obsid) + "/" + " clobber=yes", shell=True)
    sp.call(
        "barycorr infile="
        + str(obsid)
        + "/xti/event_cl/ni"
        + str(obsid)
        + "_0mpu7_cl.evt outfile="
        + str(obsid)
        + "/xti/event_cl/bc"
        + str(obsid)
        + "_0mpu7_cl.evt orbitfiles="
        + str(obsid)
        + "/auxil/ni"
        + str(obsid)
        + ".orb refframe=ICRS ra="
        + str(ras[count])
        + " dec="
        + str(decs[count])
        + " ephem=JPLEPH.430",
        shell=True,
    )

    # Here is the stuff for automatic tar.gz compression
    base_dir = os.getcwd()
    os.chdir(str(obsid) + "/xti/event_cl/")
    if tar_sel == "n" or tar_sel == "N":
        pass
    else:
        nicer_compress()
    os.chdir(base_dir)
    if q_set == "y":
        read_q = pd.read_csv(q_path)
        newline = pd.Series(
            data=[
                str(base_dir)
                + "/"
                + str(obsid)
                + "/xti/event_cl/bc"
                + str(obsid)
                + "_0mpu7_cl.evt",
                "NI" + str(obsid),
            ],
            index=["Input", "Name"],
        )
        read_q = read_q.append(newline, ignore_index=True)
        read_q.to_csv(q_path, index=False)
    else:
        pass

    count = count + 1
