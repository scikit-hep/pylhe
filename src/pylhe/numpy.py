"""
`NumPy <https://numpy.org/>`_ interface for `pylhe`.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator

import numpy as np

import pylhe

__all__ = ["EVENT_DTYPE", "PARTICLE_DTYPE", "from_numpy", "to_numpy"]


def __dir__() -> list[str]:
    return __all__


EVENT_DTYPE = np.dtype(
    [
        ("start", np.int64),
        ("nparticles", np.int32),
        ("pid", np.int32),
        ("weight", np.float64),
        ("scale", np.float64),
        ("aqed", np.float64),
        ("aqcd", np.float64),
    ]
)
"""Row layout of the ``"events"`` array: one row per event, where ``start`` and
``nparticles`` point into the flat ``"particles"`` array (the same convention
the LHEH5 format uses)."""

PARTICLE_DTYPE = np.dtype(
    [
        ("id", np.int32),
        ("status", np.int32),
        ("mother1", np.int32),
        ("mother2", np.int32),
        ("color1", np.int32),
        ("color2", np.int32),
        ("px", np.float64),
        ("py", np.float64),
        ("pz", np.float64),
        ("e", np.float64),
        ("m", np.float64),
        ("lifetime", np.float64),
        ("spin", np.float64),
    ]
)
"""Row layout of the ``"particles"`` array: one row per particle."""


def to_numpy(
    event_iterable: Iterable[pylhe.LHEEvent] | pylhe.LHEFile,
) -> dict[str, np.ndarray]:
    """Convert an iterable of LHEEvent instances to structured NumPy arrays.

    Events with a variable number of particles are stored as two flat
    rectilinear tables, following the same convention as the LHEH5 format: an
    ``"events"`` array with one row per event, whose ``start`` and
    ``nparticles`` columns index into a ``"particles"`` array with one row per
    particle.

    Note:
        Named event weights, scales, attributes and optional comments have no
        fixed-width columns and are therefore not stored; use
        :func:`pylhe.to_awkward` if you need them.

    Args:
        event_iterable (iterable): An iterable of LHEEvent instances or LHEFile.

    Returns:
        dict: ``{"events": ..., "particles": ...}`` structured arrays.
    """
    if isinstance(event_iterable, pylhe.LHEFile):
        event_iterable = event_iterable.events

    event_rows = []
    particle_rows: list[tuple] = []
    for event in event_iterable:
        ei = event.eventinfo
        event_rows.append(
            (
                len(particle_rows),
                len(event.particles),
                ei.pid,
                ei.weight,
                ei.scale,
                ei.aqed,
                ei.aqcd,
            )
        )
        particle_rows.extend(
            (
                p.id,
                p.status,
                p.mother1,
                p.mother2,
                p.color1,
                p.color2,
                p.px,
                p.py,
                p.pz,
                p.e,
                p.m,
                p.lifetime,
                p.spin,
            )
            for p in event.particles
        )

    return {
        "events": np.array(event_rows, dtype=EVENT_DTYPE),
        "particles": np.array(particle_rows, dtype=PARTICLE_DTYPE),
    }


def from_numpy(data: dict[str, np.ndarray]) -> Iterator[pylhe.LHEEvent]:
    """Rebuild LHEEvent instances from arrays produced by :func:`to_numpy`.

    Args:
        data (dict): ``{"events": ..., "particles": ...}`` structured arrays,
            as returned by :func:`to_numpy`.

    Yields:
        pylhe.LHEEvent: The reconstructed events.
    """
    events = data["events"]
    particles = data["particles"]
    for row in events:
        start = int(row["start"])
        nparticles = int(row["nparticles"])
        yield pylhe.LHEEvent(
            eventinfo=pylhe.LHEEventInfo(
                nparticles=nparticles,
                pid=int(row["pid"]),
                weight=float(row["weight"]),
                scale=float(row["scale"]),
                aqed=float(row["aqed"]),
                aqcd=float(row["aqcd"]),
            ),
            particles=[
                pylhe.LHEParticle(
                    id=int(p["id"]),
                    status=int(p["status"]),
                    mother1=int(p["mother1"]),
                    mother2=int(p["mother2"]),
                    color1=int(p["color1"]),
                    color2=int(p["color2"]),
                    px=float(p["px"]),
                    py=float(p["py"]),
                    pz=float(p["pz"]),
                    e=float(p["e"]),
                    m=float(p["m"]),
                    lifetime=float(p["lifetime"]),
                    spin=float(p["spin"]),
                )
                for p in particles[start : start + nparticles]
            ],
        )
