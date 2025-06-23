import pytest
import skhep_testdata

import pylhe

TEST_FILE_WITHOUT_WEIGHTS = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
TEST_FILE_WITH_WEIGHTS = skhep_testdata.data_path("pylhe-testlhef3.lhe")


def test_to_awkward():
    arr = pylhe.to_awkward(pylhe.read_lhe_with_attributes(TEST_FILE_WITHOUT_WEIGHTS))
    assert len(arr) == 791
    assert len(arr) == len(arr.particles)
    assert len(arr) == len(arr.eventinfo)
    for field in arr.particles.fields:
        assert len(arr) == len(arr.particles[field])
    for field in arr.eventinfo.fields:
        assert len(arr) == len(arr.eventinfo[field])
    assert "weights" not in arr.fields

    arr = pylhe.to_awkward(pylhe.read_lhe_with_attributes(TEST_FILE_WITH_WEIGHTS))
    assert len(arr) == 59
    assert len(arr) == len(arr.particles)
    assert len(arr) == len(arr.eventinfo)
    for field in arr.particles.fields:
        assert len(arr) == len(arr.particles[field])
    for field in arr.eventinfo.fields:
        assert len(arr) == len(arr.eventinfo[field])
    assert "weights" in arr.fields
    assert len(arr) == len(arr.weights)
    assert arr.weights.fields == [
        "1001",
        "1002",
        "1003",
        "1004",
        "1005",
        "1006",
        "1007",
        "1008",
        "1009",
    ]
    assert arr.weights["1001"][0] == pytest.approx(0.50109e02)
    assert arr.weights["1002"][0] == pytest.approx(0.45746e02)
    assert arr.weights["1003"][0] == pytest.approx(0.52581e02)
    assert arr.weights["1004"][0] == pytest.approx(0.50109e02)
    assert arr.weights["1005"][0] == pytest.approx(0.45746e02)
    assert arr.weights["1006"][0] == pytest.approx(0.52581e02)
    assert arr.weights["1007"][0] == pytest.approx(0.50109e02)
    assert arr.weights["1008"][0] == pytest.approx(0.45746e02)
    assert arr.weights["1009"][0] == pytest.approx(0.52581e02)
    for field in arr.weights.fields:
        assert len(arr) == len(arr.weights[field])


def test_awkward_registration():
    arr = pylhe.to_awkward(pylhe.read_lhe_with_attributes(TEST_FILE_WITHOUT_WEIGHTS))
    assert len(arr.particles.vector.mass) == len(arr.particles)

    arr = pylhe.to_awkward(pylhe.read_lhe_with_attributes(TEST_FILE_WITH_WEIGHTS))
    assert len(arr.particles.vector.mass) == len(arr.particles)
    assert len(arr.particles.vector.mass) == len(arr.weights)


def test_to_awkward_vector():
    """
    Test numeric equality of momenta represented by vectors.
    """
    arr = pylhe.to_awkward(pylhe.read_lhe_with_attributes(TEST_FILE_WITHOUT_WEIGHTS))

    assert arr.particles.vector.px[0][0] == pytest.approx(-3.1463804033e-01)
    assert arr.particles.vector.x[0][0] == pytest.approx(-3.1463804033e-01)

    assert arr.particles.vector.py[0][0] == pytest.approx(-6.3041724109e-01)
    assert arr.particles.vector.y[0][0] == pytest.approx(-6.3041724109e-01)

    assert arr.particles.vector.pz[0][0] == pytest.approx(8.5343193374e00)
    assert arr.particles.vector.z[0][0] == pytest.approx(8.5343193374e00)

    assert arr.particles.vector.e[0][0] == pytest.approx(8.5644657479e00)
    assert arr.particles.vector.t[0][0] == pytest.approx(8.5644657479e00)
