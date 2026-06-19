from __future__ import annotations

from collections.abc import Iterable, Iterator, Sequence

import h5py  # type: ignore[import-untyped]

import pylhe

_PARTICLE_COLUMNS = (
    "id",
    "status",
    "mother1",
    "mother2",
    "color1",
    "color2",
    "px",
    "py",
    "pz",
    "e",
    "m",
    "lifetime",
    "spin",
)

_INIT_COLUMNS = (
    "beamA",
    "beamB",
    "energyA",
    "energyB",
    "PDFgroupA",
    "PDFgroupB",
    "PDFsetA",
    "PDFsetB",
    "weightingStrategy",
    "numProcesses",
)

_PROCINFO_COLUMNS = (
    "procId",
    "npLO",
    "npNLO",
    "xSection",
    "error",
    "unitWeight",
)


def _decode_attr_values(values: Iterable[object]) -> list[str]:
    return [
        value.decode() if isinstance(value, bytes) else str(value) for value in values
    ]


def _column_names(dataset: h5py.Dataset, *, default: tuple[str, ...] = ()) -> list[str]:
    attr_names = ("properties", dataset.name.rsplit("/", maxsplit=1)[-1])

    for attr_name in attr_names:
        if attr_name in dataset.attrs:
            return _decode_attr_values(dataset.attrs[attr_name])

    return list(default)


def _column_indices(
    dataset: h5py.Dataset, *, default: tuple[str, ...] = ()
) -> dict[str, int]:
    return {
        name: index
        for index, name in enumerate(_column_names(dataset, default=default))
    }


def _row_int(row: Sequence[float], columns: dict[str, int], *names: str) -> int:
    for name in names:
        index = columns.get(name)
        if index is not None:
            return int(float(row[index]))

    err = f"None of the requested columns are available: {', '.join(names)}"
    raise KeyError(err)


def _row_float(
    row: Sequence[float],
    columns: dict[str, int],
    *names: str,
    default: float | None = None,
) -> float:
    for name in names:
        index = columns.get(name)
        if index is not None:
            return float(row[index])

    if default is not None:
        return default

    err = f"None of the requested columns are available: {', '.join(names)}"
    raise KeyError(err)


def _get_particles(
    particles: h5py.Dataset, start: int, n: int
) -> list[pylhe.LHEParticle]:
    particle_columns = _column_indices(particles, default=_PARTICLE_COLUMNS)

    return [
        pylhe.LHEParticle(
            id=_row_int(row, particle_columns, "id"),
            status=_row_int(row, particle_columns, "status"),
            mother1=_row_int(row, particle_columns, "mother1"),
            mother2=_row_int(row, particle_columns, "mother2"),
            color1=_row_int(row, particle_columns, "color1"),
            color2=_row_int(row, particle_columns, "color2"),
            px=_row_float(row, particle_columns, "px"),
            py=_row_float(row, particle_columns, "py"),
            pz=_row_float(row, particle_columns, "pz"),
            e=_row_float(row, particle_columns, "e"),
            m=_row_float(row, particle_columns, "m"),
            lifetime=_row_float(row, particle_columns, "lifetime"),
            spin=_row_float(row, particle_columns, "spin"),
        )
        for row in particles[start : start + n]
    ]


def get_particles(
    particles: h5py.Dataset, start: int, n: int
) -> list[pylhe.LHEParticle]:
    return _get_particles(particles, start, n)


def read_iter_events(file: h5py.File) -> Iterator[pylhe.LHEEvent]:
    with file as h5:
        events = h5["events"]
        particles = h5["particles"]
        event_columns = _column_indices(events)

        for event_row in events:
            start = _row_int(event_row, event_columns, "start")
            nparticles = _row_int(event_row, event_columns, "nparticles")

            yield pylhe.LHEEvent(
                eventinfo=pylhe.LHEEventInfo(
                    nparticles=nparticles,
                    pid=_row_int(event_row, event_columns, "pid"),
                    weight=_row_float(
                        event_row,
                        event_columns,
                        "weight",
                        "NOMINAL",
                        default=0.0,
                    ),
                    scale=_row_float(event_row, event_columns, "scale", default=0.0),
                    aqed=_row_float(event_row, event_columns, "aqed", default=0.0),
                    aqcd=_row_float(event_row, event_columns, "aqcd", default=0.0),
                ),
                particles=_get_particles(particles, start, nparticles),
            )


def iter_lheh5(file: h5py.File) -> Iterator[pylhe.LHEEvent]:
    yield from read_iter_events(file)


def read_init(file: h5py.File) -> pylhe.LHEInit:
    with file as h5:
        init = h5["init"]
        procinfo = h5["procInfo"]
        init_columns = _column_indices(init, default=_INIT_COLUMNS)
        procinfo_columns = _column_indices(procinfo, default=_PROCINFO_COLUMNS)
        init_row = init[()]

        return pylhe.LHEInit(
            initInfo=pylhe.LHEInitInfo(
                beamA=_row_int(init_row, init_columns, "beamA"),
                beamB=_row_int(init_row, init_columns, "beamB"),
                energyA=_row_float(init_row, init_columns, "energyA"),
                energyB=_row_float(init_row, init_columns, "energyB"),
                PDFgroupA=_row_int(init_row, init_columns, "PDFgroupA"),
                PDFgroupB=_row_int(init_row, init_columns, "PDFgroupB"),
                PDFsetA=_row_int(init_row, init_columns, "PDFsetA"),
                PDFsetB=_row_int(init_row, init_columns, "PDFsetB"),
                weightingStrategy=_row_int(init_row, init_columns, "weightingStrategy"),
                numProcesses=_row_int(init_row, init_columns, "numProcesses"),
            ),
            procInfo=[
                pylhe.LHEProcInfo(
                    xSection=_row_float(row, procinfo_columns, "xSection"),
                    error=_row_float(row, procinfo_columns, "error"),
                    unitWeight=_row_float(row, procinfo_columns, "unitWeight"),
                    procId=_row_int(row, procinfo_columns, "procId"),
                )
                for row in procinfo
            ],
            generators=[],
        )
