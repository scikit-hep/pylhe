import numpy as np
import pytest
import skhep_testdata

import pylhe
from pylhe.numpy import EVENT_DTYPE, PARTICLE_DTYPE

TEST_FILE_WITHOUT_WEIGHTS = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
TEST_FILE_WITH_WEIGHTS = skhep_testdata.data_path("pylhe-testlhef3.lhe")


def test_to_numpy():
    data = pylhe.to_numpy(pylhe.LesHouchesEvents.fromfile(TEST_FILE_WITHOUT_WEIGHTS))
    events, particles = data["events"], data["particles"]

    assert events.dtype == EVENT_DTYPE
    assert particles.dtype == PARTICLE_DTYPE
    assert len(events) == 791
    assert len(particles) == events["nparticles"].sum()

    # start/nparticles must tile the particles array contiguously
    assert events["start"][0] == 0
    assert np.array_equal(
        events["start"][1:], events["start"][:-1] + events["nparticles"][:-1]
    )
    assert events["start"][-1] + events["nparticles"][-1] == len(particles)

    # same anchor values as the awkward interface tests
    first = particles[events["start"][0]]
    assert first["px"] == pytest.approx(-3.1463804033e-01)
    assert first["py"] == pytest.approx(-6.3041724109e-01)
    assert first["pz"] == pytest.approx(8.5343193374e00)
    assert first["e"] == pytest.approx(8.5644657479e00)


def test_to_numpy_weights_dropped():
    # named weights have no fixed-width column; conversion works, weights are dropped
    data = pylhe.to_numpy(pylhe.LesHouchesEvents.fromfile(TEST_FILE_WITH_WEIGHTS))
    assert len(data["events"]) == 59
    assert data["events"].dtype.names == EVENT_DTYPE.names


def test_roundtrip():
    original = list(pylhe.LesHouchesEvents.fromfile(TEST_FILE_WITHOUT_WEIGHTS).events)
    back = list(pylhe.from_numpy(pylhe.to_numpy(original)))

    assert len(back) == len(original)
    for orig_event, new_event in zip(original, back, strict=True):
        assert new_event.eventinfo == orig_event.eventinfo
        assert new_event.particles == orig_event.particles


def test_empty():
    data = pylhe.to_numpy([])
    assert data["events"].shape == (0,)
    assert data["particles"].shape == (0,)
    assert data["events"].dtype == EVENT_DTYPE
    assert data["particles"].dtype == PARTICLE_DTYPE
    assert list(pylhe.from_numpy(data)) == []
