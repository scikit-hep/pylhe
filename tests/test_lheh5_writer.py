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


def _make_weighted_lhe() -> pylhe.LesHouchesEvents:
    lhe = _make_lhe()
    lhe.header = pylhe.LHEHeader(
        initrwgt=pylhe.LHEInitRWGT(
            entries=[
                pylhe.LHEInitRWGTWeightGroup(
                    name="scale_variation",
                    combine="envelope",
                    weights=[
                        pylhe.LHEInitRWGTWeight(
                            id="1001",
                            name="muR=0.5 muF=0.5",
                        ),
                        pylhe.LHEInitRWGTWeight(
                            id="1002",
                            name="muR=1.0 muF=1.0",
                        ),
                    ],
                ),
                pylhe.LHEInitRWGTWeight(
                    id="pdf1",
                    name="PDF member 1",
                ),
            ]
        )
    )

    events = list(lhe.events)
    events[0].weights = {"1001": 2.25, "1002": 2.5, "pdf1": 2.75}
    events[1].weights = {"1001": 3.25, "1002": 3.5, "pdf1": 3.75}

    return lhe


def test_lheh5_write_roundtrip(tmp_path):
    lhe = _make_lhe()
    path = tmp_path / "roundtrip.hdf5"

    lhe.tofile(path)

    with h5py.File(path, "r") as h5:
        assert set(h5.keys()) == {"events", "init", "particles", "procInfo", "version"}
        assert tuple(h5["version"][()]) == (2, 0, 0)
        assert h5["events"].compression is None
        assert h5["particles"].compression is None
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


def test_lheh5_write_roundtrip_preserves_declared_weights(tmp_path):
    lhe = _make_weighted_lhe()
    source_events = list(lhe.events)
    weight_ids = lhe.header.initrwgt.list_weights_ids()
    path = tmp_path / "weighted-roundtrip.hdf5"

    lhe.tofile(path, lheformat=pylhe.HDF5_FORMAT)

    expected_event_columns = (*pylhe.lheh5._EVENT_COLUMNS, *weight_ids)

    with h5py.File(path, "r") as h5:
        assert _column_names(h5["events"]) == expected_event_columns
        assert h5["events"].shape == (len(source_events), len(expected_event_columns))

        event_column_indices = {
            name: index for index, name in enumerate(_column_names(h5["events"]))
        }
        for event_row, source_event in zip(h5["events"], source_events, strict=True):
            for weight_id in weight_ids:
                assert event_row[event_column_indices[weight_id]] == pytest.approx(
                    source_event.weights[weight_id]
                )

    loaded = pylhe.LHEFile.fromfile(path, generator=False)
    loaded_events = list(loaded.events)

    assert loaded.header is not None
    assert [weight.id for weight in loaded.header.initrwgt.iter_weights()] == weight_ids
    assert loaded.init == lhe.init
    assert len(loaded_events) == len(source_events)

    for source_event, loaded_event in zip(source_events, loaded_events, strict=True):
        assert loaded_event.eventinfo == source_event.eventinfo
        assert loaded_event.particles == source_event.particles
        assert loaded_event.weights == source_event.weights
        assert list(loaded_event.weights) == weight_ids
        assert loaded_event.scales == source_event.scales
        assert loaded_event.attributes == source_event.attributes
        assert loaded_event.optional == source_event.optional


def test_lheh5_write_rejects_weight_name_in_default_event_columns(tmp_path):
    lhe = _make_weighted_lhe()
    assert lhe.header is not None
    next(lhe.header.initrwgt.iter_weights()).id = "pid"
    path = tmp_path / "duplicate-weight-column.hdf5"

    with (
        h5py.File(path, "w") as h5,
        pytest.raises(
            ValueError,
            match=r"Weight name 'pid' is already present in default event columns\.",
        ),
    ):
        pylhe.lheh5.write(lhe, h5, lheformat=pylhe.HDF5_FORMAT)


def test_lhe_to_lheh5_roundtrip_preserves_weights(tmp_path):
    source = pylhe.LHEFile.fromfile(
        skhep_testdata.data_path("pylhe-testlhef3.lhe"),
        generator=False,
    )
    source_events = list(source.events)
    weight_ids = source.header.initrwgt.list_weights_ids()
    path = tmp_path / "xml-to-hdf5-roundtrip.hdf5"

    assert weight_ids
    assert all(event.weights for event in source_events)

    source.tofile(path, lheformat=pylhe.HDF5_FORMAT)

    with h5py.File(path, "r") as h5:
        assert _column_names(h5["events"]) == (
            *pylhe.lheh5._EVENT_COLUMNS,
            *weight_ids,
        )

    result = pylhe.LHEFile.fromfile(path, generator=False)
    result_events = list(result.events)

    assert result.header is not None
    assert result.header.initrwgt.list_weights_ids() == weight_ids
    assert source.init.initInfo == result.init.initInfo
    assert source.init.procInfo == result.init.procInfo
    assert len(source_events) == len(result_events)

    for source_event, result_event in zip(source_events, result_events, strict=True):
        assert source_event.eventinfo == result_event.eventinfo
        assert source_event.particles == result_event.particles
        assert source_event.weights == result_event.weights
        assert list(result_event.weights) == weight_ids


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
    lheformat = pylhe.LHEHDF5Format(
        compression="gzip",
        compression_opts=4,
        shuffle=True,
        event_chunk_rows=3,
        particle_chunk_rows=5,
    )
    total_events = lheformat.event_chunk_rows + 5
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

    streamed.tofile(path, lheformat=lheformat)

    assert yielded == total_events

    with h5py.File(path, "r") as h5:
        assert h5["events"].compression == "gzip"
        assert h5["particles"].compression == "gzip"
        assert h5["events"].shuffle
        assert h5["particles"].shuffle
        assert h5["events"].chunks == (
            lheformat.event_chunk_rows,
            len(pylhe.lheh5._EVENT_COLUMNS),
        )
        assert h5["particles"].chunks == (
            lheformat.particle_chunk_rows,
            len(pylhe.lheh5._PARTICLE_COLUMNS),
        )
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


def test_lheh5_write_rejects_inconsistent_num_processes(tmp_path):
    path = tmp_path / "invalid-procinfo.hdf5"
    lhe = pylhe.LesHouchesEvents(
        init=pylhe.LHEInit(
            initInfo=pylhe.LHEInitInfo(11, -11, 100.0, 100.0, 0, 0, 0, 0, 1, 2),
            procInfo=[
                pylhe.LHEProcInfo(xSection=1.0, error=0.1, unitWeight=1.0, procId=1)
            ],
            generators=[],
        ),
        events=[],
    )

    with (
        h5py.File(path, "w") as h5,
        pytest.raises(
            ValueError,
            match=r"initInfo.numProcesses does not match the number of procInfo rows",
        ),
    ):
        pylhe.lheh5.write(lhe, h5, lheformat=pylhe.HDF5_FORMAT)
