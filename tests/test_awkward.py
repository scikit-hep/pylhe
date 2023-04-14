import skhep_testdata

import pylhe

TEST_FILE = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")


def test_register_awkward():
    pylhe.register_awkward()


def test_to_awkward():
    arr = pylhe.to_awkward(pylhe.read_lhe_with_attributes(TEST_FILE))
    assert len(arr) == 791
    assert len(arr.eventinfo.nparticles) == len(arr.particles)
    # iss 194 pr 195 - make sure vector helper classes funciton properly
    #    here we make sure the 'mass' helper function on 4D vectors
    #    is called on each particle's momentum
    assert len(arr.particles.vector.mass) == len(arr.particles)
