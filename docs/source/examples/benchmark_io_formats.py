"""Compare pylhe read, write, and storage performance across file formats.

This is deliberately a standalone benchmark rather than a pytest benchmark: the
default one-million-event run is much too expensive for routine test suites.

The benchmark keeps one source event list in memory and fully materializes every
read with ``list(lhe.events)``.  Results include the raw measurements and three
best-normalized metrics:

* write speed: fastest median write time / this median write time
* read speed: fastest median read time / this median read time
* compactness: smallest file size / this file size

The overall score is the equally weighted geometric mean of those metrics.  It
is a convenient summary, not a universal definition of the "best" format.

Examples:

    # Deterministic synthetic sample with 1,000,000 events (the default)
    python docs/source/examples/benchmark_io_formats.py

    # Fast smoke run
    python docs/source/examples/benchmark_io_formats.py --events 100 --repeats 1 --warmups 0

    # Use an existing LHE/LHE.gz/LHEH5 sample and keep the generated files
    python docs/source/examples/benchmark_io_formats.py --input sample.lhe.gz --keep-files

    # Also test the optional hdf5plugin Bitshuffle + Zstandard filter
    python docs/source/examples/benchmark_io_formats.py --include-bitshuffle

The optional chart needs matplotlib.  The Bitshuffle case needs hdf5plugin.
Neither package is required by pylhe itself.
"""

from __future__ import annotations

import argparse
import csv
import gc
import importlib
import itertools
import json
import math
import os
import platform
import random
import statistics
import tempfile
import time
from collections.abc import Callable, Iterator, Sequence
from contextlib import ExitStack
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import h5py  # type: ignore[import-untyped]

import pylhe

DEFAULT_NUM_EVENTS = 1_000_000
DEFAULT_REPEATS = 3
DEFAULT_WARMUPS = 1
DEFAULT_SEED = 1337
WEIGHT_IDS = ("1001", "1002", "1003", "1004", "1005", "1006")


@dataclass(frozen=True, slots=True)
class FormatCase:
    """One output format included in the comparison."""

    key: str
    label: str
    filename: str
    lheformat: pylhe.LHEOutputFormat


@dataclass(slots=True)
class BenchmarkResult:
    """Raw samples and derived metrics for one format."""

    key: str
    label: str
    filename: str
    write_seconds: list[float] = field(default_factory=list)
    read_seconds: list[float] = field(default_factory=list)
    size_bytes: int = 0
    write_seconds_median: float = 0.0
    read_seconds_median: float = 0.0
    write_events_per_second: float = 0.0
    read_events_per_second: float = 0.0
    relative_write_speed: float = 0.0
    relative_read_speed: float = 0.0
    relative_compactness: float = 0.0
    overall_score: float = 0.0
    write_rank: int = 0
    read_rank: int = 0
    size_rank: int = 0
    overall_rank: int = 0


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        msg = f"expected a positive integer, got {value!r}"
        raise argparse.ArgumentTypeError(msg)
    return parsed


def _nonnegative_int(value: str) -> int:
    parsed = int(value)
    if parsed < 0:
        msg = f"expected a non-negative integer, got {value!r}"
        raise argparse.ArgumentTypeError(msg)
    return parsed


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

    particles = [
        _build_particle(21, -1, 0, 0, 501, 0, 0.0, 0.0, 6500.0, 0.0, 0.0),
        _build_particle(21, -1, 0, 0, 0, 502, 0.0, 0.0, -6500.0, 0.0, 0.0),
        _build_particle(1, 1, 1, 2, 501, 0, px, py, pz, mass_a, 9.0),
        _build_particle(-1, 1, 1, 2, 0, 502, -px, -py, -pz, mass_b, -9.0),
    ]
    weights = {
        weight_id: base_weight * rng.uniform(0.8, 1.2) for weight_id in WEIGHT_IDS
    }

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
        scales={"fscale": scale * 0.9, "rscale": scale * 1.1},
        attributes={"trials": str(rng.randint(1, 100))},
    )


def _random_events(num_events: int, seed: int) -> Iterator[pylhe.LHEEvent]:
    rng = random.Random(seed)
    for _ in range(num_events):
        yield _random_event(rng)


