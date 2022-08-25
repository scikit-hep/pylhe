import pytest
import skhep_testdata

from pylhe import LHEEventInfo, LHEFile, LHEInit, LHEParticle, LHEProcInfo, read_lhe

TEST_FILE = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")


def test_LHEEvent():
    events = read_lhe(TEST_FILE)
    event = next(events)  # it contains 8 pions and a proton

    assert event.eventinfo is not None

    assert len(event.particles) == 9

    for p in event.particles:
        assert p.event == event

    assert event._graph is None


def test_LHEEventInfo_no_default_init():
    with pytest.raises(RuntimeError):
        _ = LHEEventInfo()


def test_LHEFile_default_init():
    assert LHEFile() is not None


def test_LHEInit_default_init():
    assert LHEInit() is not None


def test_LHEParticle_no_default_init():
    with pytest.raises(RuntimeError):
        _ = LHEParticle()


def test_LHEProcInfo_default_init():
    assert LHEProcInfo() is not None
