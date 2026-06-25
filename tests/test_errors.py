import io
import os
import tempfile
import xml.etree.ElementTree as ET
from tempfile import NamedTemporaryFile

import h5py
import pytest

import pylhe


def test_invalid_root_element_error():
    """Test that ValueError is raised when root element is not <LesHouchesEvents>."""
    invalid_root_content = """<NotLesHouchesEvents version="1.0">
<init>
  2212  2212  6.500000e+03  6.500000e+03  0  0  0  0  3  1
  1.000000e+00  0.000000e+00  1.000000e+00  1
</init>
</NotLesHouchesEvents>"""

    with pytest.raises(ValueError, match=r"Root element is not <LesHouchesEvents>"):
        pylhe.LHEFile.fromstring(invalid_root_content)

    buffer = io.StringIO(invalid_root_content)
    with pytest.raises(ValueError, match=r"Root element is not <LesHouchesEvents>"):
        pylhe.LHEFile.frombuffer(buffer)


def test_missing_init_block_error():
    """Test that ValueError is raised when no <init> block is found in LHE file."""
    # Create an invalid LHE file content without an <init> block
    invalid_lhe_content = """<LesHouchesEvents version="1.0">
<event>
  2      0 +1.0000000e+00  9.11884000e+01 -1.00000000e+00 -1.00000000e+00
       21 -1    0    0  501  502 +0.00000000e+00 +0.00000000e+00 +4.56308892e+02 +4.56308892e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
       21 -1    0    0  502  501 -0.00000000e+00 -0.00000000e+00 -2.24036073e+02 +2.24036073e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
</event>
</LesHouchesEvents>"""

    # Test with string buffer
    with pytest.raises(ValueError, match=r"No <init> block found in the LHE file"):
        pylhe.LHEFile.fromstring(invalid_lhe_content)

    # Test with file-like object
    buffer = io.StringIO(invalid_lhe_content)
    with pytest.raises(ValueError, match=r"No <init> block found in the LHE file"):
        pylhe.LHEFile.frombuffer(buffer)


def test_missing_init_block_error_with_file():
    """Test that ValueError is raised when reading a file without <init> block."""
    # Create an invalid LHE file content without an <init> block
    invalid_lhe_content = """<LesHouchesEvents version="1.0">
<event>
  2      0 +1.0000000e+00  9.11884000e+01 -1.00000000e+00 -1.00000000e+00
       21 -1    0    0  501  502 +0.00000000e+00 +0.00000000e+00 +4.56308892e+02 +4.56308892e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
       21 -1    0    0  502  501 -0.00000000e+00 -0.00000000e+00 -2.24036073e+02 +2.24036073e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
</event>
</LesHouchesEvents>"""

    # Create a temporary file with invalid content
    with NamedTemporaryFile(mode="w", suffix=".lhe", delete=False) as tmp_file:
        tmp_file.write(invalid_lhe_content)
        tmp_file_path = tmp_file.name

    try:
        # Test reading the file through read_lhe_init function
        with pytest.raises(ValueError, match=r"No <init> block found in the LHE file"):
            pylhe.LesHouchesEvents.fromfile(tmp_file_path)
    finally:
        os.unlink(tmp_file_path)


def test_lheh5_row_int_raises_for_missing_columns():
    with pytest.raises(
        KeyError, match=r"None of the requested columns are available: pid, start"
    ):
        pylhe.lheh5._row_int([], {}, "pid", "start")


def test_lheh5_row_float_raises_for_missing_columns():
    with pytest.raises(
        KeyError, match=r"None of the requested columns are available: scale, aqed"
    ):
        pylhe.lheh5._row_float([], {}, "scale", "aqed")


def test_lheh5_row_int_returns_default_for_missing_columns():
    assert pylhe.lheh5._row_int([], {}, "pid", "start", default=7) == 7


def test_lheh5_row_float_returns_default_for_missing_columns():
    assert pylhe.lheh5._row_float([], {}, "scale", "aqed", default=3.5) == 3.5


