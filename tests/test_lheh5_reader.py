from __future__ import annotations

from pathlib import Path

import h5py
import pytest

import pylhe
from pylhe.lheh5 import get_particles, iter_lheh5, read_init

TEST_HDF5 = Path(__file__).with_name("test.hdf5")
TEST_HDF5_J7 = Path(__file__).with_name("j7_1.hdf5")


def test_get_particles_returns_lheparticles():
    with h5py.File(TEST_HDF5, "r") as h5:
        particles = get_particles(h5["particles"], 0, 4)

    assert len(particles) == 4
    assert all(isinstance(particle, pylhe.LHEParticle) for particle in particles)

    assert particles[0].id == 1
    assert particles[0].status == -1
    assert particles[0].pz == pytest.approx(12.38393852)

    assert particles[2].id == 11
    assert particles[2].e == pytest.approx(55.07043451)


def test_iter_lheh5_reads_nominal_weight_and_particles():
    with h5py.File(TEST_HDF5_J7, "r") as h5:
        event_iter = iter_lheh5(h5)
        first_event = next(event_iter)
        second_event = next(event_iter)

    assert first_event.eventinfo.weight == pytest.approx(0.0)
    assert first_event.eventinfo.nparticles == 10

    assert second_event.eventinfo.pid == 1
    assert second_event.eventinfo.nparticles == 10
    assert second_event.eventinfo.weight == pytest.approx(58474.2496)
    assert len(second_event.particles) == 10
    assert second_event.particles[0].id == 21
    assert second_event.particles[2].id == 25
    assert second_event.particles[2].m == pytest.approx(125.0)


def test_read_init_matches_lheinit_specification():
    with h5py.File(TEST_HDF5, "r") as h5:
        init = read_init(h5)

    assert isinstance(init, pylhe.LHEInit)
    assert init.initInfo.beamA == 2212
    assert init.initInfo.beamB == 2212
    assert init.initInfo.energyA == pytest.approx(7000.0)
    assert init.initInfo.energyB == pytest.approx(7000.0)
    assert init.initInfo.PDFsetA == 13000
    assert init.initInfo.PDFsetB == 13000
    assert init.initInfo.weightingStrategy == 1
    assert init.initInfo.numProcesses == 1

    assert init.generators == []
    assert len(init.procInfo) == 1
    assert init.procInfo[0].procId == 1
    assert init.procInfo[0].xSection == pytest.approx(1661.5257101139289)
    assert init.procInfo[0].error == pytest.approx(6.367380198171124)
    assert init.procInfo[0].unitWeight == pytest.approx(2.330218119536726e-05)
