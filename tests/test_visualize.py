import itertools

import skhep_testdata

import pylhe

TEST_FILE = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")


def test_visualize(tmpdir):
    events = pylhe.read_lhe_with_attributes(TEST_FILE)
    start_event = 1
    stop_event = 2
    filename = tmpdir.join(f"event{start_event}.pdf")
    for idx, event in enumerate(itertools.islice(events, start_event, stop_event)):
        pylhe.visualize(event, filename)


def test_LHEEvent_graph():
    events = pylhe.read_lhe_with_attributes(TEST_FILE)
    # Get the first event
    e = next(events)
    # ... it contains 8 pions and a proton
    assert e.graph.source.count("&#x03c0;") == 8
    assert "<td>p</td>" in e.graph.source