def test_lheh5_column_names_returns_default_when_attrs_missing(tmp_path):
    path = tmp_path / "missing-column-names.hdf5"

    with h5py.File(path, "w") as h5:
        dataset = h5.create_dataset("rows", data=[[1.0, 2.0]], dtype="f8")

        assert pylhe.lheh5._column_names(dataset, default=("a", "b")) == ["a", "b"]


def test_lheh5_event_scale_returns_default_when_names_missing():
    event = pylhe.LHEEvent(
        eventinfo=pylhe.LHEEventInfo(0, 0, 0.0, 0.0, 0.0, 0.0),
        particles=[],
        scales={"other": 12.0},
    )

    assert pylhe.lheh5._event_scale(event, "fscale", "muf", default=9.5) == 9.5


def test_lheh5_event_trials_returns_zero_for_missing_or_invalid_trials():
    missing_trials_event = pylhe.LHEEvent(
        eventinfo=pylhe.LHEEventInfo(0, 0, 0.0, 0.0, 0.0, 0.0),
        particles=[],
    )
    invalid_trials_event = pylhe.LHEEvent(
        eventinfo=pylhe.LHEEventInfo(0, 0, 0.0, 0.0, 0.0, 0.0),
        particles=[],
        attributes={"trials": "not-a-float"},
    )

    assert pylhe.lheh5._event_trials(missing_trials_event) == 0.0
    assert pylhe.lheh5._event_trials(invalid_trials_event) == 0.0


def test_lheh5_append_rows_returns_early_for_empty_rows(tmp_path):
    path = tmp_path / "empty-append.hdf5"

    with h5py.File(path, "w") as h5:
        dataset = h5.create_dataset(
            "rows",
            shape=(0, 2),
            maxshape=(None, 2),
            dtype="f8",
            chunks=(2, 2),
        )
        pylhe.lheh5._append_rows(dataset, [])

        assert dataset.shape == (0, 2)


def test_missing_init_block_error_with_only_events():
    """Test that ValueError is raised when file contains only events without init."""
    # Create LHE content with events but no init block
    events_only_content = """<LesHouchesEvents version="1.0">
<event>
  2      0 +1.0000000e+00  9.11884000e+01 -1.00000000e+00 -1.00000000e+00
       21 -1    0    0  501  502 +0.00000000e+00 +0.00000000e+00 +4.56308892e+02 +4.56308892e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
       21 -1    0    0  502  501 -0.00000000e+00 -0.00000000e+00 -2.24036073e+02 +2.24036073e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
</event>
<event>
  2      0 +1.0000000e+00  9.11884000e+01 -1.00000000e+00 -1.00000000e+00
       21 -1    0    0  501  502 +0.00000000e+00 +0.00000000e+00 +4.56308892e+02 +4.56308892e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
       21 -1    0    0  502  501 -0.00000000e+00 -0.00000000e+00 -2.24036073e+02 +2.24036073e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
</event>
</LesHouchesEvents>"""

    with pytest.raises(ValueError, match=r"No <init> block found in the LHE file"):
        pylhe.LHEFile.fromstring(events_only_content)


def test_lheinit_fromcontext_no_init_block_error():
    """Test that LHEInit._fromcontext raises when the parse context contains no <init> block."""
    invalid_lhe_content = """<LesHouchesEvents version="1.0">
<header>
<MGGenerationInfo>
#  Number of Events        :       1
</MGGenerationInfo>
</header>
</LesHouchesEvents>"""

    context = ET.iterparse(io.StringIO(invalid_lhe_content), events=["start", "end"])
    _, root = next(context)

    with pytest.raises(ValueError, match=r"No <init> block found in the LHE file\."):
        pylhe.LHEInit._fromcontext(root, context)


