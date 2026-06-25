from __future__ import annotations

from copy import deepcopy

import h5py
import pytest
import skhep_testdata

import pylhe


def _decode_attr_values(values: object) -> tuple[str, ...]:
    return tuple(
        value.decode() if isinstance(value, bytes) else str(value) for value in values
    )


def _column_names(dataset: h5py.Dataset) -> tuple[str, ...]:
    dataset_name = dataset.name.rsplit("/", maxsplit=1)[-1]

    for attr_name in ("properties", dataset_name):
        if attr_name in dataset.attrs:
            return _decode_attr_values(dataset.attrs[attr_name])

    return ()


def _assert_hdf5_core_equal(
    source_path, roundtrip_path, *, compare_version: bool = True
) -> None:
    with (
        h5py.File(source_path, "r") as source,
        h5py.File(roundtrip_path, "r") as result,
    ):
        assert set(source.keys()) == set(result.keys())

        for dataset_name in source:
            source_dataset = source[dataset_name]
            result_dataset = result[dataset_name]

            assert source_dataset.shape == result_dataset.shape
            if dataset_name != "version" or compare_version:
                assert source_dataset[()].tolist() == result_dataset[()].tolist()

            if isinstance(source_dataset, h5py.Dataset) and dataset_name != "version":
                assert _column_names(source_dataset) == _column_names(result_dataset)


def _copy_hdf5_with_version(source_path, target_path, version) -> None:
    with (
        h5py.File(source_path, "r") as source,
        h5py.File(target_path, "w") as target,
    ):
        for dataset_name in source:
            source.copy(dataset_name, target)

        del target["version"]
        target.create_dataset("version", data=version, dtype="i8")


def _make_lhe() -> pylhe.LesHouchesEvents:
    return pylhe.LesHouchesEvents(
        init=pylhe.LHEInit(
            initInfo=pylhe.LHEInitInfo(
                beamA=11,
                beamB=-11,
                energyA=100.0,
                energyB=100.0,
                PDFgroupA=0,
                PDFgroupB=0,
                PDFsetA=0,
                PDFsetB=0,
                weightingStrategy=1,
                numProcesses=1,
            ),
            procInfo=[
                pylhe.LHEProcInfo(
                    xSection=1.5,
                    error=0.1,
                    unitWeight=1.0,
                    procId=7,
                    npLO=2,
                    npNLO=1,
                )
            ],
            generators=[],
        ),
        events=[
            pylhe.LHEEvent(
                eventinfo=pylhe.LHEEventInfo(
                    nparticles=2,
                    pid=7,
                    weight=2.5,
                    scale=91.2,
                    aqed=0.01,
                    aqcd=0.11,
                ),
                particles=[
                    pylhe.LHEParticle(
                        11,
                        -1,
                        0,
                        0,
                        0,
                        0,
                        0.0,
                        0.0,
                        50.0,
                        50.0,
                        0.0,
                        0.0,
                        9.0,
                    ),
                    pylhe.LHEParticle(
                        -11,
                        -1,
                        0,
                        0,
                        0,
                        0,
                        0.0,
                        0.0,
                        -50.0,
                        50.0,
                        0.0,
                        0.0,
                        9.0,
                    ),
                ],
                scales={"fscale": 88.0, "rscale": 94.0},
                attributes={"trials": "12.0"},
            ),
            pylhe.LHEEvent(
                eventinfo=pylhe.LHEEventInfo(
                    nparticles=3,
                    pid=8,
                    weight=3.5,
                    scale=125.0,
                    aqed=0.02,
                    aqcd=0.12,
                ),
                particles=[
                    pylhe.LHEParticle(
                        22,
                        2,
                        1,
                        2,
                        0,
                        0,
                        0.0,
                        0.0,
                        0.0,
                        125.0,
                        125.0,
                        0.0,
                        0.0,
                    ),
                    pylhe.LHEParticle(
                        13,
                        1,
                        3,
                        3,
                        0,
                        0,
                        10.0,
                        0.0,
                        40.0,
                        41.231056,
                        0.105,
                        0.0,
                        -1.0,
                    ),
                    pylhe.LHEParticle(
                        -13,
                        1,
                        3,
                        3,
                        0,
                        0,
                        -10.0,
                        0.0,
                        -40.0,
                        41.231056,
                        0.105,
                        0.0,
                        1.0,
                    ),
                ],
                scales={"fscale": 120.0, "rscale": 130.0},
                attributes={"trials": "3.5"},
            ),
        ],
    )


