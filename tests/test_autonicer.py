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
    General test of the observations, years, months, ras, and decs to ensure the expected number of parameters are stored in the respective variables of the AutoNICER object
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


def test_showsettings(capsys):
    an.command_center("settings")
    target = f"Target: {an.obj}"
    bc = f"Barycenter Correction: {an.bc_sel}"
    comp = f".gz compresion: {an.tar_sel}"
    settings = [target, bc, comp]
    out, err = capsys.readouterr()
    for i in settings:
        assert i in out


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
    assert autonicer.get_caldb_ver() == "xti20221001"


def test_pullreduce():
    an.q_set = "y"
    an.q_name = "test"
    an.command_center("3013010102")
    an.command_center("done")
    os.chdir(f"{base_dir}/data/3013010102/xti/event_cl/")
    ufa = glob.glob("*ufa.evt")
    assert len(ufa) == 0
    ufa_gz = glob.glob("*ufa.evt.gz")
    assert len(ufa_gz) == 8
    cl = glob.glob("*cl.evt")
    assert len(cl) == 2
    cl_gz = glob.glob("*cl.evt.gz")
    assert len(cl_gz) == 0
    os.chdir(f"{base_dir}")


@pytest.fixture
def setup_reprocess():
    os.chdir(f"{base_dir}/data/3013010102/")
    return autonicer.Reprocess()


def test_get_clevts(setup_reprocess):
    check = setup_reprocess
    assert len(check.clevts) == 2
    for i in check.clevts:
        assert i == "bc3013010102_0mpu7_cl.evt" or i == "ni3013010102_0mpu7_cl.evt"
    assert check.bc_det is True
    os.chdir(f"{base_dir}/data/")


def test_getmeta(setup_reprocess):
    check = setup_reprocess
    assert check.obsid == "3013010102"
    assert check.src == "PSR_B0531+21"
    assert check.ra == 83.63308
    assert check.dec == 22.01449
    os.chdir(f"{base_dir}/data/")


def test_nometa(capsys):
    os.chdir(f"{base_dir}/data/3013010102/xti/event_cl/")
    cl_files = glob.glob("*cl.evt")
    metadata = {
        "OBJECT": "PSR_B0531+21",
        "OBS_ID": "3013010102",
        "RA_OBJ": 83.63308,
        "DEC_OBJ": 22.01449,
    }
    for i in cl_files:
        hdul = fits.open(i)
        for j, k in metadata.items():
            del hdul[0].header[j]
        hdul.writeto(i, overwrite=True)
        hdul.close()
    os.chdir(f"{base_dir}/data/3013010102")
    check = autonicer.Reprocess()
    check.reprocess()
    out, err = capsys.readouterr()
    fail = "Consider Re-downloading and reducing this dataset"
    fail_reprocess = "!!!!! CANNOT REPROCESS !!!!!"
    assert fail in out
    assert fail_reprocess in out
    assert check.reprocess_err is True

    os.chdir(f"{base_dir}/data/3013010102/xti/event_cl/")
    for i in cl_files:
        hdul = fits.open(i)
        hdul[0].header["OBS_ID"] = metadata["OBS_ID"]
        hdul[0].header["RA_OBJ"] = metadata["RA_OBJ"]
        hdul[0].header["DEC_OBJ"] = metadata["DEC_OBJ"]
        hdul.writeto(i, overwrite=True)
        hdul.close()
    os.chdir(f"{base_dir}/data/3013010102")
    check2 = autonicer.Reprocess()
    out2, err2 = capsys.readouterr()
    fail2 = "Unable to identify Object -> IS OK"
    assert fail2 in out
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


def test_no_caldb(capsys, setup_reprocess):
    os.chdir(f"{base_dir}/data/3013010102/xti/event_cl/")
    cl_files = glob.glob("*cl.evt")
    for i in cl_files:
        hdul = fits.open(i)
        del hdul[0].header["CALDBVER"]
        hdul.writeto(i, overwrite=True)
        hdul.close()
    check = setup_reprocess
    check.checkcal()
    out, err = capsys.readouterr()
    fail = "!!!!! CANNOT IDENTIFY CALDB !!!!!"
    assert fail in out


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


def test_checkcal_reprocess(capsys):
    try:
        os.chdir(f"{base_dir}/data")
        files = ["test.csv", "fail.lis", "*/"]
        for i in files:
            autonicer.run(
                ["--checkcal", "--reprocess", "--bc", "--compress", f"--inlist={i}"]
            )
    except SystemExit:
        pass
    out, err = capsys.readouterr()
    passing = f"----------  Passing Reprocess of 3013010102  ----------"
    fail = "DATASETS NOT FOUND"
    unix = "Migrating to 3013010102"
    assert passing in out
    assert fail in out
    assert unix in out


def test_cleanup():
    os.chdir(base_dir)
    shutil.rmtree("data/")
