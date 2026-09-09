"""
LHEH5 format reader for reading LHE files in HDF5 format.

Note: We do not support ctparticles and ctevents datasets as of now.

References:
    - Stefan Hoeche, Stefan Prestel, and Holger Schulz,
      "Simulation of vector boson plus many jet final states at the high luminosity LHC",
      arXiv:1905.05120 (https://arxiv.org/pdf/1905.05120)
    - Enrico Bothmann et al.,
      "Efficient precision simulation of processes with many-jet final states at the LHC",
      arXiv:2309.13154 (https://arxiv.org/pdf/2309.13154)
"""

from __future__ import annotations

import json
import math
import warnings
from collections.abc import Iterable, Iterator, Sequence
from typing import Any

import h5py  # type: ignore[import-untyped]

import pylhe

_LHEH5_VERSION = (2, 6, 0)

# Below column names are used for reading and writing datasets in LHEH5 format v2.

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

_GENERATOR_COLUMNS = (
    "name",
    "version",
    "description",
    "extraAttributes",
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
    # + further weights are appended here
)


_STRING_DTYPE = h5py.string_dtype(encoding="utf-8")


def _decode_dict_json(s: str) -> Any:
    try:
        return json.loads(s)
    except json.JSONDecodeError:
        warnings.warn(f"Failed to decode JSON attribute: {s}", stacklevel=2)
        return {}


def _encode_dict_json(value: dict[str, str]) -> str:
    return json.dumps(value)


def _decode_attr_values(values: Iterable[object]) -> list[str]:
    return [
        value.decode() if isinstance(value, bytes) else str(value) for value in values
    ]


def _decode_string(value: object) -> str:
    if value is None:
        return ""
    return value.decode() if isinstance(value, bytes) else str(value)


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


def _row_int_or_none(
    row: Sequence[float],
    columns: dict[str, int],
    *names: str,
    default: int | None = None,
) -> int | None:
    for name in names:
        index = columns.get(name)
        if index is not None and index < len(row):
            float_value = float(row[index])
            # check if is nan
            if math.isnan(float_value):
                return None
            return int(float_value)

    return default


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


def _row_string(
    row: Sequence[object],
    columns: dict[str, int],
    *names: str,
    default: str = "",
) -> str:
    for name in names:
        index = columns.get(name)
        if index is not None and index < len(row):
            return _decode_string(row[index])
    return default


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


def _write_generators(lhe: pylhe.LesHouchesEvents, file: h5py.File) -> None:
    generator_rows = [
        [
            generator.name,
            generator.version,
            generator.description,
            _encode_dict_json(generator.extra_attributes),
        ]
        for generator in lhe.init.generators
    ]
    if generator_rows:
        generators = file.create_dataset(
            "generators", data=generator_rows, dtype=_STRING_DTYPE
        )
    else:
        generators = file.create_dataset(
            "generators",
            shape=(0, len(_GENERATOR_COLUMNS)),
            dtype=_STRING_DTYPE,
        )
    _set_column_attrs(generators, _GENERATOR_COLUMNS)


def read_generators(file: h5py.File) -> list[pylhe.LHEGenerator]:
    """Read generator metadata from an HDF5 file in to LHEH5 format."""
    if "generators" in file:
        generators = file["generators"]
        if isinstance(generators, h5py.Dataset):
            generator_columns = _column_indices(generators, default=_GENERATOR_COLUMNS)
            return [
                pylhe.LHEGenerator(
                    name=_row_string(row, generator_columns, "name"),
                    version=_row_string(row, generator_columns, "version"),
                    description=_row_string(row, generator_columns, "description"),
                    extra_attributes=_decode_dict_json(
                        _row_string(
                            row, generator_columns, "extraAttributes", default="{}"
                        )
                    ),
                )
                for row in generators
            ]
    # Now we try the pepper init attrs
    init = file["init"]
    name = _decode_string(init.attrs.get("generatorName", ""))
    version = _decode_string(init.attrs.get("generatorVersion", ""))
    description = _decode_string(init.attrs.get("generatorDescription", ""))
    extra_attributes = _decode_dict_json(
        _decode_string(init.attrs.get("generatorExtraAttributes", "{}"))
    )
    if name or version or description or extra_attributes:
        return [
            pylhe.LHEGenerator(
                name=name,
                version=version,
                description=description,
                extra_attributes=extra_attributes,
            )
        ]
    return []


def _event_scale(event: pylhe.LHEEvent, *names: str, default: float) -> float:
    for name in names:
        value = event.scales.get(name)
        if value is not None:
            return float(value)

    return default


def _event_trials(event: pylhe.LHEEvent) -> float:
    trials = event.attributes.get("trials")
    if trials is None:
        return float("nan")

    try:
        return float(trials)
    except ValueError:
        return float("nan")


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


def count_events(file: h5py.File) -> int:
    """Count the number of events in an HDF5 file in LHEH5 format."""
    events = file["events"]
    return len(events)


