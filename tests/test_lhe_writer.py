import gzip
import io

import pytest
import skhep_testdata

import pylhe

TEST_FILE_LHE_v1 = skhep_testdata.data_path("pylhe-testfile-pr29.lhe")
TEST_FILE_LHE_v3 = skhep_testdata.data_path("pylhe-testlhef3.lhe")
TEST_FILE_LHE_POWHEG_TRIJET = skhep_testdata.data_path(
    "pylhe-testfile-powheg-box-v2-trijet.lhe"
)
TEST_FILE_LHE_INITRWGT_WEIGHTS = skhep_testdata.data_path(
    "pylhe-testfile-powheg-box-v2-hvq.lhe"
)
TEST_FILE_LHE_RWGT_WGT = skhep_testdata.data_path("pylhe-testfile-powheg-box-v2-W.lhe")
TEST_FILES_LHE_POWHEG = [
    skhep_testdata.data_path(f"pylhe-testfile-powheg-box-v2-{proc}.lhe")
    for proc in ["Z", "W", "Zj", "trijet", "directphoton", "hvq"]
]


def test_write_lhe_eventline():
    """
    Test that the event line is written correctly.
    """
    events = pylhe.LHEFile.fromfile(TEST_FILE_LHE_v3).events
    e = next(events)
    assert (
        e.particles[0].tolhe()
        == "    5  -1   0   0 501   0  0.00000000e+00  0.00000000e+00  1.43229060e+02  1.43309460e+02  4.80000000e+00  0.0000e+00  0.0000e+00"
    )


def test_write_lhe_eventinfo():
    """
    Test that the event info is written correctly.
    """
    events = pylhe.LHEFile.fromfile(TEST_FILE_LHE_v3).events
    e = next(events)
    assert (
        e.eventinfo.tolhe()
        == "  5     66  5.0109093000e+01  1.4137688000e+02  7.5563862000e-03  1.2114027000e-01"
    )


def test_write_lhe_event():
    """
    Test that the event is written correctly.
    """
    events = pylhe.LHEFile.fromfile(TEST_FILE_LHE_v3).events
    e = next(events)
    assert (
        e.tolhe()
        == """<event>
  5     66  5.0109093000e+01  1.4137688000e+02  7.5563862000e-03  1.2114027000e-01
    5  -1   0   0 501   0  0.00000000e+00  0.00000000e+00  1.43229060e+02  1.43309460e+02  4.80000000e+00  0.0000e+00  0.0000e+00
    2  -1   0   0 502   0  0.00000000e+00  0.00000000e+00 -9.35443170e+02  9.35443230e+02  3.30000000e-01  0.0000e+00  0.0000e+00
   24   1   1   2   0   0 -8.42588040e+01 -1.57085660e+02 -1.06296000e+02  2.22571620e+02  8.03980000e+01  0.0000e+00  0.0000e+00
    5   1   1   2 501   0 -1.36680730e+02 -3.63074240e+01 -4.06144730e+01  1.47215580e+02  4.80000000e+00  0.0000e+00  0.0000e+00
    1   1   1   2 502   0  2.20939540e+02  1.93393080e+02 -6.45303640e+02  7.08965480e+02  3.30000000e-01  0.0000e+00  0.0000e+00
<rwgt>
 <wgt id='1001'> 5.0109e+01</wgt>
 <wgt id='1002'> 4.5746e+01</wgt>
 <wgt id='1003'> 5.2581e+01</wgt>
 <wgt id='1004'> 5.0109e+01</wgt>
 <wgt id='1005'> 4.5746e+01</wgt>
 <wgt id='1006'> 5.2581e+01</wgt>
 <wgt id='1007'> 5.0109e+01</wgt>
 <wgt id='1008'> 4.5746e+01</wgt>
 <wgt id='1009'> 5.2581e+01</wgt>
</rwgt>
<scales muf='90.1' mur='90.2' mups='90.3' newscale='90.4'/>
</event>"""
    )


def test_write_lhe_init():
    """
    Test that the <init> block is written correctly.
    """
    init = pylhe.LHEFile.fromfile(TEST_FILE_LHE_v3).init

    assert (
        init.initInfo.tolhe()
        == "   2212   2212  4.0000000e+03  4.0000000e+03    -1    -1  21100  21100    -4     1"
    )
    assert (
        init.procInfo[0].tolhe() == " 5.0109086e+01  8.9185414e-02  5.0109093e+01    66"
    )

    assert (
        init.tolhe()
        == """<init>
   2212   2212  4.0000000e+03  4.0000000e+03    -1    -1  21100  21100    -4     1
 5.0109086e+01  8.9185414e-02  5.0109093e+01    66
<generator name="SomeGen1" version="1.2.3">some additional comments</generator>
<generator name="SomeGen2" version="a.x.3">some other comments</generator>
<generator name="SomeGen3" version="+.#.@">more comments</generator>
</init>"""
    )
    assert (
        init.tolhe()
        == pylhe.LHEFile.fromstring(
            f"""
        <LesHouchesEvents version="3.0">
        {init.tolhe()}
        </LesHouchesEvents>
        """
        ).init.tolhe()
    )


