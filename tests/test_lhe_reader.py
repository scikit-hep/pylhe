import gzip
import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import skhep_testdata

import pylhe
from pylhe import LHEEvent

TEST_FILE_LHE_v1 = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
TEST_FILE_LHE_v3 = skhep_testdata.data_path("pylhe-testlhef3.lhe")
TEST_FILE_LHE_INITRWGT_WEIGHTS = skhep_testdata.data_path(
    "pylhe-testfile-powheg-box-v2-hvq.lhe"
)
TEST_FILE_LHE_RWGT_WGT = skhep_testdata.data_path("pylhe-testfile-powheg-box-v2-W.lhe")
TEST_FILES_LHE_POWHEG = [
    skhep_testdata.data_path(f"pylhe-testfile-powheg-box-v2-{proc}.lhe")
    for proc in ["Z", "W", "Zj", "trijet", "directphoton", "hvq"]
]
TEST_FILES_LHE_MADGRAPH = [
    skhep_testdata.data_path("pylhe-testfile-madgraph-2.0.0-wbj.lhe"),
    skhep_testdata.data_path("pylhe-testfile-madgraph-2.2.1-Z-ckkwl.lhe.gz"),
    skhep_testdata.data_path("pylhe-testfile-madgraph-2.2.1-Z-fxfx.lhe.gz"),
    skhep_testdata.data_path("pylhe-testfile-madgraph-2.2.1-Z-mlm.lhe.gz"),
    skhep_testdata.data_path("pylhe-testfile-madgraph5-3.5.8-pp_to_jj.lhe.gz"),
]
TEST_FILES_LHE_PYTHIA = [
    skhep_testdata.data_path("pylhe-testfile-pythia-6.413-ttbar.lhe"),
    skhep_testdata.data_path("pylhe-testfile-pythia-8.3.14-weakbosons.lhe"),
]
TEST_FILES_LHE_SHERPA = [
    skhep_testdata.data_path("pylhe-testfile-sherpa-3.0.1-eejjj.lhe"),
]
TEST_FILES_LHE_WHIZARD = [
    skhep_testdata.data_path("pylhe-testfile-whizard-3.1.4-eeWW.lhe"),
]
TEST_FILES_LHE_GENERATORS = [
    *TEST_FILES_LHE_MADGRAPH,
    *TEST_FILES_LHE_POWHEG,
    *TEST_FILES_LHE_PYTHIA,
    *TEST_FILES_LHE_SHERPA,
    *TEST_FILES_LHE_WHIZARD,
]


@pytest.fixture(scope="session")
def testdata_gzip_file():
    test_data = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
    tmp_path = Path(NamedTemporaryFile().name)

    # create what is basically pylhe-testfile-pr29.lhe.gz
    with open(test_data, "rb") as readfile, gzip.open(tmp_path, "wb") as writefile:
        shutil.copyfileobj(readfile, writefile)
    yield tmp_path

    # teardown
    os.remove(tmp_path)


def test_gzip_open(testdata_gzip_file):
    assert pylhe._extract_fileobj(TEST_FILE_LHE_v1)
    assert pylhe._extract_fileobj(testdata_gzip_file)

    # Needs path-like object, not a fileobj
    with pytest.raises(TypeError), open(TEST_FILE_LHE_v1, "rb") as fileobj:
        pylhe._extract_fileobj(fileobj)

    with open(TEST_FILE_LHE_v1, "rb") as fileobj:
        assert isinstance(pylhe._extract_fileobj(TEST_FILE_LHE_v1), type(fileobj))
        assert isinstance(pylhe._extract_fileobj(Path(TEST_FILE_LHE_v1)), type(fileobj))
    assert isinstance(pylhe._extract_fileobj(testdata_gzip_file), gzip.GzipFile)
    assert isinstance(pylhe._extract_fileobj(Path(testdata_gzip_file)), gzip.GzipFile)


def test_read_num_events(testdata_gzip_file):
    assert pylhe.read_num_events(TEST_FILE_LHE_v1) == 791
    assert pylhe.read_num_events(TEST_FILE_LHE_v1) == pylhe.read_num_events(
        testdata_gzip_file
    )


def test_read_lhe_init_gzipped_file(testdata_gzip_file):
    assert pylhe.read_lhe_init(TEST_FILE_LHE_v1) == pylhe.read_lhe_init(
        testdata_gzip_file
    )


