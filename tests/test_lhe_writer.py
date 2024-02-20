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
    skhep_testdata.data_path("pylhe-testfile-powheg-box-v2-%s.lhe" % (proc))
    for proc in ["Z", "W", "Zj", "trijet", "directphoton", "hvq"]
]

# TODO add write lhe gz


def test_write_lhe_eventline():
    """
    """
    events = pylhe.read_lhe_with_attributes(TEST_FILE_LHE_v3)

    assert events
    for e in events:
        assert e.particles[0].tolhe() == "    5  -1   0   0 501   0 0.0000000000e+00 0.0000000000e+00 1.4322906000e+02 1.4330946000e+02 4.8000000000e+00 0.0000e+00 0.0000e+00"
        break



def test_write_lhe_eventinfo():
    """
    """
    events = pylhe.read_lhe_with_attributes(TEST_FILE_LHE_v3)

    assert events
    for e in events:
        assert e.eventinfo.tolhe() == "  5     66 5.0109093000e+01 1.4137688000e+02 7.5563862000e-03 1.2114027000e-01"
        break


def test_write_read_lhe_identical():
    pass