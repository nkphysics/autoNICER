# autoNICER

Author: Nicholas Kuechel a.k.a. Nick The Space Cowboy a.k.a. Tsar Bomba Nick

## Description: 

autoNICER is a program that allows individuals wanting to work with data from the NICER mission to automatically retrieve observational data, reduce observational the retrieved observational data through a standardized data reduction scheme, and then compress less commonly used files from the observational data set to conserve space. 

## Changes

### v0.1:
- Original version of this code specifically written for work on a small VM

### v1.0:
- Elimination of the count rate functionality tool
- Streamiling so it runs from the directory its called in
- Changed the barycenter correction to include the modern ephemeris set to JPLEPH.430 and to custom set RA and DEC without changing the code

### v2.0:
- Added further automation to pull directly from heasarc
	- Auto pulls year, month, ra, and dec
- Added auto queing generation option 
- Added automatic tar.gz compression to all .evt files with the exception of the bary-center correcter mpu7_cl.evt file
- Fixed issue of outpath not being fully written out in the output que
