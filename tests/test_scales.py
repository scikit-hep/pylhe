import skhep_testdata

import pylhe

TEST_FILE_LHE_DIRECTPHOTON = skhep_testdata.data_path(
    "pylhe-testfile-powheg-box-v2-directphoton.lhe"
)


def test_event_scales_contains_uborn_directphoton():
    events = pylhe.read_lhe_with_attributes(TEST_FILE_LHE_DIRECTPHOTON)

    first_event = next(events)
    assert first_event.scales["uborns"] == 0.202472679e04
