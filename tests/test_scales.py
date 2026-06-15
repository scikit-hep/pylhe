import pytest
import skhep_testdata

import pylhe

TEST_FILE_LHE_DIRECTPHOTON = skhep_testdata.data_path(
    "pylhe-testfile-powheg-box-v2-directphoton.lhe"
)


def test_event_scales_contains_uborn_directphoton():
    events = pylhe.LesHouchesEvents.fromfile(TEST_FILE_LHE_DIRECTPHOTON).events

    first_event = next(events)
    assert first_event.scales["uborns"] == pytest.approx(0.202472679e04)
