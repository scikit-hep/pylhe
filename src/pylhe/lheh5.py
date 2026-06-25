"""
LHEH5 format reader for reading LHE files in HDF5 format.

References:
    - Stefan Hoeche, Stefan Prestel, and Holger Schulz,
      "Simulation of vector boson plus many jet final states at the high
      luminosity LHC", arXiv:1905.05120
      (https://arxiv.org/pdf/1905.05120)
    - Enrico Bothmann et al.,
      "Efficient precision simulation of processes with many-jet final states
      at the LHC", arXiv:2309.13154
      (https://arxiv.org/pdf/2309.13154)
"""

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

_EVENT_COLUMNS = (
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

_LHEH5_VERSION = (2, 0, 0)


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


def _row_has_column(row: Sequence[float], columns: dict[str, int], name: str) -> bool:
    index = columns.get(name)
    return index is not None and index < len(row)


def _row_int(
    row: Sequence[float],
    columns: dict[str, int],
    *names: str,
    default: int | None = None,
) -> int:
    for name in names:
        index = columns.get(name)
        if index is not None and index < len(row):
            return int(float(row[index]))

    if default is not None:
        return default

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
        if index is not None and index < len(row):
            return float(row[index])

    if default is not None:
        return default

    err = f"None of the requested columns are available: {', '.join(names)}"
    raise KeyError(err)


def _encode_attr_values(values: Iterable[str]) -> list[bytes]:
    return [value.encode() for value in values]


def _set_column_attrs(dataset: h5py.Dataset, columns: Iterable[str]) -> None:
    encoded = _encode_attr_values(columns)
    dataset_name = dataset.name.rsplit("/", maxsplit=1)[-1]
    dataset.attrs["properties"] = encoded
    dataset.attrs[dataset_name] = encoded


def _dataset_write_args(
    lheformat: pylhe.LHEHDF5Format, *, chunk_rows: int, ncolumns: int
) -> dict[str, object]:
    args: dict[str, object] = {"chunks": (chunk_rows, ncolumns)}

    if lheformat.compression is not None:
        args["compression"] = lheformat.compression
    if lheformat.compression_opts is not None:
        args["compression_opts"] = lheformat.compression_opts
    if lheformat.shuffle:
        args["shuffle"] = True

    return args


def _create_row_dataset(
    file: h5py.File,
    name: str,
    columns: tuple[str, ...],
    *,
    write_args: dict[str, object],
) -> h5py.Dataset:
    dataset = file.create_dataset(
        name,
        shape=(0, len(columns)),
        maxshape=(None, len(columns)),
        dtype="f8",
        **write_args,
    )
    _set_column_attrs(dataset, columns)
    return dataset


def _append_rows(dataset: h5py.Dataset, rows: list[list[float]]) -> None:
    if not rows:
        return

    start = dataset.shape[0]
    stop = start + len(rows)
    dataset.resize((stop, dataset.shape[1]))
    dataset[start:stop] = rows


def _event_scale(event: pylhe.LHEEvent, *names: str, default: float = 0.0) -> float:
    for name in names:
        value = event.scales.get(name)
        if value is not None:
            return float(value)

    return default


def _event_trials(event: pylhe.LHEEvent) -> float:
    trials = event.attributes.get("trials")
    if trials is None:
        return 0.0

    try:
        return float(trials)
    except ValueError:
        return 0.0


def get_particles(
    particles: h5py.Dataset, start: int, n: int
) -> list[pylhe.LHEParticle]:
    """Get a list of LHEParticle objects from a particles dataset."""
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


def read_iter_events(file: h5py.File) -> Iterator[pylhe.LHEEvent]:
    """Read events from an HDF5 file in LHEH5 format."""
    events = file["events"]
    particles = file["particles"]
    event_columns = _column_indices(events)

    for event_row in events:
        start = _row_int(event_row, event_columns, "start")
        nparticles = _row_int(event_row, event_columns, "nparticles")
        trials = _row_float(event_row, event_columns, "trials", default=0.0)
        fscale = _row_float(event_row, event_columns, "fscale", default=0.0)
        rscale = _row_float(event_row, event_columns, "rscale", default=0.0)
        attributes: dict[str, str] = {}
        scales: dict[str, float] = {}

        if trials != 0.0:
            attributes["trials"] = str(trials)
        if fscale != 0.0:
            scales["fscale"] = fscale
        if rscale != 0.0:
            scales["rscale"] = rscale

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
            particles=get_particles(particles, start, nparticles),
            scales=scales,
            attributes=attributes,
        )


