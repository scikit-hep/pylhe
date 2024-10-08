import gzip
import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import skhep_testdata

import pylhe
from pylhe import LHEEvent

TEST_FILE_LHE_v1 = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
TEST_FILE_LHE_v3 = skhep_testdata.data_path("pylhe-testlhef3.lhe")
TEST_FILE_LHE_INITRWGT_WEIGHTS = skhep_testdata.data_path(
    "pylhe-testfile-powheg-box-v2-hvq.lhe"
)
TEST_FILE_LHE_RWGT_WGT = skhep_testdata.data_path("pylhe-testfile-powheg-box-v2-W.lhe")
TEST_FILES_LHE_POWHEG = [
    skhep_testdata.data_path(f"pylhe-testfile-powheg-box-v2-{proc}.lhe")
    for proc in ["Z", "W", "Zj", "trijet", "directphoton", "hvq"]
]


@pytest.fixture(scope="session")
def testdata_gzip_file():
    test_data = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
    tmp_path = Path(NamedTemporaryFile().name)

    # create what is basically pylhe-testfile-pr29.lhe.gz
    with open(test_data, "rb") as readfile, gzip.open(tmp_path, "wb") as writefile:
        shutil.copyfileobj(readfile, writefile)
    yield tmp_path

    # teardown
    os.remove(tmp_path)


def test_gzip_open(testdata_gzip_file):
    assert pylhe._extract_fileobj(TEST_FILE_LHE_v1)
    assert pylhe._extract_fileobj(testdata_gzip_file)

    # Needs path-like object, not a fileobj
    with pytest.raises(TypeError), open(TEST_FILE_LHE_v1, "rb") as fileobj:
        pylhe._extract_fileobj(fileobj)

    with open(TEST_FILE_LHE_v1, "rb") as fileobj:
        assert isinstance(pylhe._extract_fileobj(TEST_FILE_LHE_v1), type(fileobj))
        assert isinstance(pylhe._extract_fileobj(Path(TEST_FILE_LHE_v1)), type(fileobj))
    assert isinstance(pylhe._extract_fileobj(testdata_gzip_file), gzip.GzipFile)
    assert isinstance(pylhe._extract_fileobj(Path(testdata_gzip_file)), gzip.GzipFile)


def test_read_num_events(testdata_gzip_file):
    assert pylhe.read_num_events(TEST_FILE_LHE_v1) == 791
    assert pylhe.read_num_events(TEST_FILE_LHE_v1) == pylhe.read_num_events(
        testdata_gzip_file
    )


def test_read_lhe_init_gzipped_file(testdata_gzip_file):
    assert pylhe.read_lhe_init(TEST_FILE_LHE_v1) == pylhe.read_lhe_init(
        testdata_gzip_file
    )


def test_read_lhe_init_v1():
    """
    Test method read_lhe_init() on a LesHouchesEvents version="1.0" file.
    """
    init_data = pylhe.read_lhe_init(TEST_FILE_LHE_v1)

    assert init_data["LHEVersion"] == pytest.approx(1.0)

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

    assert init_data["procInfo"] == []


def test_read_lhe_init_v3():
    """
    Test method read_lhe_init() on a LesHouchesEvents version="3.0" file.
    """
    init_data = pylhe.read_lhe_init(TEST_FILE_LHE_v3)

    assert len(init_data["weightgroup"]) == 1
    assert len(init_data["weightgroup"]["scale_variation"]["weights"]) == 9


def test_read_lhe_v1():
    """
    Test method read_lhe() on a LesHouchesEvents version="1.0" file.
    """
    events = pylhe.read_lhe(TEST_FILE_LHE_v1)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)


def test_read_lhe_v3():
    """
    Test method read_lhe() on a LesHouchesEvents version="3.0" file.
    """
    events = pylhe.read_lhe(TEST_FILE_LHE_v3)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)


def test_read_lhe_with_attributes_v1():
    """
    Test method read_lhe_with_attributes() on a LesHouchesEvents version="1.0" file.
    """
    events = pylhe.read_lhe_with_attributes(TEST_FILE_LHE_v1)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)


def test_read_lhe_with_attributes_v3():
    """
    Test method read_lhe_with_attributes() on a LesHouchesEvents version="3.0" file.
    """
    events = pylhe.read_lhe_with_attributes(TEST_FILE_LHE_v3)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)


@pytest.mark.parametrize("file", TEST_FILES_LHE_POWHEG)
def test_read_lhe_powheg(file):
    """
    Test method read_lhe() on several types of LesHouchesEvents POWHEG files.
    """
    events = pylhe.read_lhe(file)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)


@pytest.mark.parametrize("file", TEST_FILES_LHE_POWHEG)
def test_read_lhe_with_attributes_powheg(file):
    """
    Test method read_lhe_with_attributes() on several types of LesHouchesEvents POWHEG files.
    """
    events = pylhe.read_lhe_with_attributes(file)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)


@pytest.mark.parametrize(
    "file", [TEST_FILE_LHE_INITRWGT_WEIGHTS, TEST_FILE_LHE_RWGT_WGT]
)
def test_read_lhe_file(file):
    """
    Test that the read_lhe_file function works as the individual reads.
    """
    lhefile = pylhe.read_lhe_file(file, with_attributes=False)
    lheinit = pylhe.read_lhe_init(file)
    lheevents = pylhe.read_lhe(file)

    assert lheinit == lhefile.init
    assert next(lheevents).tolhe() == next(lhefile.events).tolhe()

    lhefile = pylhe.read_lhe_file(file, with_attributes=True)
    lheevents = pylhe.read_lhe_with_attributes(file)

    assert lheinit == lhefile.init
    assert next(lheevents).tolhe() == next(lhefile.events).tolhe()


def test_read_lhe_initrwgt_weights():
    """
    Test the weights from initrwgt with a weights list.
    """
    events = pylhe.read_lhe_with_attributes(TEST_FILE_LHE_INITRWGT_WEIGHTS)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)
        assert len(e.weights) > 0


def test_read_lhe_rwgt_wgt():
    """
    Test the weights from rwgt with a wgt list.
    """
    events = pylhe.read_lhe_with_attributes(TEST_FILE_LHE_RWGT_WGT)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)
        assert len(e.weights) > 0


def test_issue_102():
    """
    Test a file containing lines starting with "#aMCatNLO".
    """
    assert pylhe.read_num_events(TEST_FILE_LHE_v3) == 59
    assert len(list(pylhe.read_lhe(TEST_FILE_LHE_v3))) == len(
        list(pylhe.read_lhe_with_attributes(TEST_FILE_LHE_v3))
    )
