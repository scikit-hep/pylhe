import pytest
import skhep_testdata

import pylhe

TEST_FILE = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")


def test_gzip_open(tmpdir):
    assert pylhe._open_gzip_file(TEST_FILE) == TEST_FILE

    tmp_path = tmpdir.join("notrealfile.lhe")
    assert pylhe._open_gzip_file(tmp_path) == tmp_path

    tmp_path = tmpdir.join("notrealfile.lhe.gz")
    tmp_path.write("")
    with pytest.raises(OSError):
        pylhe._open_gzip_file(tmp_path)


def test_event_count():
    assert pylhe.readNumEvents(TEST_FILE) == 791


def test_lhe_init():
    init_data = pylhe.readLHEInit(TEST_FILE)
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
