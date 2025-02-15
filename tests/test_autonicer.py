import autonicer
from astropy.time import Time
from astropy.io import fits
import datetime
import numpy as np
import os
import pytest
import shutil
import subprocess as sp
import tarfile
import glob
from termcolor import colored

base_dir = os.getcwd()
os.mkdir("data")
os.chdir("data")
an = autonicer.AutoNICER(src="PSR_B0531+21", bc=True, comp=True)


def test_passin():
    assert an.obj == "PSR_B0531+21"
    assert an.bc_sel == "y"
    assert an.tar_sel == "y"


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
        convo = float(i) * (10 ** (-9))
        assert np.floor(convo) == cyc
        cnt += 1


def lentest(expected):
    """
    General test of the observations, years, months, ras, and decs
    to ensure the expected number of parameters are stored in the
    respective variables of the AutoNICER object
    """
    lens = [
        len(an.observations),
        len(an.years),
        len(an.months),
        len(an.ras),
        len(an.decs),
    ]
    for i in lens:
        assert i == expected
    return True


def test_single_sel():
    an.command_center("1013010112")
    lt1 = lentest(1)
    assert an.observations[0] == "1013010112"


def test_short_entry():
    an.command_center("11")
    lentest(1)


def test_wrong_obsid():
    an.command_center("1013010000")
    lentest(1)


def test_cycle_sel():
    an.command_center("cycle 1")
    lentest(59)


def test_rm_single_sel():
    an.command_center("rm 1013010112")
    assert an.observations.count("1013010112") == 0
    assert "1013010112" not in an.observations
    lentest(58)


def test_back():
    last = an.observations[-1]
    an.command_center("back")
    assert an.observations.count(last) == 0
    lentest(57)


def test_duplicate():
    an.command_center("cycle 1")
    lentest(59)
    an.command_center("1013010112")
    lentest(59)


def test_rm_all():
    an.command_center("rm all")
    lentest(0)


def test_get_caldbver():
    assert autonicer.get_caldb_ver() == "xti20240206"


def test_pullreduce():
    an.q_set = "y"
    an.q_name = "test"
    an.command_center("3013010102")
    sel = an.command_center("sel")
    assert sel is True
    an.command_center("done")
    os.chdir(f"{base_dir}/data/3013010102/xti/event_cl/")
    ufa = glob.glob("*ufa.evt")
    assert len(ufa) == 0
    ufa_gz = glob.glob("*ufa.evt.gz")
    assert len(ufa_gz) == 8
    cl = glob.glob("*cl.evt")
    assert len(cl) == 1
    cl_gz = glob.glob("*cl.evt.gz")
    assert len(cl_gz) == 1
    os.chdir(f"{base_dir}")


@pytest.fixture
def setup_reprocess():
    os.chdir(f"{base_dir}/data/3013010102/")
    return autonicer.Reprocess()


def test_get_clevts(setup_reprocess):
    check = setup_reprocess
    assert len(check.clevts) == 1
    for i in check.clevts:
        assert i == "bc3013010102_0mpu7_cl.evt"
    assert check.bc_det is True
    os.chdir(f"{base_dir}/data/")


def test_getmeta(setup_reprocess):
    check = setup_reprocess
    assert check.obsid == "3013010102"
    assert check.reprocess_err == None
    os.chdir(f"{base_dir}/data/")


metadata = {
    "OBS_ID": None,
    "RA_OBJ": None,
    "DEC_OBJ": None,
}


def test_nometa():
    os.chdir(f"{base_dir}/data/3013010102/xti/event_cl/")
    cl_files = glob.glob("*cl.evt")
    for i in cl_files:
        hdul = fits.open(i)
        assert hdul[0].header["OBS_ID"] == hdul[1].header["OBS_ID"]
        for j, k in metadata.items():
            metadata[j] = hdul[0].header[j]
            del hdul[0].header[j]
        del hdul[1].header["OBS_ID"]
        hdul.writeto(i, overwrite=True)
        hdul.close()
    os.chdir(f"{base_dir}/data/3013010102")
    check = autonicer.Reprocess()
    check.reprocess()
    assert check.reprocess_err is True