def test_read_lhe_init_v1():
    """
    Test method read_lhe_init() on a LesHouchesEvents version="1.0" file.
    """
    init_data = pylhe.read_lhe_init(TEST_FILE_LHE_v1)

    assert init_data["LHEVersion"] == pytest.approx(1.0)

    init_info = init_data["initInfo"]
    assert init_info["beamA"] == pytest.approx(1.0)
    assert init_info["beamB"] == pytest.approx(2.0)
    assert init_info["energyA"] == pytest.approx(1.234567)
    assert init_info["energyB"] == pytest.approx(2.345678)
    assert init_info["PDFgroupA"] == pytest.approx(3.0)
    assert init_info["PDFgroupB"] == pytest.approx(4.0)
    assert init_info["PDFsetA"] == pytest.approx(5.0)
    assert init_info["PDFsetB"] == pytest.approx(6.0)
    assert init_info["weightingStrategy"] == pytest.approx(7.0)
    assert init_info["numProcesses"] == pytest.approx(8.0)

    assert init_data["procInfo"] == []


def test_read_lhe_init_v3():
    """
    Test method read_lhe_init() on a LesHouchesEvents version="3.0" file.
    """
    init_data = pylhe.read_lhe_init(TEST_FILE_LHE_v3)

    assert len(init_data["weightgroup"]) == 1
    assert len(init_data["weightgroup"]["scale_variation"]["weights"]) == 9


def test_read_lhe_v1():
    """
    Test method read_lhe() on a LesHouchesEvents version="1.0" file.
    """
    events = pylhe.read_lhe(TEST_FILE_LHE_v1)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)


def test_read_lhe_v3():
    """
    Test method read_lhe() on a LesHouchesEvents version="3.0" file.
    """
    events = pylhe.read_lhe(TEST_FILE_LHE_v3)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)


def test_read_lhe_with_attributes_v1():
    """
    Test method read_lhe_with_attributes() on a LesHouchesEvents version="1.0" file.
    """
    events = pylhe.read_lhe_with_attributes(TEST_FILE_LHE_v1)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)


def test_read_lhe_with_attributes_v3():
    """
    Test method read_lhe_with_attributes() on a LesHouchesEvents version="3.0" file.
    """
    events = pylhe.read_lhe_with_attributes(TEST_FILE_LHE_v3)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)


@pytest.mark.parametrize("file", TEST_FILES_LHE_GENERATORS)
def test_read_lhe_generator(file):
    """
    Test method read_lhe() on several types of LesHouchesEvents generator files.
    """
    events = pylhe.read_lhe(file)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)


@pytest.mark.parametrize("file", TEST_FILES_LHE_GENERATORS)
def test_read_lhe_with_attributes_generator(file):
    """
    Test method read_lhe_with_attributes() on several types of LesHouchesEvents generator files.
    """
    events = pylhe.read_lhe_with_attributes(file)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)


@pytest.mark.parametrize(
    "file", [TEST_FILE_LHE_INITRWGT_WEIGHTS, TEST_FILE_LHE_RWGT_WGT]
)
def test_read_lhe_file(file):
    """
    Test that the read_lhe_file function works as the individual reads.
    """
    lhefile = pylhe.read_lhe_file(file, with_attributes=False)
    lheinit = pylhe.read_lhe_init(file)
    lheevents = pylhe.read_lhe(file)

    assert lheinit == lhefile.init
    assert next(lheevents).tolhe() == next(lhefile.events).tolhe()

    lhefile = pylhe.read_lhe_file(file, with_attributes=True)
    lheevents = pylhe.read_lhe_with_attributes(file)

    assert lheinit == lhefile.init
    assert next(lheevents).tolhe() == next(lhefile.events).tolhe()


def test_read_lhe_initrwgt_weights():
    """
    Test the weights from initrwgt with a weights list.
    """
    events = pylhe.read_lhe_with_attributes(TEST_FILE_LHE_INITRWGT_WEIGHTS)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)
        assert len(e.weights) > 0


def test_read_lhe_rwgt_wgt():
    """
    Test the weights from rwgt with a wgt list.
    """
    events = pylhe.read_lhe_with_attributes(TEST_FILE_LHE_RWGT_WGT)

    assert events
    for e in events:
        assert isinstance(e, LHEEvent)
        assert len(e.weights) > 0


