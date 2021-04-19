import gzip
import os
import shutil
import warnings
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
import skhep_testdata

import pylhe

TEST_FILE = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")


@pytest.fixture(scope="session")
def testdata_gzip_file():
    test_data = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
    tmp_path = Path(NamedTemporaryFile().name)

    # create what is basically pylhe-testfile-pr29.lhe.gz
    with open(test_data, "rb") as readfile:
        with gzip.open(tmp_path, "wb") as writefile:
            shutil.copyfileobj(readfile, writefile)
    yield tmp_path

    # teardown
    os.remove(tmp_path)


def test_gzip_open(tmpdir, testdata_gzip_file):
    assert pylhe._extract_fileobj(TEST_FILE)
    assert pylhe._extract_fileobj(testdata_gzip_file)

    # Needs path-like object, not a fileobj
    with pytest.raises(TypeError):
        with open(TEST_FILE, "rb") as fileobj:
            pylhe._extract_fileobj(fileobj)

    with open(TEST_FILE, "rb") as fileobj:
        assert isinstance(pylhe._extract_fileobj(TEST_FILE), type(fileobj))
        assert isinstance(pylhe._extract_fileobj(Path(TEST_FILE)), type(fileobj))
    assert isinstance(pylhe._extract_fileobj(testdata_gzip_file), gzip.GzipFile)
    assert isinstance(pylhe._extract_fileobj(Path(testdata_gzip_file)), gzip.GzipFile)


def test_read_num_events(testdata_gzip_file):
    assert pylhe.read_num_events(TEST_FILE) == 791
    assert pylhe.read_num_events(TEST_FILE) == pylhe.read_num_events(testdata_gzip_file)


def test_lhe_init(testdata_gzip_file):
    assert pylhe.read_lhe_init(TEST_FILE) == pylhe.read_lhe_init(testdata_gzip_file)

    init_data = pylhe.read_lhe_init(TEST_FILE)
    init_info = init_data["initInfo"]
    assert init_info["beamA"] == pytest.approx(1.0)
    assert init_info["beamB"] == pytest.approx(2.0)
    assert init_info["energyA"] == pytest.approx(1.234567)
    assert init_info["energyB"] == pytest.approx(2.345678)
    assert init_info["PDFgroupA"] == pytest.approx(3.0)
    assert init_info["PDFgroupB"] == pytest.approx(4.0)
    assert init_info["PDFsetA"] == pytest.approx(5.0)
    assert init_info["PDFsetB"] == pytest.approx(6.0)
    assert init_info["weightingStrategy"] == pytest.approx(7.0)
    assert init_info["numProcesses"] == pytest.approx(8.0)


def test_read_lhe(testdata_gzip_file):
    assert pylhe.read_lhe(TEST_FILE)
    assert pylhe.read_lhe(testdata_gzip_file)


# test deprecation warnings
def test_deprecated_apis(testdata_gzip_file):
    with warnings.catch_warnings(record=True) as _warning:
        # Cause all warnings to always be triggered
        warnings.simplefilter("always")
        pylhe.readLHE(TEST_FILE)
        assert len(_warning) == 1
        assert issubclass(_warning[-1].category, DeprecationWarning)
        assert "readLHE is deprecated in favor of read_lhe" in str(_warning[-1].message)

    with warnings.catch_warnings(record=True) as _warning:
        warnings.simplefilter("always")
        pylhe.readLHEInit(TEST_FILE)
        assert len(_warning) == 1
        assert issubclass(_warning[-1].category, DeprecationWarning)
        assert "readLHEInit is deprecated in favor of read_lhe_init" in str(
            _warning[-1].message
        )

    with warnings.catch_warnings(record=True) as _warning:
        warnings.simplefilter("always")
        pylhe.readLHEWithAttributes(TEST_FILE)
        assert len(_warning) == 1
        assert issubclass(_warning[-1].category, DeprecationWarning)
        assert (
            "readLHEWithAttributes is deprecated in favor of read_lhe_with_attributes"
            in str(_warning[-1].message)
        )

    with warnings.catch_warnings(record=True) as _warning:
        warnings.simplefilter("always")
        pylhe.readNumEvents(TEST_FILE)
        assert len(_warning) == 1
        assert issubclass(_warning[-1].category, DeprecationWarning)
        assert "readNumEvents is deprecated in favor of read_num_events" in str(
            _warning[-1].message
        )
