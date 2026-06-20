from __future__ import annotations

import h5py
import pytest

import pylhe


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
            ),
        ],
    )


def test_lheh5_write_roundtrip(tmp_path):
    lhe = _make_lhe()
    path = tmp_path / "roundtrip.hdf5"

    lhe.tofile(path)

    with h5py.File(path, "r") as h5:
        assert set(h5.keys()) == {"events", "init", "particles", "procInfo", "version"}
        assert tuple(h5["version"][()]) == (1, 0, 0)
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
        pylhe.lheh5.write(lhe, h5)
