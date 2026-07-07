from __future__ import annotations

from copy import deepcopy

import pylhe


def _make_repetitive_lhe(num_events: int = 256) -> pylhe.LesHouchesEvents:
    template_event = pylhe.LHEEvent(
        eventinfo=pylhe.LHEEventInfo(
            nparticles=3,
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
                501,
                0,
                0.0,
                0.0,
                50.0,
                50.0,
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
                501,
                0.0,
                0.0,
                -50.0,
                50.0,
                0.0,
                0.0,
                -1.0,
            ),
            pylhe.LHEParticle(
                22,
                1,
                1,
                2,
                0,
                0,
                0.0,
                0.0,
                0.0,
                100.0,
                100.0,
                0.0,
                0.0,
            ),
        ],
        scales={"fscale": 88.0, "rscale": 94.0},
        attributes={"trials": "12.0"},
    )

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
        events=[deepcopy(template_event) for _ in range(num_events)],
    )


def test_xml_gzip_output_is_smaller_than_plain(tmp_path):
    lhe = _make_repetitive_lhe()
    plain_path = tmp_path / "events.lhe"
    gzip_path = tmp_path / "events.lhe.gz"

    lhe.tofile(plain_path)
    lhe.tofile(gzip_path, lheformat=pylhe.GZ_FORMAT)

    assert gzip_path.stat().st_size < plain_path.stat().st_size


def test_hdf5_compressed_output_is_smaller_than_uncompressed(tmp_path):
    lhe = _make_repetitive_lhe()
    plain_path = tmp_path / "events-uncompressed.hdf5"
    compressed_path = tmp_path / "events-compressed.hdf5"

    lhe.tofile(plain_path, lheformat=pylhe.HDF5_FORMAT)
    lhe.tofile(compressed_path, lheformat=pylhe.HDF5_GZ_FORMAT)

    assert compressed_path.stat().st_size < plain_path.stat().st_size
