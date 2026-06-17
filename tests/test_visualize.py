import copy
import itertools

import skhep_testdata

import pylhe

# Minimal LHE file with 3 particles: two identical incoming gluons (particles 1 and 2)
# and one outgoing particle (particle 3) with mother1=1, mother2=2.
# The two gluons are field-identical (same id, status, colors, momenta, etc.) which
# would cause list.index() to return index 0 for both, producing duplicate edges.
_IDENTICAL_MOTHERS_LHE = """\
<LesHouchesEvents version="3.0">
<init>
  2212   2212  6.5000000e+03  6.5000000e+03    -1    -1  260000  260000     3     1
  1.0000000e+00  0.0000000e+00  1.0000000e+00     1
</init>
<event>
     3     1  1.0000000e+00  9.1188200e+01  7.5425328e-03  1.1800000e-01
        21    -1     0     0   504     0  0.000000000e+00  0.000000000e+00  5.0000000e+02  5.0000000e+02  0.0  0.  9.
        21    -1     0     0   506   504  0.000000000e+00  0.000000000e+00 -5.0000000e+02  5.0000000e+02  0.0  0.  9.
        21     1     1     2     0     0  0.000000000e+00  0.000000000e+00  0.0000000e+00  1.0000000e+03  0.0  0.  9.
</event>
</LesHouchesEvents>
"""


def test_LHEEvent_graph_source():
    lhe_file = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
    events = pylhe.LesHouchesEvents.fromfile(lhe_file).events

    # Get the first event
    event = next(events)
    # ... it contains 8 pions and a proton
    # pi unicode character is '&#x03c0;'
    assert event.graph.source.count("&#x03c0;") == 8
    assert "<td>p</td>" in event.graph.source


def test_LHEEvent_graph_source_nonstandard_pdg():
    lhe_file = skhep_testdata.data_path("pylhe-testfile-pr180.lhe")
    events = pylhe.LesHouchesEvents.fromfile(lhe_file).events

    # Get the first event
    event = next(events)
    # building the graph should succeed even though there is
    # a non-standard PDG ID 1023 and the name in the graph
    # source should just be the ID number itself
    assert event.graph.source.count("<td>1023</td>") == 1


def test_LHEEvent_graph_render():
    lhe_file = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
    events = pylhe.LesHouchesEvents.fromfile(lhe_file).events

    event = next(itertools.islice(events, 1, 2))
    event.graph.render(filename="test_event1", format="pdf", cleanup=True)


def test_mime():
    lhe_file = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
    events = pylhe.LesHouchesEvents.fromfile(lhe_file).events

    event = next(itertools.islice(events, 1, 2))
    assert event._repr_mimebundle_() == event.graph._repr_mimebundle_()


def test_graph_distinct_edges_for_identical_mother_particles():
    """
    When two field-identical particles are both mothers of a third particle,
    the graph must contain edges from each mother to the daughter — not two
    edges from the first mother.  This was broken when _build_graph used
    list.index() (which returns the first match) instead of the 1-based
    mother1/mother2 indices directly.
    """
    lhefile = pylhe.LHEFile.fromstring(_IDENTICAL_MOTHERS_LHE)
    event = next(lhefile.events)
    source = event.graph.source
    # Edge from particle 0 (first gluon) to particle 2 (daughter)
    assert "0 -> 2" in source
    # Edge from particle 1 (second gluon) to particle 2 (daughter)
    assert "1 -> 2" in source


def test_graph_no_attr_dict_in_source():
    """
    The graph DOT source must not contain 'attr_dict'.  Previously every node
    was constructed with attr_dict=str(p.__dict__), which dumped the full event
    repr (including the back-reference to the entire event) into every node.
    """
    lhefile = pylhe.LHEFile.fromstring(_IDENTICAL_MOTHERS_LHE)
    event = next(lhefile.events)
    assert "attr_dict" not in event.graph.source


def test_graph_field_excluded_from_eq_and_repr():
    """
    _graph must be excluded from __eq__ and __repr__ so that:
    - two semantically equal events compare equal even if one has built its graph
    - repr() does not contain a Digraph object address
    """
    # Re-parse to get a fresh copy with no cached graph
    lhefile2 = pylhe.LHEFile.fromstring(_IDENTICAL_MOTHERS_LHE)
    event_a = next(iter(lhefile2.events))
    event_b = copy.deepcopy(event_a)

    # Build the graph on one copy only
    _ = event_a.graph
    assert event_a._graph is not None
    assert event_b._graph is None

    # They must still compare equal because _graph is excluded from __eq__
    assert event_a == event_b

    # repr must not leak the Digraph object
    assert "Digraph" not in repr(event_a)
