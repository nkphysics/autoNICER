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

### v1.1.0
- Added two new columns to the output log: CALDB_ver and DateTime. Also changed the "Name" column to "OBSID". This should lead to less confusion and give the user a better idea of which calibration version was used to process their data, and at what point in time they processed that data.

### v1.1.1
- Error handling for the done command
- Error handling for OBSIDs that do not exist in the nicermastr query
- Error handling for OBSID entries that are too short
- Fixed new issue where autonicer runs pull_reduce after each command
- Enhanced testing of commands
- Removed pull_reduce call from the init and added it under the done command

### v1.1.2
- Error handling for duplicate obsid entries from the autoNICER prompt
- Error handling for src not resolving in HEASARC nicermastr
- Added `settings` command to display current settings
- Added `--src` flag that can be called from the command line to set the src with default settings (i.e. `$ autonicer --src=DESIRED-SRC`)

### v1.1.3
- Fixed bug with single OBSID not resolving. When querying HEASARC sometimes an extra space would be in the OBSID which lead to the resolving issues.

### v1.2.0
- Added `--checkcal` CLI option to check if calibrations are up to date with an existing NICER OBSID dataset
- Added `--reprocess` CLI option to reprocess an existing NICER OBSID dataset with nicerl2
- Added `--bc` CLI option to toggle the barycenter correction setting with autonicer whether pulling and reducing or reprocessing
- Added `--compress` CLI option to toggle the compression of ufa .evt files again whether pulling and reducing or just reducing
- Added `--inlist` CLI option that accepts the path to a file in csv format with the column `Input` containing the paths to NICER OBSID datasets or mpu7_cl.evt files (This works great with the output log csv files)
- Changed compression from .tar.gz format to just .gz format (decompression of .tar.gz's supported to handle files compressed with pervious versions)
- Tested issues with Astropy v5.1, Astroquery, and HEASARC. Found no issues and supressed warnings.
- Significant additions to testing taking coverage >= 90%
- Resolved dependency vulnerability with CVE-2022-42969

### v1.2.1
- Fixed vulnerability with CVE-2022-2341
- Fixed issue where --checkcal kills --inlist cmd  

### v1.2.2
- Migrated sp.run("ls STUFF") commands to glob
- Limited get_caldb_ver() pulls to once per run of autonicer rather than once per OBSID passed in
- Added error handling for datasets lacking the required metadata
- Added unix like passthrough to `--inlist` so use cases like `--inlist *` will pass in all datasets for the current working dir

### v1.2.3
- Fixed error handling messages for missing metadata in cl.evt files
- Switched the pull of required metadata from hdu 0 (primary header) to hdu 1 (event header) for the cl.evt NICER files
- Added OBSID corolation for easier identification

### v1.2.4
- Added in multi-threaded compression/decompression of files (should speed up runtime)
- Re-added in compression of non barycenter corrected mpu7_cl.evt files if a barycenter corrrected cl.evt file is created
- Fixed bug with an unexpected `Target: ` prompt appearing if OBJECT metadata cannot be found
- Fixed bug with auto-detection of barycenter correction parsing

### v1.2.5
- Fixed vulnerabilites with cryptography dep (CVE-2023-0286 and CVE-2023-23931)