def _synthetic_lhe(num_events: int, seed: int) -> pylhe.LHEFile:
    return pylhe.LHEFile(
        init=_build_init(),
        header=_build_header(),
        events=list(_random_events(num_events, seed)),
        version="3.0",
    )


def _close_iterator(iterator: object) -> None:
    close = getattr(iterator, "close", None)
    if callable(close):
        close()


def _load_lhe(path: Path, limit: int | None) -> pylhe.LHEFile:
    source = pylhe.LHEFile.fromfile(path)
    source_events = source.events
    try:
        if limit is None:
            events = list(source_events)
        else:
            events = list(itertools.islice(source_events, limit))
    finally:
        _close_iterator(source_events)

    if not events:
        msg = f"input contains no events: {path}"
        raise ValueError(msg)

    return pylhe.LHEFile(
        init=source.init,
        events=events,
        header=source.header,
        comment=source.comment,
        version=source.version,
        extra_attributes=dict(source.extra_attributes),
    )


def _bitshuffle_case(zstd_level: int) -> FormatCase:
    try:
        hdf5plugin = importlib.import_module("hdf5plugin")
    except ImportError as exc:
        msg = (
            "--include-bitshuffle requires the optional hdf5plugin package; "
            "install it with `python -m pip install hdf5plugin`"
        )
        raise RuntimeError(msg) from exc

    # Bitshuffle is itself the preprocessing filter, so h5py's byte-shuffle
    # option must remain disabled for this case.
    plugin_options = dict(hdf5plugin.Bitshuffle(cname="zstd", clevel=zstd_level))
    lheformat = pylhe.LHEHDF5Format(
        compression=plugin_options["compression"],  # type: ignore[arg-type]
        compression_opts=plugin_options["compression_opts"],  # type: ignore[arg-type]
        shuffle=False,
    )
    return FormatCase(
        key="hdf5-bitshuffle-zstd",
        label=f"HDF5 Bitshuffle + Zstd-{zstd_level}",
        filename="events-bitshuffle-zstd.hdf5",
        lheformat=lheformat,
    )


def _format_cases(include_bitshuffle: bool, zstd_level: int) -> list[FormatCase]:
    cases = [
        FormatCase(
            key="lhe",
            label="LHE (plain)",
            filename="events.lhe",
            lheformat=pylhe.DEFAULT_FORMAT,
        ),
        FormatCase(
            key="lhe-gzip",
            label="LHE gzip-9",
            filename="events.lhe.gz",
            lheformat=pylhe.GZ_FORMAT,
        ),
        FormatCase(
            key="hdf5",
            label="HDF5 (uncompressed)",
            filename="events.hdf5",
            lheformat=pylhe.HDF5_FORMAT,
        ),
        FormatCase(
            key="hdf5-gzip-shuffle",
            label="HDF5 gzip-4 + byte shuffle",
            filename="events-gzip-shuffle.hdf5",
            lheformat=pylhe.LHEHDF5Format(
                compression="gzip",
                compression_opts=4,
                shuffle=True,
            ),
        ),
    ]
    if include_bitshuffle:
        cases.append(_bitshuffle_case(zstd_level))
    return cases


def _time_write(
    lhe: pylhe.LHEFile,
    path: Path,
    lheformat: pylhe.LHEOutputFormat,
    *,
    fsync: bool,
) -> float:
    started = time.perf_counter()
    lhe.tofile(path, lheformat=lheformat)
    if fsync:
        with path.open("rb") as stream:
            os.fsync(stream.fileno())
    return time.perf_counter() - started


def _time_read(path: Path, expected_events: int) -> float:
    started = time.perf_counter()
    loaded = pylhe.LHEFile.fromfile(path)
    # Keep this explicit: the benchmark intentionally measures a full in-memory
    # read, rather than only constructing or partially consuming the generator.
    loaded_events = list(loaded.events)
    elapsed = time.perf_counter() - started

    if len(loaded_events) != expected_events:
        msg = (
            f"read {len(loaded_events)} events from {path}, expected {expected_events}"
        )
        raise RuntimeError(msg)

    del loaded_events
    return elapsed