def test_no_primary_obsid():
    os.chdir(f"{base_dir}/data/3013010102/xti/event_cl/")
    cl_files = glob.glob("*cl.evt")
    for i in cl_files:
        hdul = fits.open(i)
        hdul[1].header["OBS_ID"] = metadata["OBS_ID"]
        hdul[0].header["RA_OBJ"] = metadata["RA_OBJ"]
        hdul[0].header["DEC_OBJ"] = metadata["DEC_OBJ"]
        hdul.writeto(i, overwrite=True)
        hdul.close()
    os.chdir(f"{base_dir}/data/3013010102")
    check2 = autonicer.Reprocess()
    assert check2.reprocess_err is None
    assert check2.src is False


def test_decompress(setup_reprocess):
    os.chdir(f"{base_dir}/data/3013010102/xti/event_cl/")
    with open("dummy.txt", "w") as dummy:
        pass
    with tarfile.open("dummy.tar.gz", "w:gz") as tar:
        tar.add("dummy.txt")
    check = setup_reprocess
    comp_det = check.decompress()
    assert comp_det is True
    gzs = glob.glob("*evt.gz")
    tars = glob.glob("*.tar.gz")
    assert len(gzs) == 0
    assert len(tars) == 0
    os.chdir(f"{base_dir}/data/")


def test_checkcal(setup_reprocess):
    check = setup_reprocess
    check.checkcal()
    assert check.calstate == True
    os.chdir(f"{base_dir}/data/")


def test_no_caldb(setup_reprocess):
    os.chdir(f"{base_dir}/data/3013010102/xti/event_cl/")
    cl_files = glob.glob("*cl.evt")
    for i in cl_files:
        hdul = fits.open(i)
        del hdul[1].header["CALDBVER"]
        hdul.writeto(i, overwrite=True)
        hdul.close()
    check = setup_reprocess
    check.checkcal()


def get_processed_time(file):
    hdul = fits.open(file)
    dt_created = hdul[1].header["DATE"]
    hdul.close()
    return dt_created


def test_reprocess(setup_reprocess):
    check = setup_reprocess
    os.chdir(f"{check.base_dir}/xti/event_cl/")
    pbc_dt_str = get_processed_time(f"bc{check.obsid}_0mpu7_cl.evt")
    pre_bc_dt = datetime.datetime.strptime(pbc_dt_str, "%Y-%m-%dT%H:%M:%S")
    os.chdir(f"{check.base_dir}")
    autonicer.run(["--reprocess", "--bc", "--compress"])
    os.chdir(f"{check.base_dir}/xti/event_cl/")
    pobc_dt_str = get_processed_time(f"bc{check.obsid}_0mpu7_cl.evt")
    post_bc_dt = datetime.datetime.strptime(pobc_dt_str, "%Y-%m-%dT%H:%M:%S")
    assert post_bc_dt > pre_bc_dt


def test_checkcal_reprocess():
    try:
        os.chdir(f"{base_dir}/data")
        files = ["test.csv", "fail.lis", "*"]
        for i in files:
            autonicer.run(["--checkcal",
                           "--reprocess",
                           "--bc",
                           "--compress",
                           f"--inlist={i}"])
    except SystemExit:
        pass


def test_inlist_singledir():
    os.chdir(f"{base_dir}/data")
    os.remove("test.csv")
    autonicer.run(["--checkcal", "-inlist", "*"])


def test_inlist_readin():
    os.chdir(f"{base_dir}")
    files = ["README.md", "fail.lis"]
    for i in files:
        autonicer.run(["--checkcal", "-i", f"{i}"])


def test_cleanup():
    os.chdir(base_dir)
    shutil.rmtree("data/")