def read_init(file: h5py.File) -> pylhe.LHEInit:
    """Read the init and procInfo datasets from an HDF5 file in LHEH5 format."""
    init = file["init"]
    procinfo = file["procInfo"]
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
                npLO=(
                    _row_int(row, procinfo_columns, "npLO")
                    if _row_has_column(row, procinfo_columns, "npLO")
                    else None
                ),
                npNLO=(
                    _row_int(row, procinfo_columns, "npNLO")
                    if _row_has_column(row, procinfo_columns, "npNLO")
                    else None
                ),
            )
            for row in procinfo
        ],
        generators=[],
    )


def write(
    lhe: pylhe.LesHouchesEvents, file: h5py.File, lheformat: pylhe.LHEHDF5Format
) -> None:
    """Write a LesHouchesEvents object to an HDF5 file in LHEH5 format."""
    proc_info = lhe.init.procInfo
    init_info = lhe.init.initInfo

    if init_info.numProcesses != len(proc_info):
        err = (
            "initInfo.numProcesses does not match the number of procInfo rows: "
            f"{init_info.numProcesses} != {len(proc_info)}"
        )
        raise ValueError(err)

    init_dataset = file.create_dataset(
        "init",
        data=[
            init_info.beamA,
            init_info.beamB,
            init_info.energyA,
            init_info.energyB,
            init_info.PDFgroupA,
            init_info.PDFgroupB,
            init_info.PDFsetA,
            init_info.PDFsetB,
            init_info.weightingStrategy,
            init_info.numProcesses,
        ],
        dtype="f8",
    )
    _set_column_attrs(init_dataset, _INIT_COLUMNS)

    proc_rows = [
        [
            proc.procId,
            0.0 if proc.npLO is None else proc.npLO,
            0.0 if proc.npNLO is None else proc.npNLO,
            proc.xSection,
            proc.error,
            proc.unitWeight,
        ]
        for proc in proc_info
    ]
    proc_dataset = file.create_dataset(
        "procInfo",
        data=proc_rows or None,
        shape=(len(proc_rows), len(_PROCINFO_COLUMNS)),
        dtype="f8",
    )
    _set_column_attrs(proc_dataset, _PROCINFO_COLUMNS)

    events_write_args = _dataset_write_args(
        lheformat,
        chunk_rows=lheformat.event_chunk_rows,
        ncolumns=len(_EVENT_COLUMNS),
    )
    events_dataset = _create_row_dataset(
        file,
        "events",
        _EVENT_COLUMNS,
        write_args=events_write_args,
    )
    particles_write_args = _dataset_write_args(
        lheformat,
        chunk_rows=lheformat.particle_chunk_rows,
        ncolumns=len(_PARTICLE_COLUMNS),
    )
    particles_dataset = _create_row_dataset(
        file,
        "particles",
        _PARTICLE_COLUMNS,
        write_args=particles_write_args,
    )

    particle_rows: list[list[float]] = []
    event_rows: list[list[float]] = []
    start = 0

    def _flush_pending_rows() -> None:
        _append_rows(events_dataset, event_rows)
        _append_rows(particles_dataset, particle_rows)
        event_rows.clear()
        particle_rows.clear()

    for event in lhe.events:
        nparticles = len(event.particles)
        if event.eventinfo.nparticles != nparticles:
            err = (
                "eventinfo.nparticles does not match the number of particle rows: "
                f"{event.eventinfo.nparticles} != {nparticles}"
            )
            raise ValueError(err)

        event_rows.append(
            [
                event.eventinfo.pid,
                nparticles,
                start,
                _event_trials(event),
                event.eventinfo.scale,
                _event_scale(event, "fscale", "muf"),
                _event_scale(event, "rscale", "mur"),
                event.eventinfo.aqed,
                event.eventinfo.aqcd,
                event.eventinfo.weight,
            ]
        )

        particle_rows.extend(
            [
                [
                    particle.id,
                    particle.status,
                    particle.mother1,
                    particle.mother2,
                    particle.color1,
                    particle.color2,
                    particle.px,
                    particle.py,
                    particle.pz,
                    particle.e,
                    particle.m,
                    particle.lifetime,
                    particle.spin,
                ]
                for particle in event.particles
            ]
        )
        start += nparticles
        if (
            len(event_rows) >= lheformat.event_chunk_rows
            or len(particle_rows) >= lheformat.particle_chunk_rows
        ):
            _flush_pending_rows()

    _flush_pending_rows()

    file.create_dataset("version", data=_LHEH5_VERSION, dtype="i8")
