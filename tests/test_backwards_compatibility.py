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


def test_mothers_backwards_compatibility():
    lhefile = _single_event_lhefile()
    event = lhefile.events[0]
    assert len(event.particles) > 3
    assert len(event.mothers(event.particles[3])) == 2
    assert event.particles[3].mothers() == event.mothers(event.particles[3])


def test_mothers_backwards_compatibility_requires_parent_event():
    particle = pylhe.LHEParticle(
        id=1,
        status=1,
        mother1=1,
        mother2=2,
        color1=501,
        color2=0,
        px=0.0,
        py=0.0,
        pz=1.0,
        e=1.0,
        m=0.0,
        lifetime=0.0,
        spin=9.0,
    )

    with (
        pytest.warns(
            DeprecationWarning,
            match=r"Access by `LHEParticle\.mothers\(\)` is deprecated",
        ),
        pytest.raises(ValueError, match=r"Particle is not associated to an event\."),
    ):
        particle.mothers()
