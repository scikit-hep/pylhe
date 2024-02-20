import pytest
import skhep_testdata

from pylhe import (
    LHEEventInfo,
    LHEFile,
    LHEInit,
    LHEInitInfo,
    LHEParticle,
    LHEProcInfo,
    read_lhe,
)

TEST_FILE = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")


def test_LHEEvent():
    events = read_lhe(TEST_FILE)
    event = next(events)  # it contains 8 pions and a proton

    assert event.eventinfo is not None

    assert len(event.particles) == 9

    for p in event.particles:
        assert p.event == event

    assert event._graph is None


def test_LHEEventInfo_no_default_init():
    with pytest.raises(RuntimeError):
        _ = LHEEventInfo()


def test_LHEEventInfo_fromstring():
    """
    Data taken from the first <event> block of scikit-hep-testdata's package
    "pylhe-testlhef3.lhe" file.
    """
    data = "5 66 0.50109093E+02 0.14137688E+03 0.75563862E-02 0.12114027E+00"
    event_info = LHEEventInfo.fromstring(data)

    assert event_info.nparticles == 5
    assert event_info.pid == 66
    assert event_info.weight == pytest.approx(0.50109093e02)
    assert event_info.scale == pytest.approx(0.14137688e03)
    assert event_info.aqed == pytest.approx(0.75563862e-02)
    assert event_info.aqcd == pytest.approx(0.12114027e00)


def test_LHEFile_default_init():
    assert LHEFile() is not None


def test_LHEInit_default_init():
    assert LHEInit() is not None


def test_LHEInit_fromstring():
    """
    Data taken from the <init> block of scikit-hep-testdata's package
    "pylhe-testlhef3.lhe" file.
    """
    data = "2212 2212 0.40000000E+04 0.40000000E+04 -1 -1 21100 21100 -4 1"
    result = {
        "beamA": 2212.0,
        "beamB": 2212.0,
        "energyA": 4000.0,
        "energyB": 4000.0,
        "PDFgroupA": -1.0,
        "PDFgroupB": -1.0,
        "PDFsetA": 21100.0,
        "PDFsetB": 21100.0,
        "weightingStrategy": -4.0,
        "numProcesses": 1.0,
    }
    assert LHEInitInfo.fromstring(data) == result


def test_LHEParticle_no_default_init():
    with pytest.raises(RuntimeError):
        _ = LHEParticle()


def test_LHEParticle_fromstring():
    """
    Data taken from the first <event> block of scikit-hep-testdata's package
    "pylhe-testlhef3.lhe" file.
    """
    particles = [
        "        5 -1    0    0  501    0 0.00000000E+00 0.00000000E+00 0.14322906E+03 0.14330946E+03 0.48000000E+01 0.0000E+00 0.0000E+00",
        "        2 -1    0    0  502    0 0.00000000E+00 0.00000000E+00 -.93544317E+03 0.93544323E+03 0.33000000E+00 0.0000E+00 0.0000E+00",
        "       24  1    1    2    0    0 -.84258804E+02 -.15708566E+03 -.10629600E+03 0.22257162E+03 0.80398000E+02 0.0000E+00 0.0000E+00",
        "        5  1    1    2  501    0 -.13668073E+03 -.36307424E+02 -.40614473E+02 0.14721558E+03 0.48000000E+01 0.0000E+00 0.0000E+00",
        "        1  1    1    2  502    0 0.22093954E+03 0.19339308E+03 -.64530364E+03 0.70896548E+03 0.33000000E+00 0.0000E+00 0.0000E+00",
    ]

    particle_objs = [LHEParticle.fromstring(p) for p in particles]

    assert [p.id for p in particle_objs] == [5, 2, 24, 5, 1]
    assert [p.status for p in particle_objs] == [-1.0, -1.0, 1.0, 1.0, 1.0]
    assert [p.mother1 for p in particle_objs] == [0.0, 0.0, 1.0, 1.0, 1.0]
    assert [p.mother2 for p in particle_objs] == [0.0, 0.0, 2.0, 2.0, 2.0]
    assert [p.color1 for p in particle_objs] == [501.0, 502.0, 0.0, 501.0, 502.0]
    assert [p.color2 for p in particle_objs] == [0.0, 0.0, 0.0, 0.0, 0.0]
    assert [p.px for p in particle_objs] == [
        0.0,
        0.0,
        -84.258804,
        -136.68073,
        220.93954,
    ]
    assert [p.py for p in particle_objs] == [
        0.0,
        0.0,
        -157.08566,
        -36.307424,
        193.39308,
    ]
    assert [p.pz for p in particle_objs] == [
        143.22906,
        -935.44317,
        -106.296,
        -40.614473,
        -645.30364,
    ]
    assert [p.e for p in particle_objs] == [
        143.30946,
        935.44323,
        222.57162,
        147.21558,
        708.96548,
    ]
    assert [p.m for p in particle_objs] == [4.8, 0.33, 80.398, 4.8, 0.33]
    assert [p.lifetime for p in particle_objs] == [0.0, 0.0, 0.0, 0.0, 0.0]
    assert [p.spin for p in particle_objs] == [0.0, 0.0, 0.0, 0.0, 0.0]


def test_LHEProcInfo_default_init():
    assert LHEProcInfo() is not None


def test_LHEProcInfo_fromstring():
    """
    Data taken from the <init> block of scikit-hep-testdata's package
    "pylhe-testlhef3.lhe" file.
    """
    data = "0.50109086E+02 0.89185414E-01 0.50109093E+02 66"
    result = {
        "xSection": 50.109086,
        "error": 0.089185414,
        "unitWeight": 50.109093,
        "procId": 66.0,
    }
    assert LHEProcInfo.fromstring(data) == result