def test_empty_init_block_error():
    """Test that ValueError is raised when <init> block has no text content."""
    # Create LHE content with an empty <init> block
    empty_init_content = """<LesHouchesEvents version="1.0">
<init></init>
<event>
  2      0 +1.0000000e+00  9.11884000e+01 -1.00000000e+00 -1.00000000e+00
       21 -1    0    0  501  502 +0.00000000e+00 +0.00000000e+00 +4.56308892e+02 +4.56308892e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
       21 -1    0    0  502  501 -0.00000000e+00 -0.00000000e+00 -2.24036073e+02 +2.24036073e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
</event>
</LesHouchesEvents>"""

    # Test with string buffer
    with pytest.raises(ValueError, match=r"<init> block has no text"):
        pylhe.LHEFile.fromstring(empty_init_content)

    # Test with file-like object
    buffer = io.StringIO(empty_init_content)
    with pytest.raises(ValueError, match=r"<init> block has no text"):
        pylhe.LHEFile.frombuffer(buffer)


def test_initrwgt_top_level_weight_without_id_error():
    """Test that AttributeError is raised when a top-level <initrwgt><weight> has attributes but no id."""
    invalid_initrwgt_content = """<LesHouchesEvents version="3.0">
<header>
<initrwgt>
  <weight bogus="1">central</weight>
</initrwgt>
</header>
<init>
  2212  2212  6.500000e+03  6.500000e+03  0  0  0  0  3  1
  1.000000e+00  0.000000e+00  1.000000e+00  1
</init>
</LesHouchesEvents>"""

    with pytest.raises(AttributeError, match=r"weight must have attribute 'id'"):
        pylhe.LHEFile.fromstring(invalid_initrwgt_content)


def test_empty_event_block_error():
    """Test that ValueError is raised when <event> block has no text content."""
    # Create LHE content with valid init but empty event block
    empty_event_content = """<LesHouchesEvents version="1.0">
<init>
  2212  2212  6.500000e+03  6.500000e+03  0  0  0  0  3  1
  1.000000e+00  0.000000e+00  1.000000e+00  1
</init>
<event></event>
</LesHouchesEvents>"""

    # Test reading events with empty event block
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lhe", delete=False) as tmp_file:
        tmp_file.write(empty_event_content)
        tmp_file_path = tmp_file.name

    try:
        with pytest.raises(ValueError, match=r"<event> block has no text"):
            list(
                pylhe.LesHouchesEvents.fromfile(
                    tmp_file_path, with_attributes=False
                ).events
            )
    finally:
        os.unlink(tmp_file_path)


def test_empty_weights_block_error():
    """Test that ValueError is raised when <weights> block has no text content."""
    # Create LHE content with valid init and event but empty weights block
    empty_weights_content = """<LesHouchesEvents version="1.0">
<init>
  2212  2212  6.500000e+03  6.500000e+03  0  0  0  0  3  1
  1.000000e+00  0.000000e+00  1.000000e+00  1
</init>
<event>
  2      0 +1.0000000e+00  9.11884000e+01 -1.00000000e+00 -1.00000000e+00
       21 -1    0    0  501  502 +0.00000000e+00 +0.00000000e+00 +4.56308892e+02 +4.56308892e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
       21 -1    0    0  502  501 -0.00000000e+00 -0.00000000e+00 -2.24036073e+02 +2.24036073e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
<weights></weights>
</event>
</LesHouchesEvents>"""

    # Test reading events with empty weights block
    with NamedTemporaryFile(mode="w", suffix=".lhe", delete=False) as tmp_file:
        tmp_file.write(empty_weights_content)
        tmp_file_path = tmp_file.name

    try:
        with pytest.raises(ValueError, match=r"<weights> block has no text"):
            list(pylhe.LesHouchesEvents.fromfile(tmp_file_path).events)
    finally:
        os.unlink(tmp_file_path)


