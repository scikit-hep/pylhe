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
    for field in arr.weights.fields:
        assert len(arr) == len(arr.weights[field])


def test_awkward_registration():
    arr = pylhe.to_awkward(pylhe.read_lhe_with_attributes(TEST_FILE_WITHOUT_WEIGHTS))
    assert len(arr.particles.vector.mass) == len(arr.particles)

    arr = pylhe.to_awkward(pylhe.read_lhe_with_attributes(TEST_FILE_WITH_WEIGHTS))
    assert len(arr.particles.vector.mass) == len(arr.particles)
    assert len(arr.particles.vector.mass) == len(arr.weights)