def read_iter_events(file: h5py.File) -> Iterator[pylhe.LHEEvent]:
    """Read events from an HDF5 file in LHEH5 format."""
    events = file["events"]
    particles = file["particles"]
    event_columns = _column_indices(events, default=_EVENT_COLUMNS)

    for event_row in events:
        start = _row_int(event_row, event_columns, "start")
        nparticles = _row_int(event_row, event_columns, "nparticles")
        trials = _row_float(event_row, event_columns, "trials", default=float("nan"))
        fscale = _row_float(event_row, event_columns, "fscale", default=float("nan"))
        rscale = _row_float(event_row, event_columns, "rscale", default=float("nan"))
        attributes: dict[str, str] = {}
        scales: dict[str, float] = {}

        if not math.isnan(trials):
            attributes["trials"] = str(trials)
        if not math.isnan(fscale):
            scales["fscale"] = fscale
        if not math.isnan(rscale):
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
                scale=_row_float(
                    event_row, event_columns, "scale", default=float("nan")
                ),
                aqed=_row_float(event_row, event_columns, "aqed", default=float("nan")),
                aqcd=_row_float(event_row, event_columns, "aqcd", default=float("nan")),
            ),
            particles=get_particles(particles, start, nparticles),
            weights=_get_weights(event_row, event_columns),
            scales=scales,
            attributes=attributes,
        )


def _get_weights(event_row: Any, event_columns: dict[str, int]) -> dict[str, float]:
    """Get the weights from an event row in an HDF5 file in to LHEH5 format."""
    weightnames = _weight_columns(event_columns)
    return {
        name: _row_float(event_row, event_columns, name, default=float("nan"))
        for name in weightnames
    }


def _weight_columns(event_columns: dict[str, int]) -> list[str]:
    standard_columns = set(_EVENT_COLUMNS)
    return [name for name in event_columns if name not in standard_columns]


def read_header(file: h5py.File) -> pylhe.LHEHeader | None:
    """Read the header from an HDF5 file in to LHEH5 format."""
    events = file["events"]
    event_columns = _column_indices(events, default=_EVENT_COLUMNS)
    # Construct LHEInitRWGT using the weight names/ids
    weightnames = _weight_columns(event_columns)

    header = file.get("xml/header")

    if isinstance(header, h5py.Dataset):
        lheheader = pylhe.LHEHeader.fromstring(header.asstr()[()])

        # check weightnames are the same as in lheheader.initrwgt
        if weightnames != lheheader.initrwgt.list_weights_ids():
            err = "Weight names in the header do not match the weight names in the events. "
            raise ValueError(err)
        return lheheader
    if not weightnames:
        return None

    # We do not have weight group information nor how weights were defined by default in LHEH5
    return pylhe.LHEHeader(
        initrwgt=pylhe.LHEInitRWGT(
            entries=[
                pylhe.LHEInitRWGTWeight(id=name, name=name) for name in weightnames
            ]
        )
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
                npLO=(_row_int_or_none(row, procinfo_columns, "npLO")),
                npNLO=(_row_int_or_none(row, procinfo_columns, "npNLO")),
            )
            for row in procinfo
        ],
        generators=read_generators(file),
    )


def read_comment(file: h5py.File) -> str | None:
    """Read the comment attribute from an HDF5 file in to LHEH5 format."""
    init = file["init"]
    comment = init.attrs.get("description", None)
    if comment is None:
        return None
    return _decode_string(comment)


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

    if lhe.comment is not None:
        init_dataset.attrs["description"] = lhe.comment
    if lhe.init.generators:
        # Pepper only wants one generator https://gitlab.com/spice-mc/pepper/-/merge_requests/320/
        gen = lhe.init.generators[0]
        init_dataset.attrs["generatorName"] = gen.name
        init_dataset.attrs["generatorVersion"] = gen.version
        init_dataset.attrs["generatorDescription"] = gen.description
        init_dataset.attrs["generatorExtraAttributes"] = _encode_dict_json(
            gen.extra_attributes
        )

    proc_rows = [
        [
            proc.procId,
            float("nan") if proc.npLO is None else proc.npLO,
            float("nan") if proc.npNLO is None else proc.npNLO,
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

    _event_columns = list(_EVENT_COLUMNS)
    weightnames = []
    if lhe.header is not None:
        xml = file.create_group("xml")
        # write header as a string dataset
        header_dataset = xml.create_dataset(
            "header",
            data=lhe.header.tolhe(lheformat=pylhe.DEFAULT_FORMAT).encode("utf-8"),
            dtype=_STRING_DTYPE,
        )
        _set_column_attrs(header_dataset, ("header",))
        weightnames = lhe.header.initrwgt.list_weights_ids()
    if weightnames:
        # if any of the weightnames is also in _EVENT_COLUMNS
        for name in weightnames:
            if name in _event_columns:
                err = (
                    f"Weight name '{name}' is already present in default event columns."
                )
                raise ValueError(err)
        _event_columns += weightnames
    event_columns = tuple(_event_columns)

    events_write_args = _dataset_write_args(
        lheformat,
        chunk_rows=lheformat.event_chunk_rows,
        ncolumns=len(event_columns),
    )
    events_dataset = _create_row_dataset(
        file,
        "events",
        event_columns,
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
                _event_scale(event, "fscale", "muf", default=float("nan")),
                _event_scale(event, "rscale", "mur", default=float("nan")),
                event.eventinfo.aqed,
                event.eventinfo.aqcd,
                event.eventinfo.weight,
                *[event.weights[wid] for wid in weightnames],
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
