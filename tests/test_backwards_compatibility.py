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


def _orphan_lhe_init():
    init_info = pylhe.LHEInitInfo(
        beamA=2212,
        beamB=2212,
        energyA=6500.0,
        energyB=6500.0,
        PDFgroupA=10800,
        PDFgroupB=10800,
        PDFsetA=0,
        PDFsetB=0,
        weightingStrategy=3,
        numProcesses=1,
    )
    return pylhe.LHEInit(initInfo=init_info, procInfo=[], generators=[])


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


def test_lhe_init_lhe_version_backwards_compatibility():
    lhefile = _single_event_lhefile()

    assert lhefile.init.LHEVersion == "3.0"
    assert lhefile.init.LHEVersion == lhefile.version


def test_lhe_init_lhe_version_requires_parent_lhefile():
    lhe_init = _orphan_lhe_init()

    with pytest.raises(
        ValueError, match=r"LHEInit instance is not associated to an LHE file\."
    ):
        _ = lhe_init.LHEVersion


def test_lhe_init_weightgroups_backwards_compatibility():
    lhefile = pylhe.LHEFile.fromstring(
        """<LesHouchesEvents version="3.0">
<header>
<initrwgt>
  <weight id="1">This is the original event weight</weight>
  <weightgroup name="scale variation" combine="envelope">
    <weight id="2">muR = 2.0</weight>
    <weight id="3">muR = 0.5</weight>
  </weightgroup>
  <weightgroup name="PDF variation" combine="hessian">
    <weight id="4">set 01</weight>
  </weightgroup>
</initrwgt>
</header>
<init>
  2212   2212  6.5000000e+03  6.5000000e+03    -1    -1  260000  260000     3     1
  1.0000000e+00  0.0000000e+00  1.0000000e+00     1
</init>
</LesHouchesEvents>""",
        with_attributes=True,
    )

    with pytest.warns(
        DeprecationWarning,
        match=r"LHEWeightGroup is deprecated and read-only now and will be removed in a future version",
    ):
        weightgroups = lhefile.init.weightgroups

    assert list(weightgroups) == ["scale variation", "PDF variation"]
    assert "1" not in weightgroups

    scale_variation = weightgroups["scale variation"]
    assert isinstance(scale_variation, pylhe.LHEWeightGroup)
    assert scale_variation.attrib == {
        "name": "scale variation",
        "combine": "envelope",
    }
    assert list(scale_variation.weights) == ["2", "3"]
    assert isinstance(scale_variation.weights["2"], pylhe.LHEWeightInfo)
    assert scale_variation.weights["2"].attrib == {"id": "2"}
    assert scale_variation.weights["2"].name == "muR = 2.0"
    assert scale_variation.weights["2"].index == 0
    assert scale_variation.weights["3"].index == 1

    pdf_variation = weightgroups["PDF variation"]
    assert isinstance(pdf_variation, pylhe.LHEWeightGroup)
    assert list(pdf_variation.weights) == ["4"]
    assert pdf_variation.weights["4"].name == "set 01"
    assert pdf_variation.weights["4"].index == 2


def test_lhe_init_weightgroups_requires_parent_lhefile():
    lhe_init = _orphan_lhe_init()

    with pytest.raises(
        ValueError, match=r"LHEInit instance is not associated to an LHE file\."
    ):
        _ = lhe_init.weightgroups
