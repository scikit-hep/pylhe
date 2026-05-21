#  These tests solely exist to get 100% coverage also on already deprecated functions.
import pytest
import skhep_testdata

import pylhe

TEST_FILE_LHE_v3 = skhep_testdata.data_path("pylhe-testlhef3.lhe")


def _single_event_lhefile():
    lhefile = pylhe.LHEFile.fromfile(TEST_FILE_LHE_v3, with_attributes=True)
    events = lhefile.events
    lhefile.events = [next(events)]
    return lhefile


def test_write_lhe_file_path_backwards_compatibility(tmp_path):
    lhefile = _single_event_lhefile()
    output_path = tmp_path / "test.lhe"

    with pytest.warns(
        DeprecationWarning,
        match=r"write_lhe_file_path is deprecated and will be removed in a future version",
    ):
        pylhe.write_lhe_file_path(lhefile, str(output_path))

    assert output_path.read_text() == lhefile.tolhe()

    reread = pylhe.LHEFile.fromfile(str(output_path), with_attributes=True)
    assert reread.init.tolhe() == lhefile.init.tolhe()
    reread_header = getattr(reread, "header", None)
    if reread_header is not None and lhefile.header is not None:
        assert reread_header.tolhe() == lhefile.header.tolhe()
    assert next(reread.events).tolhe() == lhefile.events[0].tolhe()


def test_write_lhe_string_backwards_compatibility():
    lhefile = _single_event_lhefile()
    expected = pylhe.LHEFile(init=lhefile.init, events=lhefile.events).tolhe()

    with pytest.warns(
        DeprecationWarning,
        match=r"`write_lhe_string` is deprecated and will be removed in a future version",
    ):
        output = pylhe.write_lhe_string(lhefile.init, lhefile.events)

    assert output == expected


def test_write_lhe_file_backwards_compatibility(tmp_path):
    lhefile = _single_event_lhefile()
    expected = pylhe.LHEFile(init=lhefile.init, events=lhefile.events).tolhe()
    output_path = tmp_path / "test.lhe"

    with pytest.warns(
        DeprecationWarning,
        match=r"`write_lhe_file` is deprecated and will be removed in a future version",
    ):
        pylhe.write_lhe_file(lhefile.init, lhefile.events, str(output_path))

    assert output_path.read_text() == expected

    reread = pylhe.LHEFile.fromfile(str(output_path), with_attributes=True)
    assert getattr(reread, "header", None) is None
    assert reread.init.tolhe() == lhefile.init.tolhe()
    assert next(reread.events).tolhe() == lhefile.events[0].tolhe()


def test_mothers_backwards_compatibility():
    lhefile = _single_event_lhefile()
    event = lhefile.events[0]
    assert len(event.particles) > 3
    assert len(event.mothers(event.particles[3])) == 2
    assert event.particles[3].mothers() == event.mothers(event.particles[3])
