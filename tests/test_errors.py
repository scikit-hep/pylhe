import io
import os
import tempfile
import xml.etree.ElementTree as ET
from tempfile import NamedTemporaryFile

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


def test_event_tolhe_both_formats_error():
    """Test that ValueError is raised when both rwgt and weights formats are specified simultaneously."""
    # Create a simple LHEEvent instance for testing
    eventinfo = pylhe.LHEEventInfo(
        nparticles=2, pid=1, weight=1.0, scale=100.0, aqed=0.007, aqcd=0.1
    )

    particles = [
        pylhe.LHEParticle(
            id=21,
            status=-1,
            mother1=0,
            mother2=0,
            color1=501,
            color2=502,
            px=0.0,
            py=0.0,
            pz=456.3,
            e=456.3,
            m=0.0,
            lifetime=0.0,
            spin=9.0,
        ),
        pylhe.LHEParticle(
            id=21,
            status=-1,
            mother1=0,
            mother2=0,
            color1=502,
            color2=501,
            px=0.0,
            py=0.0,
            pz=-224.0,
            e=224.0,
            m=0.0,
            lifetime=0.0,
            spin=9.0,
        ),
    ]

    event = pylhe.LHEEvent(
        eventinfo=eventinfo, particles=particles, weights={"1001": 1.5, "1002": 0.8}
    )

    # Test that specifying both rwgt=True and weights=True raises ValueError
    with pytest.raises(
        ValueError, match=r"Cannot specify both rwgt and weights formats simultaneously"
    ):
        event.tolhe(rwgt=True, weights=True)