def _run_rounds(
    operation: str,
    cases: Sequence[FormatCase],
    rounds: int,
    seed: int,
    function: Callable[[FormatCase], float],
    *,
    record: bool,
    results: dict[str, BenchmarkResult],
    log: Callable[[str], None],
) -> None:
    rng = random.Random(seed)
    for round_index in range(rounds):
        ordered_cases = list(cases)
        rng.shuffle(ordered_cases)
        for case in ordered_cases:
            gc.collect()
            log(f"{operation} round {round_index + 1}/{rounds}: {case.label} ...")
            elapsed = function(case)
            log(f"  {elapsed:.3f} s")
            if record:
                samples = (
                    results[case.key].write_seconds
                    if operation == "write"
                    else results[case.key].read_seconds
                )
                samples.append(elapsed)


def _assign_ranks(
    results: Sequence[BenchmarkResult], attribute: str, rank_attribute: str
) -> None:
    for rank, result in enumerate(
        sorted(results, key=lambda item: getattr(item, attribute)), start=1
    ):
        setattr(result, rank_attribute, rank)


def _derive_metrics(
    results: Sequence[BenchmarkResult], num_events: int
) -> list[BenchmarkResult]:
    for result in results:
        result.write_seconds_median = statistics.median(result.write_seconds)
        result.read_seconds_median = statistics.median(result.read_seconds)
        result.write_events_per_second = num_events / result.write_seconds_median
        result.read_events_per_second = num_events / result.read_seconds_median

    fastest_write = min(result.write_seconds_median for result in results)
    fastest_read = min(result.read_seconds_median for result in results)
    smallest_size = min(result.size_bytes for result in results)

    for result in results:
        result.relative_write_speed = fastest_write / result.write_seconds_median
        result.relative_read_speed = fastest_read / result.read_seconds_median
        result.relative_compactness = smallest_size / result.size_bytes
        result.overall_score = (
            result.relative_write_speed
            * result.relative_read_speed
            * result.relative_compactness
        ) ** (1.0 / 3.0)

    _assign_ranks(results, "write_seconds_median", "write_rank")
    _assign_ranks(results, "read_seconds_median", "read_rank")
    _assign_ranks(results, "size_bytes", "size_rank")

    ranked = sorted(results, key=lambda result: result.overall_score, reverse=True)
    for rank, result in enumerate(ranked, start=1):
        result.overall_rank = rank
    return ranked


def run_benchmark(
    lhe: pylhe.LHEFile,
    cases: Sequence[FormatCase],
    work_dir: Path,
    *,
    repeats: int,
    warmups: int,
    seed: int,
    fsync: bool,
    log: Callable[[str], None],
) -> list[BenchmarkResult]:
    """Run all write and full-read measurements and return ranked results."""
    events = lhe.events
    if not isinstance(events, list):
        msg = "benchmark source events must already be materialized as a list"
        raise TypeError(msg)
    num_events = len(events)
    paths = {case.key: work_dir / case.filename for case in cases}
    results = {
        case.key: BenchmarkResult(case.key, case.label, case.filename) for case in cases
    }

    write = lambda case: _time_write(lhe, paths[case.key], case.lheformat, fsync=fsync)
    read = lambda case: _time_read(paths[case.key], num_events)

    if warmups:
        log("Write warm-up")
        _run_rounds(
            "write",
            cases,
            warmups,
            seed,
            write,
            record=False,
            results=results,
            log=log,
        )

    log("Measured writes")
    _run_rounds(
        "write",
        cases,
        repeats,
        seed + 1,
        write,
        record=True,
        results=results,
        log=log,
    )

    for case in cases:
        results[case.key].size_bytes = paths[case.key].stat().st_size

    if warmups:
        log("Read warm-up")
        _run_rounds(
            "read",
            cases,
            warmups,
            seed + 2,
            read,
            record=False,
            results=results,
            log=log,
        )

    log("Measured reads")
    _run_rounds(
        "read",
        cases,
        repeats,
        seed + 3,
        read,
        record=True,
        results=results,
        log=log,
    )

    return _derive_metrics(list(results.values()), num_events)


