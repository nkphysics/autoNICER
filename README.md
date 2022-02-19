# autoNICER
A piece of software that allows for the automated retrieval, and default data reduction of NICER data. This software was developed to automate the retrieval of NICER data and perform standardized data reduction on the retrieved NICER data. 
This project unaffiliated with the NICER team, NASA, the Goddard Space Flight Center (GSFC), and HEASARC. Thus, under no circumstances should anyone consider this project endorsed or recommended by the afformentioned agencies and organizations.

## Contributing
Anyone considering contribiting to this project is encouraged to do so.
Constributing can be something as small as submitting issues you have found or requesting enhancements. Your feedback is valuable.
All that is asked is that if you wish to contribute code please reach out in one way or another to nkphysics(Nick Space Cowboy), and submit a pull request.

Thank you. 

## Disclaimer
This software is licensed under the Apache 2.0 license, so it is free and open source for you to use.
This project unaffiliated with the NICER team, NASA, the Goddard Space Flight Center (GSFC), and HEASARC. Under no circumstances should anyone consider this project endorsed or recommended by the afformentioned agencies and organizations.

## Pre-Requisite Software
- HEASoft v6.29c <https://heasarc.gsfc.nasa.gov/docs/software/lheasoft/>
- Remote CALDB <https://heasarc.gsfc.nasa.gov/docs/heasarc/caldb/caldb_remote_access.html>
- wget

## Installation

For standard non-dev use cases (download the .whl) (normal pip installation coming soon):

::

	$ pip3 install autonicer-1.0.0-py3-none-any.whl

For development cases:
- Clone the repo
- cd into the project directory
- make sure you are using poetry to help manage dependencies
- Start working!

## Basic Usage

1. Make sure you have heasoft ready to be called.

2. Go to the HEASARC archive in your web browser and query the NICERMASTER catalog for the source of your choice.

2. Navigate to the desired directory where you want the NICER data that will be retrieved to be stored.

3. Run autonicer
	
4. Upon starting autoNICER you will be asked to input the  target source that you would like to query. Input the same source that you queryed in the web browser.

5. Next you will be prompted to select if you want the results of this automated pipeline to be written out in a csv que. If you want to an output que written then enter "y" otherwise just hit enter/return to pass through this line.

	- If you selected that you want want an output que written then create a .csv file with the header `Input,Name` and input the path to that file when prompted.

6. Next you will see the following prompt `autoNICER > `. Enter in the desired OBSID for the observation that you want retrieved and reduced. Better yet, copy the desired observation ID from the HEASARC archive and paste into the program. This will query that observation to be retrieved and processed. Type `done` when you have entered in all the observation IDs you want retrieved and reduced.
	
7. You will see autoNICER start retrieving the data with wget, then that will be fed directly into `nicerl2`, then it will be barycenter corrected and lastly compressed in a .tar.gz format.
