import autonicer
from astropy.time import Time
import datetime
import mock

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
		