def _markdown_table(results: Sequence[BenchmarkResult]) -> str:
    header = (
        "| Overall rank | Format | Write median (s) | Read median (s) | "
        "Size (MiB) | W/R/S ranks | Write rel. | Read rel. | Size rel. | "
        "Overall |\n"
        "| ---: | :--- | ---: | ---: | ---: | :---: | ---: | ---: | ---: | "
        "---: |"
    )
    rows = [header]
    for result in results:
        rows.append(
            "| "
            f"{result.overall_rank} | {result.label} | "
            f"{result.write_seconds_median:.3f} | "
            f"{result.read_seconds_median:.3f} | "
            f"{result.size_bytes / (1024**2):.2f} | "
            f"{result.write_rank}/{result.read_rank}/{result.size_rank} | "
            f"{result.relative_write_speed:.1%} | "
            f"{result.relative_read_speed:.1%} | "
            f"{result.relative_compactness:.1%} | "
            f"{result.overall_score:.1%} |"
        )
    return "\n".join(rows) + "\n"


def _write_csv(path: Path, results: Sequence[BenchmarkResult], num_events: int) -> None:
    fieldnames = [
        "overall_rank",
        "format",
        "key",
        "filename",
        "num_events",
        "write_seconds_median",
        "read_seconds_median",
        "write_events_per_second",
        "read_events_per_second",
        "size_bytes",
        "size_mib",
        "write_rank",
        "read_rank",
        "size_rank",
        "relative_write_speed",
        "relative_read_speed",
        "relative_compactness",
        "overall_score",
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for result in results:
            writer.writerow(
                {
                    "overall_rank": result.overall_rank,
                    "format": result.label,
                    "key": result.key,
                    "filename": result.filename,
                    "num_events": num_events,
                    "write_seconds_median": result.write_seconds_median,
                    "read_seconds_median": result.read_seconds_median,
                    "write_events_per_second": result.write_events_per_second,
                    "read_events_per_second": result.read_events_per_second,
                    "size_bytes": result.size_bytes,
                    "size_mib": result.size_bytes / (1024**2),
                    "write_rank": result.write_rank,
                    "read_rank": result.read_rank,
                    "size_rank": result.size_rank,
                    "relative_write_speed": result.relative_write_speed,
                    "relative_read_speed": result.relative_read_speed,
                    "relative_compactness": result.relative_compactness,
                    "overall_score": result.overall_score,
                }
            )


def _write_json(
    path: Path,
    results: Sequence[BenchmarkResult],
    metadata: dict[str, Any],
) -> None:
    payload = {
        "metadata": metadata,
        "ranking_method": (
            "geometric mean of best-normalized write speed, read speed, and compactness"
        ),
        "results": [asdict(result) for result in results],
    }
    with path.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2)
        stream.write("\n")


def _write_chart(path: Path, results: Sequence[BenchmarkResult]) -> bool:
    try:
        matplotlib = importlib.import_module("matplotlib")
        matplotlib.use("Agg")
        pyplot = importlib.import_module("matplotlib.pyplot")
    except ImportError:
        return False

    labels = [result.label for result in results]
    y_positions = list(range(len(results)))
    metrics = [
        ("Write speed", [result.relative_write_speed for result in results]),
        ("Read speed", [result.relative_read_speed for result in results]),
        ("Compactness", [result.relative_compactness for result in results]),
        ("Overall", [result.overall_score for result in results]),
    ]
    bar_height = 0.18
    offsets = (-1.5, -0.5, 0.5, 1.5)

    figure, axis = pyplot.subplots(figsize=(11, max(4.5, 1.2 * len(results))))
    for (metric_name, values), offset in zip(metrics, offsets, strict=True):
        axis.barh(
            [position + offset * bar_height for position in y_positions],
            [100.0 * value for value in values],
            height=bar_height,
            label=metric_name,
        )

    axis.set_yticks(y_positions, labels=labels)
    axis.invert_yaxis()
    axis.set_xlim(0, 105)
    axis.set_xlabel("Relative score (% of best result; higher is better)")
    axis.set_title("pylhe format read/write/storage comparison")
    axis.grid(axis="x", alpha=0.25)
    axis.legend(ncols=2, loc="lower right")
    figure.tight_layout()
    figure.savefig(path, dpi=180)
    pyplot.close(figure)
    return True