def test_write_lhe_generator_escapes_attributes():
    generator = pylhe.LHEGenerator(
        description="some additional comments",
        extra_attributes={},
        name='Some "Gen" & Co',
        version="1'2&3",
    )

    assert (
        generator.tolhe()
        == """<generator name='Some "Gen" &amp; Co' version="1'2&amp;3">some additional comments</generator>"""
    )


def test_write_lhe():
    """
    Test that the LHE file is written correctly.
    """
    file = pylhe.LHEFile.fromfile(TEST_FILE_LHE_v3, with_attributes=True)
    assert file.header is not None
    events = file.events
    # single test event
    file.events = [next(events)]
    header = file.header.tolhe()
    init = file.init.tolhe()

    assert (
        file.tolhe(True, False)
        == f"""<LesHouchesEvents version="3.0">
{header}
{init}
<event>
  5     66  5.0109093000e+01  1.4137688000e+02  7.5563862000e-03  1.2114027000e-01
    5  -1   0   0 501   0  0.00000000e+00  0.00000000e+00  1.43229060e+02  1.43309460e+02  4.80000000e+00  0.0000e+00  0.0000e+00
    2  -1   0   0 502   0  0.00000000e+00  0.00000000e+00 -9.35443170e+02  9.35443230e+02  3.30000000e-01  0.0000e+00  0.0000e+00
   24   1   1   2   0   0 -8.42588040e+01 -1.57085660e+02 -1.06296000e+02  2.22571620e+02  8.03980000e+01  0.0000e+00  0.0000e+00
    5   1   1   2 501   0 -1.36680730e+02 -3.63074240e+01 -4.06144730e+01  1.47215580e+02  4.80000000e+00  0.0000e+00  0.0000e+00
    1   1   1   2 502   0  2.20939540e+02  1.93393080e+02 -6.45303640e+02  7.08965480e+02  3.30000000e-01  0.0000e+00  0.0000e+00
<rwgt>
 <wgt id='1001'> 5.0109e+01</wgt>
 <wgt id='1002'> 4.5746e+01</wgt>
 <wgt id='1003'> 5.2581e+01</wgt>
 <wgt id='1004'> 5.0109e+01</wgt>
 <wgt id='1005'> 4.5746e+01</wgt>
 <wgt id='1006'> 5.2581e+01</wgt>
 <wgt id='1007'> 5.0109e+01</wgt>
 <wgt id='1008'> 4.5746e+01</wgt>
 <wgt id='1009'> 5.2581e+01</wgt>
</rwgt>
<scales muf='90.1' mur='90.2' mups='90.3' newscale='90.4'/>
</event>
</LesHouchesEvents>"""
    )

    assert (
        file.tolhe(rwgt=False, weights=True)
        == f"""<LesHouchesEvents version="3.0">
{header}
{init}
<event>
  5     66  5.0109093000e+01  1.4137688000e+02  7.5563862000e-03  1.2114027000e-01
    5  -1   0   0 501   0  0.00000000e+00  0.00000000e+00  1.43229060e+02  1.43309460e+02  4.80000000e+00  0.0000e+00  0.0000e+00
    2  -1   0   0 502   0  0.00000000e+00  0.00000000e+00 -9.35443170e+02  9.35443230e+02  3.30000000e-01  0.0000e+00  0.0000e+00
   24   1   1   2   0   0 -8.42588040e+01 -1.57085660e+02 -1.06296000e+02  2.22571620e+02  8.03980000e+01  0.0000e+00  0.0000e+00
    5   1   1   2 501   0 -1.36680730e+02 -3.63074240e+01 -4.06144730e+01  1.47215580e+02  4.80000000e+00  0.0000e+00  0.0000e+00
    1   1   1   2 502   0  2.20939540e+02  1.93393080e+02 -6.45303640e+02  7.08965480e+02  3.30000000e-01  0.0000e+00  0.0000e+00
<weights>
 5.0109e+01
 4.5746e+01
 5.2581e+01
 5.0109e+01
 4.5746e+01
 5.2581e+01
 5.0109e+01
 4.5746e+01
 5.2581e+01
</weights>
<scales muf='90.1' mur='90.2' mups='90.3' newscale='90.4'/>
</event>
</LesHouchesEvents>"""
    )


