# Regression tests for compatibility and previously-removed/legacy behaviors.
import skhep_testdata

import pylhe

TEST_FILE_LHE_v3 = skhep_testdata.data_path("pylhe-testlhef3.lhe")


def _single_event_lhefile():
    lhefile = pylhe.LHEFile.fromfile(TEST_FILE_LHE_v3, with_attributes=True)
    events = lhefile.events
    lhefile.events = [next(events)]
    return lhefile


def test_mothers_backwards_compatibility():
    lhefile = _single_event_lhefile()
    event = lhefile.events[0]
    assert len(event.particles) > 3
    assert len(event.mothers(event.particles[3])) == 2