def _metadata(
    args: argparse.Namespace,
    *,
    input_path: Path | None,
    num_events: int,
    work_dir: Path,
) -> dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "pylhe": pylhe.__version__,
        "h5py": h5py.__version__,
        "input": str(input_path.resolve()) if input_path is not None else "synthetic",
        "num_events": num_events,
        "seed": args.seed,
        "repeats": args.repeats,
        "warmups": args.warmups,
        "fsync": args.fsync,
        "work_dir": str(work_dir.resolve()),
        "include_bitshuffle": args.include_bitshuffle,
        "bitshuffle_zstd_level": (args.zstd_level if args.include_bitshuffle else None),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        help="existing LHE, LHE.gz, or LHEH5 source; otherwise generate data",
    )
    parser.add_argument(
        "--events",
        type=_positive_int,
        help=(
            f"synthetic event count (default: {DEFAULT_NUM_EVENTS:,}); with "
            "--input, read at most this many events"
        ),
    )
    parser.add_argument(
        "--repeats",
        type=_positive_int,
        default=DEFAULT_REPEATS,
        help=f"measured rounds per operation (default: {DEFAULT_REPEATS})",
    )
    parser.add_argument(
        "--warmups",
        type=_nonnegative_int,
        default=DEFAULT_WARMUPS,
        help=f"unmeasured rounds per operation (default: {DEFAULT_WARMUPS})",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=f"synthetic-data and format-order seed (default: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--include-bitshuffle",
        action="store_true",
        help="add optional hdf5plugin Bitshuffle + Zstandard",
    )
    parser.add_argument(
        "--zstd-level",
        type=int,
        choices=range(1, 23),
        default=22,
        metavar="1..22",
        help="Zstandard level for the Bitshuffle case (default: 22)",
    )
    parser.add_argument(
        "--fsync",
        action="store_true",
        help="include an fsync in each write timing",
    )
    parser.add_argument(
        "--work-dir",
        type=Path,
        help="directory for large benchmark files; files are retained",
    )
    parser.add_argument(
        "--keep-files",
        action="store_true",
        help="keep benchmark files under OUTPUT_DIR/files instead of using /tmp",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(".benchmarks/io-formats"),
        help="report directory (default: .benchmarks/io-formats)",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="do not create the matplotlib PNG chart",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="suppress progress messages (the final table is still printed)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    log = (lambda _message: None) if args.quiet else print

    try:
        cases = _format_cases(args.include_bitshuffle, args.zstd_level)
    except RuntimeError as exc:
        parser.error(str(exc))

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.input is None:
        num_events = args.events or DEFAULT_NUM_EVENTS
        log(f"Building {num_events:,} deterministic synthetic events in memory ...")
        lhe = _synthetic_lhe(num_events, args.seed)
        input_path = None
    else:
        input_path = args.input
        log(f"Loading source events from {input_path} into memory ...")
        lhe = _load_lhe(input_path, args.events)
        if not isinstance(lhe.events, list):
            msg = "failed to materialize source events"
            raise TypeError(msg)
        num_events = len(lhe.events)
        log(f"Loaded {num_events:,} events")

    with ExitStack() as stack:
        if args.work_dir is not None:
            work_dir = args.work_dir
            work_dir.mkdir(parents=True, exist_ok=True)
        elif args.keep_files:
            work_dir = output_dir / "files"
            work_dir.mkdir(parents=True, exist_ok=True)
        else:
            temporary_dir = stack.enter_context(
                tempfile.TemporaryDirectory(prefix="pylhe-io-benchmark-")
            )
            work_dir = Path(temporary_dir)

        log(f"Benchmark files: {work_dir}")
        results = run_benchmark(
            lhe,
            cases,
            work_dir,
            repeats=args.repeats,
            warmups=args.warmups,
            seed=args.seed,
            fsync=args.fsync,
            log=log,
        )
        metadata = _metadata(
            args,
            input_path=input_path,
            num_events=num_events,
            work_dir=work_dir,
        )

        table = _markdown_table(results)
        (output_dir / "results.md").write_text(table, encoding="utf-8")
        _write_csv(output_dir / "results.csv", results, num_events)
        _write_json(output_dir / "results.json", results, metadata)

        chart_written = False
        if not args.no_plot:
            chart_written = _write_chart(
                output_dir / "relative-performance.png", results
            )

        print("\n" + table)
        print(f"Reports written to {output_dir.resolve()}")
        if not args.no_plot and not chart_written:
            print("Chart skipped: install matplotlib or pass --no-plot")
        if args.work_dir is not None or args.keep_files:
            print(f"Benchmark data files retained in {work_dir.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