def test_write_lhe_includes_powheg_comment():
    """
    Test that writing a POWHEG LHE file preserves the top-level XML comment.
    """
    file = pylhe.LHEFile.fromfile(TEST_FILE_LHE_POWHEG_TRIJET, with_attributes=True)
    events = file.events
    file.events = [next(events)]

    output = file.tolhe()

    assert "<!-- file generated with POWHEG-BOX-V2" in output
    assert "End of powheg.input content" in output
    assert output.index("<!-- ") < output.index("<init>")


def test_write_lhe_twice(tmpdir):
    file1 = tmpdir.join("test1.lhe")
    file2 = tmpdir.join("test2.lhe")

    file = pylhe.LHEFile.fromfile(TEST_FILE_LHE_v3, with_attributes=True)
    events = file.events
    # single test event
    events = [next(events)]

    # write the file
    file.tofile(file1.strpath)

    # read it again
    lhefile = pylhe.LHEFile.fromfile(file1, with_attributes=True)
    events = lhefile.events

    # write it again
    lhefile.tofile(file2.strpath)

    # assert that the files are the same
    assert file1.read() == file2.read()


def test_write_lhe_gzip(tmpdir):
    file1 = tmpdir.join("test1.lhe.gz")

    file = pylhe.LesHouchesEvents.fromfile(TEST_FILE_LHE_v3, with_attributes=True)
    init = file.init
    assert init is not None
    events = file.events
    # single test event
    events = [next(events)]

    # write the file
    file.tofile(file1.strpath, gz=True)

    # read it again
    init = pylhe.LesHouchesEvents.fromfile(file1.strpath).init


def test_tofile_accepts_pathlib_path(tmp_path):
    """
    Test that tofile() accepts a pathlib.Path object (not just str).
    Previously raised AttributeError because _open_write_file called
    filepath.endswith(...) which does not exist on PosixPath/WindowsPath.
    """
    out_path = tmp_path / "test_output.lhe"

    file = pylhe.LHEFile.fromfile(TEST_FILE_LHE_v3, with_attributes=True)
    events = file.events
    file.events = [next(events)]

    # Must not raise AttributeError
    file.tofile(out_path)

    # Verify the output is valid and readable
    result = pylhe.LHEFile.fromfile(out_path)
    assert result.init is not None
    assert len(list(result.events)) == 1


def test_tofile_accepts_pathlib_path_gz(tmp_path):
    """
    Test that tofile() accepts a pathlib.Path with a .gz suffix and writes
    valid gzip-compressed output.
    """
    out_path = tmp_path / "test_output.lhe.gz"

    file = pylhe.LHEFile.fromfile(TEST_FILE_LHE_v3, with_attributes=True)
    events = file.events
    file.events = [next(events)]

    # Must not raise AttributeError
    file.tofile(out_path)

    # Verify the file is actually gzip-compressed
    with gzip.open(out_path, "rt") as f:
        content = f.read()
    assert "<LesHouchesEvents" in content

    # Verify the output is valid and readable via pylhe
    result = pylhe.LHEFile.fromfile(out_path)
    assert result.init is not None
    assert len(list(result.events)) == 1


def test_write_raises_before_writing_when_both_formats_given(tmp_path):
    """
    Test that LesHouchesEvents.write() raises ValueError BEFORE writing anything
    when both rwgt=True and weights=True are specified.
    Previously the error was only raised per-event, leaving a partial file on disk.
    """
    out_path = tmp_path / "should_not_exist.lhe"

    file = pylhe.LHEFile.fromfile(TEST_FILE_LHE_v3, with_attributes=True)
    events = file.events
    file.events = [next(events)]

    with pytest.raises(
        ValueError, match=r"Cannot specify both rwgt and weights formats simultaneously"
    ):
        file.tofile(out_path, rwgt=True, weights=True)

    # The file must NOT have been created — the error fired before any I/O
    assert not out_path.exists()


def test_write_stream_raises_before_writing_when_both_formats_given():
    """
    Test that LesHouchesEvents.write() raises ValueError on an in-memory stream
    before any bytes are written.
    """
    file = pylhe.LHEFile.fromfile(TEST_FILE_LHE_v3, with_attributes=True)
    events = file.events
    file.events = [next(events)]

    stream = io.StringIO()
    with pytest.raises(
        ValueError, match=r"Cannot specify both rwgt and weights formats simultaneously"
    ):
        file.write(stream, rwgt=True, weights=True)

    # Nothing should have been written to the stream
    assert stream.getvalue() == ""
