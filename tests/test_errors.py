import io
import os
from tempfile import NamedTemporaryFile

import pytest

import pylhe


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
    with pytest.raises(ValueError, match="No <init> block found in the LHE file"):
        pylhe.LHEInit.fromstring(invalid_lhe_content)

    # Test with file-like object
    buffer = io.StringIO(invalid_lhe_content)
    with pytest.raises(ValueError, match="No <init> block found in the LHE file"):
        pylhe.LHEInit.frombuffer(buffer)


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
        with pytest.raises(ValueError, match="No <init> block found in the LHE file"):
            pylhe.read_lhe_init(tmp_file_path)
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

    with pytest.raises(ValueError, match="No <init> block found in the LHE file"):
        pylhe.LHEInit.fromstring(events_only_content)
