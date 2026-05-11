import pytest
import skhep_testdata

import pylhe

TEST_FILE_LHE_v3 = skhep_testdata.data_path("pylhe-testlhef3.lhe")


def test_write_lhe_file_path_backwards_compatibility(tmp_path):
    lhefile = pylhe.LHEFile.fromfile(TEST_FILE_LHE_v3, with_attributes=True)
    events = lhefile.events
    lhefile.events = [next(events)]

    output_path = tmp_path / "test.lhe"

    with pytest.warns(
        DeprecationWarning,
        match=r"write_lhe_file_path is deprecated and will be removed in a future version",
    ):
        pylhe.write_lhe_file_path(lhefile, str(output_path))

    assert output_path.read_text() == lhefile.tolhe()

    reread = pylhe.LHEFile.fromfile(str(output_path), with_attributes=True)
    assert reread.header is not None
    assert lhefile.header is not None
    assert reread.init.tolhe() == lhefile.init.tolhe()
    assert reread.header.tolhe() == lhefile.header.tolhe()
    assert next(reread.events).tolhe() == lhefile.events[0].tolhe()