def test_weights_block_without_initrwgt_error():
    """Test that ValueError is raised when <weights> is present but <initrwgt> is missing from the header."""
    weights_without_initrwgt_content = """<LesHouchesEvents version="1.0">
<header>
<MGGenerationInfo>
#  Number of Events        :       1
</MGGenerationInfo>
</header>
<init>
  2212  2212  6.500000e+03  6.500000e+03  0  0  0  0  3  1
  1.000000e+00  0.000000e+00  1.000000e+00  1
</init>
<event>
  2      0 +1.0000000e+00  9.11884000e+01 -1.00000000e+00 -1.00000000e+00
       21 -1    0    0  501  502 +0.00000000e+00 +0.00000000e+00 +4.56308892e+02 +4.56308892e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
       21 -1    0    0  502  501 -0.00000000e+00 -0.00000000e+00 -2.24036073e+02 +2.24036073e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
<weights>
 1.0000000e+00
</weights>
</event>
</LesHouchesEvents>"""

    with NamedTemporaryFile(mode="w", suffix=".lhe", delete=False) as tmp_file:
        tmp_file.write(weights_without_initrwgt_content)
        tmp_file_path = tmp_file.name

    try:
        with pytest.raises(
            ValueError,
            match=r"<initrwgt> is required to parse <weights> block but not found in the header",
        ):
            list(pylhe.LesHouchesEvents.fromfile(tmp_file_path).events)
    finally:
        os.unlink(tmp_file_path)


def test_weights_block_more_entries_than_initrwgt_error():
    """Test that ValueError is raised when <weights> has more entries than <initrwgt> declares."""
    too_many_weights_content = """<LesHouchesEvents version="3.0">
<header>
<initrwgt>
<weightgroup name="scale_variation" combine="envelope">
<weight id="1001"> mur=1 muf=1 </weight>
</weightgroup>
</initrwgt>
</header>
<init>
  2212  2212  6.500000e+03  6.500000e+03  0  0  0  0  3  1
  1.000000e+00  0.000000e+00  1.000000e+00  1
</init>
<event>
  2      0 +1.0000000e+00  9.11884000e+01 -1.00000000e+00 -1.00000000e+00
       21 -1    0    0  501  502 +0.00000000e+00 +0.00000000e+00 +4.56308892e+02 +4.56308892e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
       21 -1    0    0  502  501 -0.00000000e+00 -0.00000000e+00 -2.24036073e+02 +2.24036073e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
<weights>
 1.0000000e+00 2.0000000e+00
</weights>
</event>
</LesHouchesEvents>"""

    with NamedTemporaryFile(mode="w", suffix=".lhe", delete=False) as tmp_file:
        tmp_file.write(too_many_weights_content)
        tmp_file_path = tmp_file.name

    try:
        with pytest.raises(
            ValueError,
            match=r"<weights> block has 2 entries but <initrwgt> declares only 1",
        ):
            list(pylhe.LesHouchesEvents.fromfile(tmp_file_path).events)
    finally:
        os.unlink(tmp_file_path)


def test_empty_wgt_block_error():
    """Test that ValueError is raised when <wgt> block has no text content."""
    # Create LHE content with valid init and event but empty wgt block
    empty_wgt_content = """<LesHouchesEvents version="1.0">
<init>
  2212  2212  6.500000e+03  6.500000e+03  0  0  0  0  3  1
  1.000000e+00  0.000000e+00  1.000000e+00  1
</init>
<event>
  2      0 +1.0000000e+00  9.11884000e+01 -1.00000000e+00 -1.00000000e+00
       21 -1    0    0  501  502 +0.00000000e+00 +0.00000000e+00 +4.56308892e+02 +4.56308892e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
       21 -1    0    0  502  501 -0.00000000e+00 -0.00000000e+00 -2.24036073e+02 +2.24036073e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
<rwgt>
<wgt id="1001"></wgt>
</rwgt>
</event>
</LesHouchesEvents>"""

    # Test reading events with empty wgt block
    with NamedTemporaryFile(mode="w", suffix=".lhe", delete=False) as tmp_file:
        tmp_file.write(empty_wgt_content)
        tmp_file_path = tmp_file.name

    try:
        with pytest.raises(ValueError, match=r"<wgt> block has no text"):
            list(pylhe.LesHouchesEvents.fromfile(tmp_file_path).events)
    finally:
        os.unlink(tmp_file_path)