def test_issue_102():
    """
    Test a file containing lines starting with "#aMCatNLO".
    """
    assert pylhe.read_num_events(TEST_FILE_LHE_v3) == 59
    assert len(list(pylhe.read_lhe(TEST_FILE_LHE_v3))) == len(
        list(pylhe.read_lhe_with_attributes(TEST_FILE_LHE_v3))
    )


def test_read_lhe_init_raises():
    """
    Test that the <init> block raises AttributeErrors on faulty inputs.
    """

    with pytest.raises(
        AttributeError, match="weightgroup must have attribute 'type' or 'name'."
    ):
        pylhe.LHEInit.fromstring(
            """<init>
   2212   2212  4.0000000e+03  4.0000000e+03    -1    -1  21100  21100    -4     1
 5.0109086e+01  8.9185414e-02  5.0109093e+01    66
<initrwgt>
  <weightgroup combine="envelope">
    <weight id="1001">muR=0.10000E+01 muF=0.10000E+01</weight>
    <weight id="1002">muR=0.10000E+01 muF=0.20000E+01</weight>
    <weight id="1003">muR=0.10000E+01 muF=0.50000E+00</weight>
    <weight id="1004">muR=0.20000E+01 muF=0.10000E+01</weight>
    <weight id="1005">muR=0.20000E+01 muF=0.20000E+01</weight>
    <weight id="1006">muR=0.20000E+01 muF=0.50000E+00</weight>
    <weight id="1007">muR=0.50000E+00 muF=0.10000E+01</weight>
    <weight id="1008">muR=0.50000E+00 muF=0.20000E+01</weight>
    <weight id="1009">muR=0.50000E+00 muF=0.50000E+00</weight>
  </weightgroup>
</initrwgt>
</init>"""
        )

    with pytest.raises(AttributeError, match="weight must have attribute 'id'"):
        pylhe.LHEInit.fromstring(
            """<init>
   2212   2212  4.0000000e+03  4.0000000e+03    -1    -1  21100  21100    -4     1
 5.0109086e+01  8.9185414e-02  5.0109093e+01    66
<initrwgt>
  <weightgroup name="a fake name" combine="envelope">
    <spam>muR=0.10000E+01 muF=0.10000E+01</spam>
    <weight id="1001">muR=0.10000E+01 muF=0.10000E+01</weight>
    <weight id="1002">muR=0.10000E+01 muF=0.20000E+01</weight>
    <weight id="1003">muR=0.10000E+01 muF=0.50000E+00</weight>
    <weight id="1004">muR=0.20000E+01 muF=0.10000E+01</weight>
    <weight id="1005">muR=0.20000E+01 muF=0.20000E+01</weight>
    <weight id="1006">muR=0.20000E+01 muF=0.50000E+00</weight>
    <weight id="1007">muR=0.50000E+00 muF=0.10000E+01</weight>
    <weight id="1008">muR=0.50000E+00 muF=0.20000E+01</weight>
    <weight>muR=0.50000E+00 muF=0.50000E+00</weight>
  </weightgroup>
</initrwgt>
</init>"""
        )


