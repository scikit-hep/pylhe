import skhep_testdata

import pylhe

TEST_FILE = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")


def test_to_awkward():
    arr = pylhe.to_awkward(pylhe.read_lhe_with_attributes(TEST_FILE))
    assert len(arr) == 791
    assert len(arr.eventinfo.nparticles) == len(arr.particles)


def test_awkward_registration():
    arr = pylhe.to_awkward(pylhe.read_lhe_with_attributes(TEST_FILE))
    assert len(arr.particles.vector.mass) == len(arr.particles)
