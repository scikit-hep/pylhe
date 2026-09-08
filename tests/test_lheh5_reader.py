from __future__ import annotations

import h5py
import pytest
import skhep_testdata

import pylhe
from pylhe.lheh5 import get_particles, read_header, read_init, read_iter_events


def test_get_particles_returns_lheparticles():
    with h5py.File(skhep_testdata.data_path("pylhe-testfile-hpcgen.hdf5"), "r") as h5:
        particles = get_particles(h5["particles"], 0, 4)

    assert len(particles) == 4
    assert all(isinstance(particle, pylhe.LHEParticle) for particle in particles)

    assert particles[0].id == 1
    assert particles[0].status == -1
    assert particles[0].pz == pytest.approx(12.38393852)

    assert particles[2].id == 11
    assert particles[2].e == pytest.approx(55.07043451)


def test_read_iter_events_reads_nominal_weight_and_particles():
    with h5py.File(skhep_testdata.data_path("pylhe-testfile-sherpa.hdf5"), "r") as h5:
        event_iter = read_iter_events(h5)
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


def test_count_events_matches_hdf5_events_dataset_length():
    path = skhep_testdata.data_path("pylhe-testfile-sherpa.hdf5")

    with h5py.File(path, "r") as h5:
        expected = len(h5["events"])

    assert pylhe.LesHouchesEvents.count_events(path) == expected
    assert pylhe.LHEFile.count_events(path) == expected
    assert pylhe.LHEFile.count_events(path) == sum(
        1 for _ in pylhe.LHEFile.fromfile(path).events
    )


def test_read_init_matches_lheinit_specification():
    with h5py.File(skhep_testdata.data_path("pylhe-testfile-hpcgen.hdf5"), "r") as h5:
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


def test_read_init_reads_generators_dataset(tmp_path):
    path = tmp_path / "generators.hdf5"

    with h5py.File(path, "w") as h5:
        h5.create_dataset(
            "init",
            data=[2212, 2212, 7000.0, 7000.0, 0, 0, 13000, 13000, 1, 1],
            dtype="f8",
        )
        h5["init"].attrs["generatorName"] = "fallback"
        h5["init"].attrs["generatorVersion"] = "0.0"
        h5["init"].attrs["generatorDescription"] = "fallback generator"
        h5.create_dataset(
            "procInfo",
            data=[[1, 2, 0, 1.5, 0.1, 1.0]],
            dtype="f8",
        )
        generators = h5.create_dataset(
            "generators",
            shape=(2, 4),
            dtype=h5py.string_dtype(encoding="utf-8"),
        )
        generators.attrs["properties"] = [
            b"name",
            b"version",
            b"description",
            b"extraAttributes",
        ]
        generators[...] = [
            ["Sherpa", "3.0.0", "first generator", "{}"],
            ["MadGraph", "2.9.20", "second generator", '{"custom": "yes"}'],
        ]

    with h5py.File(path, "r") as h5:
        init = read_init(h5)

    assert [generator.name for generator in init.generators] == ["Sherpa", "MadGraph"]
    assert [generator.version for generator in init.generators] == ["3.0.0", "2.9.20"]
    assert [generator.description for generator in init.generators] == [
        "first generator",
        "second generator",
    ]
    assert init.generators[0].extra_attributes == {}
    assert init.generators[1].extra_attributes == {"custom": "yes"}


def test_read_header_synthesizes_weights_without_xml_header(tmp_path):
    path = tmp_path / "weights-without-xml-header.hdf5"
    event_columns = (*pylhe.lheh5._EVENT_COLUMNS, "1001", "1002")

    with h5py.File(path, "w") as h5:
        events = h5.create_dataset("events", shape=(0, len(event_columns)), dtype="f8")
        events.attrs["properties"] = [name.encode() for name in event_columns]

    with h5py.File(path, "r") as h5:
        header = read_header(h5)

    assert header is not None
    assert header.initrwgt.list_weights_ids() == ["1001", "1002"]
    assert [weight.name for weight in header.initrwgt.iter_weights()] == [
        "1001",
        "1002",
    ]