def test_event_at_position_5():
    """
    Test that the event at position 5 has the expected values.
    The element at position 5 in the LHE file is:

    <event>
         5     0  1.554392E-03  0.000000E+00  0.000000E+00  0.000000E+00
         111    0    0    0    0    0 -9.7035523745E-01 -9.8435906372E-01  5.1424008917E+00  5.3267140888E+00  1.3800000000E-01 0. 9.
         211    0    0    0    0    0 -2.1024089632E-01 -3.2883303721E-02  3.1406432734E+00  3.1508676134E+00  1.3800000000E-01 0. 9.
        -211    0    0    0    0    0  3.9695103971E-02 -2.2872518121E-01  1.0496526207E-01  2.8974577830E-01  1.3800000000E-01 0. 9.
        2212    0    0    0    0    0 -8.6160811751E-01 -7.3819273849E-01  7.4246467306E+00  7.5762050386E+00  9.9307937557E-01 0. 9.
         211    0    0    0    0    0 -4.7889071830E-01 -2.8340027352E-01  1.5195379346E+00  1.6240971553E+00  1.3800000000E-01 0. 9.
    # 5    34  1.5543917618E-03   3.6288856778E+01  0.0000000000E+00  0.0000000000E+00  3.6288856778E+01   1.9388062018E+01  2.3242767182E+00  2.1256769904E+00  1.9130504008E+01   9.0374892691E-01 -1.4114
    </event>
    """
    events = pylhe.read_lhe(TEST_FILE_LHE_v1)

    # Get the event at position 5 (0-indexed)
    target_event = None
    for i, event in enumerate(events):
        if i == 5:
            target_event = event
            break

    assert target_event is not None, "Event at position 5 should exist"

    # Test event info values from the LHE format comment
    assert target_event.eventinfo.nparticles == pytest.approx(5.0)
    assert target_event.eventinfo.pid == pytest.approx(0.0)
    assert target_event.eventinfo.weight == pytest.approx(1.554392e-03)
    assert target_event.eventinfo.scale == pytest.approx(0.0)
    assert target_event.eventinfo.aqed == pytest.approx(0.0)
    assert target_event.eventinfo.aqcd == pytest.approx(0.0)

    # Test that we have the expected number of particles
    assert len(target_event.particles) == 5

    # Test particle properties based on the LHE event data
    # First particle: 111 (pi0)
    first_particle = target_event.particles[0]
    assert first_particle.id == pytest.approx(111.0)  # pi0
    assert first_particle.status == pytest.approx(0.0)
    assert first_particle.mother1 == pytest.approx(0.0)
    assert first_particle.mother2 == pytest.approx(0.0)
    assert first_particle.px == pytest.approx(-9.7035523745e-01)
    assert first_particle.py == pytest.approx(-9.8435906372e-01)
    assert first_particle.pz == pytest.approx(5.1424008917e00)
    assert first_particle.e == pytest.approx(5.3267140888e00)
    assert first_particle.m == pytest.approx(1.3800000000e-01)

    # Second particle: 211 (pi+)
    second_particle = target_event.particles[1]
    assert second_particle.id == pytest.approx(211.0)  # pi+
    assert second_particle.status == pytest.approx(0.0)
    assert second_particle.px == pytest.approx(-2.1024089632e-01)
    assert second_particle.py == pytest.approx(-3.2883303721e-02)
    assert second_particle.pz == pytest.approx(3.1406432734e00)
    assert second_particle.e == pytest.approx(3.1508676134e00)
    assert second_particle.m == pytest.approx(1.3800000000e-01)

    # Third particle: -211 (pi-)
    third_particle = target_event.particles[2]
    assert third_particle.id == pytest.approx(-211.0)  # pi-
    assert third_particle.status == pytest.approx(0.0)
    assert third_particle.px == pytest.approx(3.9695103971e-02)
    assert third_particle.py == pytest.approx(-2.2872518121e-01)
    assert third_particle.pz == pytest.approx(1.0496526207e-01)
    assert third_particle.e == pytest.approx(2.8974577830e-01)
    assert third_particle.m == pytest.approx(1.3800000000e-01)

    # Fourth particle: 2212 (proton)
    fourth_particle = target_event.particles[3]
    assert fourth_particle.id == pytest.approx(2212.0)  # proton
    assert fourth_particle.status == pytest.approx(0.0)
    assert fourth_particle.px == pytest.approx(-8.6160811751e-01)
    assert fourth_particle.py == pytest.approx(-7.3819273849e-01)
    assert fourth_particle.pz == pytest.approx(7.4246467306e00)
    assert fourth_particle.e == pytest.approx(7.5762050386e00)
    assert fourth_particle.m == pytest.approx(9.9307937557e-01)

    # Fifth particle: 211 (pi+)
    fifth_particle = target_event.particles[4]
    assert fifth_particle.id == pytest.approx(211.0)  # pi+
    assert fifth_particle.status == pytest.approx(0.0)
    assert fifth_particle.px == pytest.approx(-4.7889071830e-01)
    assert fifth_particle.py == pytest.approx(-2.8340027352e-01)
    assert fifth_particle.pz == pytest.approx(1.5195379346e00)
    assert fifth_particle.e == pytest.approx(1.6240971553e00)
    assert fifth_particle.m == pytest.approx(1.3800000000e-01)

    # Test that all particles have proper parent-child relationships
    for particle in target_event.particles:
        assert hasattr(particle, "event")
        assert particle.event is target_event
