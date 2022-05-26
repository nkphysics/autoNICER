# autoNICER

Author: Nicholas Kuechel a.k.a. Nick The Space Cowboy a.k.a. Tsar Bomba Nick

## Description: 

autoNICER is a program that allows individuals wanting to work with data from the NICER mission to automatically retrieve observational data, reduce observational the retrieved observational data through a standardized data reduction scheme, and then compress less commonly used files from the observational data set to conserve space. 

## Changes Pre-v1.0.0 release
- Original version of this code specifically written for work on a small VM
- Elimination of the count rate functionality tool
- Streamiling so it runs from the directory its called in
- Changed the barycenter correction to include the modern ephemeris set to JPLEPH.430 and to custom set RA and DEC without changing the code
- Added further automation to pull directly from heasarc
	- Auto pulls year, month, ra, and dec
- Added auto queing generation option 
- Added automatic tar.gz compression to all .evt files with the exception of the bary-center corrected mpu7_cl.evt file
- Fixed issue of outpath not being fully written out in the output que

### v1.0.0
- Added cycle selection functionality with the command "cycle [cycle #]"
- Added rm command to remove either all selected obsid's with `rm all`, or a specific obsid with `rm obsid` where "obsid" is the observation ID we want removed from the processing queue

### v1.0.1
- PRIMARY: Changed the way output ques/logs are written out. Users may now select if they want to add to an exisiting log file or create a new log file.
- SECONDARY: Added testing of functions that can be tested without requiring the retrieval of NICER observational data for CI testing on the github end. 
- Added coloration of text in the terminal when running autoNICER so a user can be more aware of the where in the procedure autoNICER is.

### v1.0.2
- Limited the astropy dependency to versions less than v5.1 since the changes in astropy v5.1 mess with the time conversions. (Future versions will make autonicer compatable with astropy v5.1)
