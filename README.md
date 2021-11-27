# autoNICER
A piece of software that allows for the automated retrieval, and default data reduction of NICER data. Started by Nick Kuechel, an independent researcher, this software was developed to automate the retrieval and standardardized reduction of NICER data. This project unaffiliated with the NICER team, NASA, the Goddard Space Flight Center (GSFC), and HEASARC. Thus, under no circumstances should anyone consider this project endorsed or recommended by the afformentioned agencies and organizations.

Anyone considering contribiting to this project is encouraged to do so.

## Disclaimer

This software is licensed under the Apache 2.0 license, so it is free and open source for you to use.

## Pre-Requisites Libraries and Software

### Python Libraries
1. subprocess
2. os
3. pandas
4. time
5. numpy
6. astropy
7. astroquery
8. datetime

### Other software

- HEASoft v6.29c <https://heasarc.gsfc.nasa.gov/docs/software/lheasoft/>
- Remote CALDB <https://heasarc.gsfc.nasa.gov/docs/heasarc/caldb/caldb_remote_access.html>
- wget

## Usage

1. Go to the HEASARC archive in your web browser and query the NICERMASTER catalog for the source of your choice.

2. Navigate to the desired directory where you want the NICER data that will be retrieved to be stored.

3. Run autoNICER with the following command, or better yet set up an alias in your .bashrc and call that alias (autoNICER would be a good alias).

	`python3 PATH/TO/autoNICER.py` or `python PATH/TO/autoNICER.py`
	
4. Upon starting autoNICER you will be asked to input the  target source that you would like to query. Input the same source that you queryed in the web browser.

5. Next you will be prompted to select if you want the results of this automated pipeline to be written out in a csv que. If you want to an output que written then enter "y" otherwise just hit enter/return to pass through this line.

	- If you selected that you want want an output que written then create a .csv file with the header `Input,Name` and input the path to that file when prompted.

6. Next you will see the following prompt `Enter Observation ID or Command: `. Enter in the desired OBSID for the observation that you want retrieved and reduced. Better yet, copy the desired observation ID from the HEASARC archive and paste into the program.

	- Hit enter/return after entering in the desired NICER observation ID
	- Enter `done` in the prompt after you have entered in all your desired observation IDs
	- Enter `sel` if you want to see the OBSIDs you have entered. Do this before you use `done`
	- Enter `back` to delete the most recently enterd observation id
	- Enter `cycle #` (# being the desired cycle number (1,2,3,...)) to select all observation IDs from an obsrving cycle 
	
7. You will see autoNICER start retrieving the data with wget, then that will be fed directly into `nicerl2`, then it will be barycenter corrected and lastly compressed in a .tar.gz format.
