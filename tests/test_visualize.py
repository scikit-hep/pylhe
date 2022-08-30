import itertools

import skhep_testdata

import pylhe


def test_LHEEvent_graph_source():
    lhe_file = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
    events = pylhe.read_lhe_with_attributes(lhe_file)

    # Get the first event
    event = next(events)
    # ... it contains 8 pions and a proton
    # pi unicode charecter is '&#x03c0;'
    assert event.graph.source.count("&#x03c0;") == 8
    assert "<td>p</td>" in event.graph.source


def test_LHEEvent_graph_render():
    lhe_file = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
    events = pylhe.read_lhe_with_attributes(lhe_file)

    event = next(itertools.islice(events, 1, 2))
    event.graph.render(filename="test_event1", format="pdf", cleanup=True)