def test_lheh5_write_roundtrip(tmp_path):
    lhe = _make_lhe()
    path = tmp_path / "roundtrip.hdf5"

    lhe.tofile(path)

    with h5py.File(path, "r") as h5:
        assert set(h5.keys()) == {"events", "init", "particles", "procInfo", "version"}
        assert tuple(h5["version"][()]) == (2, 0, 0)
        assert tuple(h5["events"].attrs["properties"]) == (
            "pid",
            "nparticles",
            "start",
            "trials",
            "scale",
            "fscale",
            "rscale",
            "aqed",
            "aqcd",
            "NOMINAL",
        )

    loaded = pylhe.LesHouchesEvents.fromfile(path, generator=False)
    loaded_lazy = pylhe.LesHouchesEvents.fromfile(path)

    assert loaded.init == lhe.init
    assert list(loaded.events) == list(lhe.events)
    assert list(loaded_lazy.events) == list(lhe.events)


def test_lheh5_hpcgen_roundtrip(tmp_path):
    fixture_path = skhep_testdata.data_path("pylhe-testfile-hpcgen.hdf5")
    source_path = tmp_path / "hpcgen-v1.hdf5"
    roundtrip_path = tmp_path / "hpcgen-roundtrip.hdf5"

    _copy_hdf5_with_version(fixture_path, source_path, version=(1, 0, 0))

    loaded = pylhe.LesHouchesEvents.fromfile(source_path, generator=False)
    loaded.tofile(roundtrip_path)

    _assert_hdf5_core_equal(source_path, roundtrip_path, compare_version=False)

    with h5py.File(roundtrip_path, "r") as h5:
        assert tuple(h5["version"][()]) == (2, 0, 0)


def test_lheh5_write_streams_generator_across_multiple_flushes(tmp_path):
    total_events = pylhe.lheh5._EVENT_CHUNK_ROWS + 5
    template = _make_lhe()
    template_events = list(template.events)
    yielded = 0

    def event_iter():
        nonlocal yielded

        for index in range(total_events):
            event = deepcopy(template_events[index % len(template_events)])
            event.eventinfo.pid = 1000 + index
            event.attributes["trials"] = str(float(index))
            yielded += 1
            yield event

    streamed = pylhe.LesHouchesEvents(init=template.init, events=event_iter())
    path = tmp_path / "streamed.hdf5"

    streamed.tofile(path, lheformat=pylhe.HDF5_GZ_FORMAT)

    assert yielded == total_events

    with h5py.File(path, "r") as h5:
        assert h5["events"].shape == (total_events, len(pylhe.lheh5._EVENT_COLUMNS))
        assert h5["particles"].shape == (
            sum(event.eventinfo.nparticles for event in template_events)
            * (total_events // len(template_events))
            + sum(
                template_events[index].eventinfo.nparticles
                for index in range(total_events % len(template_events))
            ),
            len(pylhe.lheh5._PARTICLE_COLUMNS),
        )

    loaded = pylhe.LesHouchesEvents.fromfile(path, generator=False)
    loaded_events = list(loaded.events)

    assert len(loaded_events) == total_events
    assert loaded_events[0].eventinfo.pid == 1000
    assert loaded_events[-1].eventinfo.pid == 1000 + total_events - 1


def test_lheh5_write_rejects_inconsistent_particle_count(tmp_path):
    path = tmp_path / "invalid.hdf5"
    lhe = pylhe.LesHouchesEvents(
        init=pylhe.LHEInit(
            initInfo=pylhe.LHEInitInfo(11, -11, 100.0, 100.0, 0, 0, 0, 0, 1, 1),
            procInfo=[
                pylhe.LHEProcInfo(xSection=1.0, error=0.1, unitWeight=1.0, procId=1)
            ],
            generators=[],
        ),
        events=[
            pylhe.LHEEvent(
                eventinfo=pylhe.LHEEventInfo(
                    nparticles=1,
                    pid=1,
                    weight=1.0,
                    scale=1.0,
                    aqed=0.0,
                    aqcd=0.0,
                ),
                particles=[
                    pylhe.LHEParticle(
                        11,
                        -1,
                        0,
                        0,
                        0,
                        0,
                        0.0,
                        0.0,
                        1.0,
                        1.0,
                        0.0,
                        0.0,
                        1.0,
                    ),
                    pylhe.LHEParticle(
                        -11,
                        -1,
                        0,
                        0,
                        0,
                        0,
                        0.0,
                        0.0,
                        -1.0,
                        1.0,
                        0.0,
                        0.0,
                        -1.0,
                    ),
                ],
            )
        ],
    )

    with (
        h5py.File(path, "w") as h5,
        pytest.raises(ValueError, match=r"eventinfo.nparticles does not match"),
    ):
        pylhe.lheh5.write(lhe, h5, lheformat=pylhe.HDF5_FORMAT)
