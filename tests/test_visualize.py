import pylhe
import skhep_testdata
import itertools


def test_visualize(tmpdir):
    lhe_file = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
    events = pylhe.readLHEWithAttributes(lhe_file)
    start_event = 1
    stop_event = 2
    # TODO: Use f-strings once Python 2 dropped
    # TODO: Remove explicit str wrapping once Python 2 dropped
    filename = str(tmpdir.join("event{}.pdf".format(start_event)))
    for idx, event in enumerate(itertools.islice(events, start_event, stop_event)):
        pylhe.visualize(event, filename)
