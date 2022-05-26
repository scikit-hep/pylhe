import itertools

import skhep_testdata

import pylhe


def test_visualize(tmpdir):
    lhe_file = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
    events = pylhe.read_lhe_with_attributes(lhe_file)

    start_event = 1
    stop_event = 2
    filename = tmpdir.join(f"event{start_event}.pdf")
    for idx, event in enumerate(itertools.islice(events, start_event, stop_event)):
        pylhe.visualize(event, filename)


def test_LHEEvent_graph():
    lhe_file = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
    events = pylhe.read_lhe_with_attributes(lhe_file)

    # Get the first event
    event = next(events)
    # ... it contains 8 pions and a proton
    assert event.graph.source.count("&#x03c0;") == 8
    assert "<td>p</td>" in event.graph.source
