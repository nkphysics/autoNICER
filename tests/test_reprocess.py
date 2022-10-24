import autonicer
import os

base_dir = os.getcwd()
os.chdir("data/3013010102/")
check = autonicer.Reprocess()

def test_get_clevts():
    assert len(check.clevts) == 2
    for i in check.clevts:
        assert i == "bc3013010102_0mpu7_cl.evt" or i == "ni3013010102_0mpu7_cl.evt"
