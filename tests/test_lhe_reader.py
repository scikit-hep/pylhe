import gzip
import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import skhep_testdata

import pylhe

TEST_FILE = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")


@pytest.fixture(scope="session")
def testdata_gzip_file():
    test_data = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
    # Create a tmp path that is named with .gz
    tmp_file = NamedTemporaryFile()
    tmp_path = Path(Path(tmp_file.name).parent.joinpath("pylhe-testfile-pr29.lhe.gz"))
    shutil.copy(tmp_file.name, tmp_path)

    # create pylhe-testfile-pr29.lhe.gz
    with open(test_data, "rb") as readfile:
        with gzip.open(tmp_path, "wb") as writefile:
            shutil.copyfileobj(readfile, writefile)
    yield tmp_path

    # teardown
    os.remove(tmp_path)


def test_gzip_open(tmpdir, testdata_gzip_file):
    assert pylhe._extract_gzip_file(TEST_FILE) == TEST_FILE

    assert pylhe._extract_gzip_file(testdata_gzip_file)

    tmp_path = tmpdir.join("notrealfile.lhe")
    assert pylhe._extract_gzip_file(tmp_path) == tmp_path

    tmp_path = tmpdir.join("notrealfile.lhe.gz")
    tmp_path.write("")
    with pytest.raises(OSError):
        pylhe._extract_gzip_file(tmp_path)


def test_event_count():
    assert pylhe.readNumEvents(TEST_FILE) == 791


def test_lhe_init():
    init_data = pylhe.readLHEInit(TEST_FILE)
    init_info = init_data["initInfo"]
    assert init_info["beamA"] == pytest.approx(1.0)
    assert init_info["beamB"] == pytest.approx(2.0)
    assert init_info["energyA"] == pytest.approx(1.234567)
    assert init_info["energyB"] == pytest.approx(2.345678)
    assert init_info["PDFgroupA"] == pytest.approx(3.0)
    assert init_info["PDFgroupB"] == pytest.approx(4.0)
    assert init_info["PDFsetA"] == pytest.approx(5.0)
    assert init_info["PDFsetB"] == pytest.approx(6.0)
    assert init_info["weightingStrategy"] == pytest.approx(7.0)
    assert init_info["numProcesses"] == pytest.approx(8.0)


def test_readLHE(testdata_gzip_file):
    assert pylhe.readLHE(TEST_FILE)
    assert pylhe.readLHE(testdata_gzip_file)
