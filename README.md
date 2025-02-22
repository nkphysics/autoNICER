[![PyPI](https://img.shields.io/pypi/v/autonicer.svg)](https://pypi.org/project/autonicer/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/autonicer.svg?label=PyPI%20downloads)](https://pypi.org/project/autonicer/)

# autoNICER
A CLI that allows for the automated retrieval, and default data reduction of NICER data. This software was developed to automate the retrieval of NICER data and perform standardized data reduction on the retrieved NICER data.

## Contributing
Anyone considering contribiting to this project is encouraged to do so.
Constributing can be something as small as submitting issues you have found or requesting enhancements. Your feedback is incredibly valuable for improving the project.
All that is asked is that if you wish to contribute code please reach out in one way or another to nkphysics, and submit a pull request.

If you are reading this and considering contributing, know that you even taking the time to consider contributing is greatly appreciated. 

Thank you. 

## Disclaimer
This software is licensed under the Apache 2.0 license, so it is free for you to use.
This project is unaffiliated with the NICER mission, NASA, the Goddard Space Flight Center (GSFC), and HEASARC. Under no circumstances should anyone consider this project endorsed by or recommended by the afformentioned agencies and organizations.

## Watch a video Tutorial on how to use autoNICER
After v1.0.2 I a made a video going over autoNICER and demoing some of its functionality.
See it here:
<https://youtu.be/q23dvn3Da7Q>

For more in depth instructions and documentation check out the wiki:
<https://github.com/nkphysics/autoNICER/wiki>

## Pre-Requisite Software
- HEASoft v6.29-v6.34, MOST RECENT VERSION RECOMMENDED (v6.34 as of 2025-02-22) <https://heasarc.gsfc.nasa.gov/docs/software/lheasoft/>

A video tutorial on how to generally install heasoft can be found here: <https://youtu.be/3-gobnSEuDo>
- Remote CALDB <https://heasarc.gsfc.nasa.gov/docs/heasarc/caldb/caldb_remote_access.html>

A video tutorial on how to setup Remote CALDB can be found here: <https://youtu.be/s01DF0cwOvM>
- wget (Only for versions < v1.3.0)

## Installation

For standard non-dev use cases download via pip.

	$ pip3 install autonicer

OR

	$ pip install autonicer

For development cases:
- Clone the repo
- cd into the project directory
- Install with dev deps `python -m pip install .[dev]`
- Start working!
- Run tests locally before submitting a PR

## Basic Usage

1. Initialize HEASoft.

2. Go to the HEASARC archive in your web browser and query the NICERMASTER catalog for the source of your choice.

2. Navigate to the desired directory where you want the NICER data that will be retrieved to be stored.

3. Run autonicer by calling the local installation (i.e. `$ autonicer`)
	
4. Upon starting autoNICER you will be asked to input the target source that you would like to query. Input the same source that you queryed in the web browser (ex: PSR_B0531+21).

5. Next you will be prompted to select the settings. You can select the following
	- If you want a barycenter correction performed
	- If a .csv log of the autoNICER run is written out
	- If the *ufa.evt files are compressed after reduction

6. Next you will see the following prompt `autoNICER > `. Enter in the desired OBSID for the observation that you want retrieved and reduced. Better yet, copy the desired observation ID from the HEASARC archive and paste into the program. This will query that observation to be retrieved and processed. Type `sel` to see all the OBSID's you've selected. Type `cycle [cycle number]`(not with the brackets) to select all OBSID's from a specific cycle. You can use the `rm [all or OBSID]` or `back` commands to remove unwanted OBSID's that you may have selected by mistake. Type `done` when you have entered in all the observation IDs you want retrieved and reduced.
	
7. You will see autoNICER start retrieving the data with wget, then that will be fed directly into `nicerl2`, then it will be barycenter corrected and lastly compressed in a .gz format if you selected for it to happen. Selected OBSID's are retrieved and processed in series so autoNICER will move on the the next OBSID you've queryed up and give you back command of your terminal after it has retrieved and reduced all selected OBSIDs.

- Run `autonicer --help` for a list of CLI options
