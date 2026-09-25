"""Benchmarks for LHEH5 I/O through the public pylhe API.

Source events are materialized before write timing. Reads are also fully
materialized so that the benchmark includes parsing into pylhe objects.
"""

from pathlib import Path

import pytest
import skhep_testdata

import pylhe


@pytest.fixture(scope="module")
def lhe_file():
    source = skhep_testdata.data_path("pylhe-testfile-sherpa.hdf5")
    return pylhe.LHEFile.fromfile(source, generator=False)


FORMATS = [
    pytest.param(pylhe.HDF5_FORMAT, id="uncompressed-chunks"),
    pytest.param(pylhe.HDF5_GZ_FORMAT, id="gzip-chunks"),
]


def _write_lhe(path: Path, lhe, lheformat) -> None:
    lhe.tofile(path, lheformat=lheformat)


def _read_lhe(path: Path):
    return pylhe.LHEFile.fromfile(path, generator=False)


@pytest.mark.parametrize("lheformat", FORMATS)
def test_lheh5_write_benchmark(benchmark, tmp_path, lhe_file, lheformat):
    """Measure writing already-materialized pylhe events."""
    path = tmp_path / "write.hdf5"
    benchmark(_write_lhe, path, lhe_file, lheformat)

    assert path.stat().st_size > 0


@pytest.mark.parametrize("lheformat", FORMATS)
def test_lheh5_read_benchmark(benchmark, tmp_path, lhe_file, lheformat):
    """Measure reading and parsing a complete LHEH5 file."""
    path = tmp_path / "read.hdf5"
    _write_lhe(path, lhe_file, lheformat)

    result = benchmark(_read_lhe, path)

    assert isinstance(result.events, list)
    assert len(result.events) == len(lhe_file.events)
