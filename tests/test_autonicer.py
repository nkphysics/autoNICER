import autonicer
from astropy.time import Time
import datetime
import numpy as np

an = autonicer.AutoNICER("crab pulsar")

def test_passin():
	assert an.obj == "crab pulsar"
	
def test_call_nicer():
	an.call_nicer()
	for i in an.xti["OBSID"]:
		assert isinstance(i, str) == True
		assert isinstance(i, bytes) == False
	for i in an.xti["TIME"]:
		assert isinstance(i, float) == False
		assert isinstance(i, datetime.datetime) == True
		
def test_make_cycle():
	an.make_cycle()
	assert len(an.xti["Cycle#"]) == len(an.xti["OBSID"])
	cnt = 0
	for i in an.xti["OBSID"]:
		cyc = an.xti.loc[cnt, "Cycle#"]
		convo = float(i) * (10**(-9))
		assert np.floor(convo) == cyc
		cnt += 1
		
def test_single_sel():
	an.command_center("1013010112")
	assert len(an.observations) == 1
	assert an.observations[0] == "1013010112"
	an.command_center("rm all")
	assert len(an.observations) == 0
	
def test_cycle_sel():
	an.command_center("cycle 1")
	assert len(an.observations) == 59
	assert len(an.ras) == len(an.observations)
	assert len(an.decs) == len(an.ras)
	an.command_center("rm 1013010112")
	assert an.observations.count("1013010112") == 0
	assert len(an.observations) == 58
	assert len(an.ras) == len(an.observations)
	assert len(an.decs) == len(an.ras)
	
def test_back():
	last = an.observations[-1]
	an.command_center("back")
	assert an.observations.count(last) == 0
	assert len(an.observations) == 57
	assert len(an.ras) == len(an.observations)
	assert len(an.decs) == len(an.ras)
	
def get_caldb_ver():
	assert an.get_caldb_ver() == "xti20210707"
	
