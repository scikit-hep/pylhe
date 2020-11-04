import pylhe
import skhep_testdata
import itertools


def test_visualize():
    lhe_file = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
    events = pylhe.readLHEWithAttributes(lhe_file)
    start_event = 1
    stop_event = 2
    for idx, event in enumerate(itertools.islice(events, start_event, stop_event)):
        pylhe.visualize(event, f"event{idx+start_event}.pdf")
