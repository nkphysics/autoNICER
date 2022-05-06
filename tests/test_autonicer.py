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
	