def test_whitespace_only_wgt_block_error():
    """Test that ValueError is raised when <wgt> block has only whitespace content."""
    # Create LHE content with valid init and event but whitespace-only wgt block
    whitespace_wgt_content = """<LesHouchesEvents version="1.0">
<init>
  2212  2212  6.500000e+03  6.500000e+03  0  0  0  0  3  1
  1.000000e+00  0.000000e+00  1.000000e+00  1
</init>
<event>
  2      0 +1.0000000e+00  9.11884000e+01 -1.00000000e+00 -1.00000000e+00
       21 -1    0    0  501  502 +0.00000000e+00 +0.00000000e+00 +4.56308892e+02 +4.56308892e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
       21 -1    0    0  502  501 -0.00000000e+00 -0.00000000e+00 -2.24036073e+02 +2.24036073e+02 +0.00000000e+00 0.0000e+00 9.0000e+00
<rwgt>
<wgt id="1001">   </wgt>
</rwgt>
</event>
</LesHouchesEvents>"""

    # Test reading events with whitespace-only wgt block
    with NamedTemporaryFile(mode="w", suffix=".lhe", delete=False) as tmp_file:
        tmp_file.write(whitespace_wgt_content)
        tmp_file_path = tmp_file.name

    try:
        with pytest.raises(
            ValueError,
            match=r"could not convert string to float|invalid literal for float",
        ):
            list(pylhe.LesHouchesEvents.fromfile(tmp_file_path).events)
    finally:
        os.unlink(tmp_file_path)


def test_count_events_parse_error():
    """Test that ParseError warning is issued and -1 returned when counting events in malformed LHE file."""
    # Create a temporary file with invalid XML content
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lhe", delete=True) as f:
        # Write invalid XML that will cause a parse error
        f.write('<LesHouchesEvents version="3.0">\n')
        f.write("<init>\n")
        f.write("invalid xml content without proper closing\n")
        # Missing </init> and </LesHouchesEvents> tags

        f.flush()

        # Test that a RuntimeWarning is issued and -1 is returned
        with pytest.warns(RuntimeWarning, match=r"Parse Error:"):
            assert pylhe.LHEFile.count_events(f.name) == -1


def test_fromfile_parse_error():
    """Test that ParseError warning is issued when loading malformed LHE file with fromfile."""
    # Create a temporary file with invalid XML content
    with tempfile.NamedTemporaryFile(mode="w", suffix=".lhe", delete=True) as f:
        # Write invalid XML that will cause a parse error
        f.write('<LesHouchesEvents version="3.0">\n')
        f.write("<init>\n")
        f.write("invalid xml content without proper closing\n")
        # Missing </init> and </LesHouchesEvents> tags

        f.flush()

        # Test that a RuntimeWarning is issued when trying to load the malformed file
        # and potentially a ValueError if the generator stops without yielding
        with (
            pytest.warns(RuntimeWarning, match=r"Parse Error:"),
            pytest.raises(
                ValueError,
                match=r"No or faulty <header>/<init> block found in the LHE file",
            ),
        ):
            pylhe.LHEFile.fromfile(f.name)


def test_event_mother_indices_out_of_range_error():
    """Test that IndexError is raised when a particle references a missing mother."""
    event = pylhe.LHEEvent(
        eventinfo=pylhe.LHEEventInfo(
            nparticles=1, pid=1, weight=1.0, scale=100.0, aqed=0.007, aqcd=0.1
        ),
        particles=[
            pylhe.LHEParticle(
                id=11,
                status=1,
                mother1=2,
                mother2=0,
                color1=0,
                color2=0,
                px=0.0,
                py=0.0,
                pz=1.0,
                e=1.0,
                m=0.0,
                lifetime=0.0,
                spin=9.0,
            )
        ],
    )

    with pytest.raises(
        IndexError,
        match=r"Mother index 2 out of range for event with 1 particles\.",
    ):
        event.mother_indices(event.particles[0])
