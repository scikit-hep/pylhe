"""
Benchmark tests for pylhe write performance.
"""

from __future__ import annotations

import math
import os
import random
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pylhe

NUM_EVENTS = int(os.environ.get("PYLHE_BENCH_NUM_EVENTS", "100000"))
RNG_SEED = 1337
WEIGHT_IDS = ("1001", "1002", "1003", "1004", "1005", "1006")


def _build_init() -> pylhe.LHEInit:
    return pylhe.LHEInit(
        initInfo=pylhe.LHEInitInfo(
            beamA=2212,
            beamB=2212,
            energyA=6500.0,
            energyB=6500.0,
            PDFgroupA=0,
            PDFgroupB=0,
            PDFsetA=0,
            PDFsetB=0,
            weightingStrategy=3,
            numProcesses=1,
        ),
        procInfo=[
            pylhe.LHEProcInfo(
                xSection=1.0,
                error=0.0,
                unitWeight=1.0,
                procId=1,
            )
        ],
        generators=[],
    )


def _build_header() -> pylhe.LHEHeader:
    return pylhe.LHEHeader(
        initrwgt=pylhe.LHEInitRWGT(
            entries=[
                pylhe.LHEInitRWGTWeightGroup(
                    name="scale_variation",
                    combine="envelope",
                    weights=[
                        pylhe.LHEInitRWGTWeight(
                            id=weight_id,
                            name=f"variation_{index}",
                        )
                        for index, weight_id in enumerate(WEIGHT_IDS)
                    ],
                )
            ]
        )
    )


def _build_particle(
    particle_id: int,
    status: int,
    mother1: int,
    mother2: int,
    color1: int,
    color2: int,
    px: float,
    py: float,
    pz: float,
    mass: float,
    spin: float,
) -> pylhe.LHEParticle:
    energy = math.sqrt(px * px + py * py + pz * pz + mass * mass)
    return pylhe.LHEParticle(
        id=particle_id,
        status=status,
        mother1=mother1,
        mother2=mother2,
        color1=color1,
        color2=color2,
        px=px,
        py=py,
        pz=pz,
        e=energy,
        m=mass,
        lifetime=0.0,
        spin=spin,
    )


def _random_event(rng: random.Random) -> pylhe.LHEEvent:
    base_weight = rng.uniform(0.1, 10.0)
    scale = rng.uniform(50.0, 5000.0)
    px = rng.uniform(-750.0, 750.0)
    py = rng.uniform(-750.0, 750.0)
    pz = rng.uniform(-3000.0, 3000.0)
    mass_a = rng.uniform(0.0, 50.0)
    mass_b = rng.uniform(0.0, 50.0)

    weights = {
        weight_id: base_weight * rng.uniform(0.8, 1.2) for weight_id in WEIGHT_IDS
    }
    particles = [
        _build_particle(
            particle_id=21,
            status=-1,
            mother1=0,
            mother2=0,
            color1=501,
            color2=0,
            px=0.0,
            py=0.0,
            pz=6500.0,
            mass=0.0,
            spin=0.0,
        ),
        _build_particle(
            particle_id=21,
            status=-1,
            mother1=0,
            mother2=0,
            color1=0,
            color2=502,
            px=0.0,
            py=0.0,
            pz=-6500.0,
            mass=0.0,
            spin=0.0,
        ),
        _build_particle(
            particle_id=1,
            status=1,
            mother1=1,
            mother2=2,
            color1=501,
            color2=0,
            px=px,
            py=py,
            pz=pz,
            mass=mass_a,
            spin=9.0,
        ),
        _build_particle(
            particle_id=-1,
            status=1,
            mother1=1,
            mother2=2,
            color1=0,
            color2=502,
            px=-px,
            py=-py,
            pz=-pz,
            mass=mass_b,
            spin=-9.0,
        ),
    ]

    return pylhe.LHEEvent(
        eventinfo=pylhe.LHEEventInfo(
            nparticles=len(particles),
            pid=1,
            weight=base_weight,
            scale=scale,
            aqed=7.2973525693e-3,
            aqcd=1.18e-1,
        ),
        particles=particles,
        weights=weights,
    )


def _random_events(num_events: int, seed: int) -> Iterator[pylhe.LHEEvent]:
    rng = random.Random(seed)
    for _ in range(num_events):
        yield _random_event(rng)


def _write_random_events_to_temporary_gzip(num_events: int) -> int:
    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "random-events.lhe.gz"
        pylhe.LHEFile(
            init=_build_init(),
            header=_build_header(),
            events=_random_events(num_events=num_events, seed=RNG_SEED),
            version="3.0",
        ).tofile(
            str(output_path),
            pylhe.LHEFormat(
                file=pylhe.LHEFileFormat.GZIP, weights=pylhe.LHEWeightFormat.RWGT
            ),
        )
        return output_path.stat().st_size


def test_write_random_events_gzip_benchmark(benchmark) -> None:
    """Benchmark writing NUM_EVENTS random weighted events to a temporary gzip file.

    NUM_EVENTS is configurable via the PYLHE_BENCH_NUM_EVENTS environment variable.
    """

    benchmark.extra_info["num_events"] = NUM_EVENTS
    benchmark.extra_info["num_weights"] = len(WEIGHT_IDS)

    result = benchmark(_write_random_events_to_temporary_gzip, NUM_EVENTS)

    assert result > 0
