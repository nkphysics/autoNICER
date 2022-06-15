#! /usr/bin/env python3

# AutoNICER
# Copyright 2021 Nicholas Kuechel
# License Apache 2.0

import subprocess as sp
import os
import pandas as pd
import time
import numpy as np
from astroquery.heasarc import Heasarc
from astropy.table import Table
from astropy.time import Time
from termcolor import colored
import datetime


class AutoNICER(object):
	def __init__(self, obj=None):
		self.st = True
		self.xti = 0
		self.observations = []
		self.years = []
		self.months = []
		self.ras = []
		self.decs = []
		self.caldb_ver = ""
		
		print(colored("##############  Auto NICER  ##############", "cyan"))
		print()
		self.obj = obj
		self.bc_sel = "y"
		self.q_set = "n"
		self.tar_sel = "y"
		self.q_path = 0
		self.q_name = 0
		if obj==None:
			self.startup()
			
	def startup(self):
		self.obj = str(input("Target: "))
		self.bc_sel = str(input("Apply Bary-Center Correction: [y] "))
		self.q_set = str(input("Write Output Log: [n] "))
		self.tar_sel = str(input("Compress XTI files (.tar.gz): [y] "))
		self.q_set = self.q_set.lower()
		if self.q_set == "y":
			ne = str(input("New or Add to existing Log: "))
			if ne.lower() == "add":
				self.q_path = str(input("Input Que: "))
				if self.q_path[0] == r"'" or self.que_path[0] == r'"':
					self.q_path = self.q_path.replace("'", "")
					self.q_path = self.q_path.replace(" ", "")
					self.q_path = self.q_path.replace('"', "")
			elif ne.lower() == "new":
				self.q_name = str(input("Name of output log file (no .csv): "))
					
	def call_nicer(self):
		"""
		Querys the nicermastr catalog for all observations of the specified source(self.obj)
		"""
		heasarc = Heasarc()
		xti = heasarc.query_object(
			self.obj, mission="nicermastr"
		)  # calls NICER master catalogue for an input object
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
		self.xti = xti

	def make_cycle(self):
		cycle = []
		for i in self.xti["OBSID"]:
			convo = np.floor(float(i) * 10 ** (-9))
			cycle.append(int(convo))
		self.xti["Cycle#"] = cycle
		return self.xti
		
	def get_caldb_ver(self):
		caldb = sp.run("nicaldbver", shell=True, capture_output=True, encoding="utf-8")
		convo = str(caldb.stdout).split("\n")
		return convo[0]

	def sel_obs(self, enter):
		self.observations.append(enter)
		row = self.xti.loc[self.xti["OBSID"] == enter]
		dt = row["TIME"]
		row.reset_index(drop=True, inplace=True)
		dt.reset_index(drop=True, inplace=True)
		year = str(dt[0].year)
		self.years.append(year)
		month = dt[0].month
		# basic if else statement to fix single digit months not having a zero out front
		if month < 10:
			month = "0" + str(month)
		else:
			month = str(month)
		self.months.append(month)
		self.ras.append(row["RA"][0])
		self.decs.append(row["DEC"][0])

	def rm_obs(self, cmd):
		if cmd == "all":
			self.observations.clear()
			self.years.clear()
			self.months.clear()
			self.ras.clear()
			self.decs.clear()
		else:
			n = self.observations.index(cmd)
			del self.observations[n]
			del self.years[n]
			del self.months[n]
			del self.ras[n]
			del self.decs[n]
			
	def commands(self, enter):
		if enter[0].lower() == "done":
			# Command to finish selection of obs.
			self.st = False
		elif enter[0].lower() == "sel":
			# displays all selected observations in the cmd line
			print("Observations Selected:")
			for i in self.observations:
				print(i)
		elif enter[0] == None or enter[0] == "":
			# Error message for nothing entered in the prompt
			print("Nothing entered...")
			print("!!!ENTER SOMETHING!!!")
		elif enter[0].lower() == "back":
			# Deletes the previously entered obsid
			print(f"Removing {self.observations[-1]}")
			del self.observations[-1]
			del self.ras[-1]
			del self.decs[-1]
		elif enter[0].lower() == "cycle":
			row = self.make_cycle().loc[
				self.make_cycle()["Cycle#"] == float(enter[1])
				]
			for i in row["OBSID"]:
				self.sel_obs(i)
		elif enter[0].lower() == "rm":
			try:
				self.rm_obs(enter[1])
			except:
				print(colored("Nothing found to Remove!", "red"))
		elif enter[0] == "exit":
			exit()
		else:
			try:
				if int(enter[0]) > (10 ** 8):
					print(f"Adding {enter[0]}")
					self.sel_obs(enter[0])
			except:
				print("Unknown Entry")
					
	def command_center(self, enter=None):
		# prompts the user to select obs to be pulled and reduced
		orig_in = enter
		self.st = True
		while self.st == True:
			if orig_in != None:
				self.commands(enter.split(" "))
				self.st = False
			else:
				enter = str(input(colored("autoNICER", "blue") + " > ")).split(" ")
				self.commands(enter)
			
	def nicer_compress(self):
		"""
		compresses .evt files
		"""
		print(colored("##########  .tar.gz compression  ##########", "green"))

		def tar_compr(file):
			"""
			commands for a .tar.gz compression of a single file and removal of original file after compression is complete
			"""
			if file == "":
				pass
			else:
				sp.call(f"tar czvf {file}.tar.gz {file}", shell=True)
				sp.call(f"rm -r {file}", shell=True)

		print("Compressing ufa.evt files")
		print("----------------------------------------------------------")
		# files and loop to compress the ufa files
		files = sp.run("ls *ufa.evt", shell=True, capture_output=True, encoding="utf-8")
		for i in str(files.stdout).split("\n"):
			tar_compr(i)

		# compression of the non-bc mpu7_cl.evt file if barycenter correction is selected
		if self.bc_sel.lower() == "n":
			pass
		else:
			print("")
			print("Compressing cl.evt files")
			print("----------------------------------------------------------")
			# files and liip to compress the cl files
			cl_file = sp.run(
				"ls ni*cl.evt", shell=True, capture_output=True, encoding="utf-8"
			)
			for i in str(cl_file.stdout).split("\n"):
				tar_compr(i)
				
	def add2q(self, q, base_dir, obsid):
		newline = pd.DataFrame({
				"Input":[f"{base_dir}/{obsid}/xti/event_cl/bc{obsid}_0mpu7_cl.evt"],
				"OBSID":[f"NI{obsid}"],
				"CALDB_ver": [f"{self.caldb_ver}"],
				"DateTime": [f"{datetime.datetime.now()}"]
				},
		)
		q = pd.concat([q, newline])
		q.to_csv(self.q_path, index=False)

	def pull_reduce(self):
		"""
		Downloads the NICER data
		Puts the retrieved data through a standardized data reduction scheme
		"""
		downCommand = (
			"wget -q -nH --no-check-certificate --cut-dirs=5 -r -l0 -c -N -np -R "
			+ "'index*'"
			+ " -erobots=off --retr-symlinks https://heasarc.gsfc.nasa.gov/FTP/nicer/data/obs/"
		)

		count = 0
		for obsid in self.observations:
			print("")
			print("--------------------------------------------------------------")
			print("             Prosessing OBSID: " + colored(str(obsid), "cyan"))
			print("--------------------------------------------------------------")
			pull_templ = (
				f"{downCommand}{self.years[count]}_{self.months[count]}//{obsid}"
			)
			end_args = f"--show-progress --progress=bar:force"
			print(colored("Downloading xti data...", "green"))
			sp.call(f"{pull_templ}/xti/ {end_args}", shell=True)
			print(colored("Downloadng log data...", "green"))
			sp.call(f"{pull_templ}/log/ {end_args}", shell=True)
			print(colored("Downloading auxil data...", "green"))
			sp.call(f"{pull_templ}/auxil/ {end_args}", shell=True)
			self.caldb_ver = self.get_caldb_ver()
			sp.call(f"nicerl2 indir={obsid}/ clobber=yes", shell=True)
			if self.bc_sel.lower() == "n":
				pass
			else:
				sp.call(
					f"barycorr infile={obsid}/xti/event_cl/ni{obsid}_0mpu7_cl.evt outfile={obsid}/xti/event_cl/bc{obsid}_0mpu7_cl.evt orbitfiles={obsid}/auxil/ni{obsid}.orb refframe=ICRS ra={self.ras[count]} dec={self.decs[count]} ephem=JPLEPH.430",
					shell=True,
				)

			base_dir = os.getcwd()
			os.chdir(f"{obsid}/xti/event_cl/")
			if self.tar_sel == "n" or self.tar_sel == "N":
				pass
			else:
				self.nicer_compress()
			os.chdir(base_dir)
			if self.q_set == "y" and self.q_path != 0:
				read_q = pd.read_csv(self.q_path)
				self.add2q(read_q, base_dir, obsid)
			elif self.q_set == "y" and self.q_path == 0:
				q = pd.DataFrame({"Input":[], "Name":[], "CALDB_ver": [], "DateTime": []})
				self.q_path = f"{base_dir}/{self.q_name}.csv"
				self.add2q(q, base_dir, obsid)
			else:
				pass
				
			count = count + 1
		
