from sys import version_info

import pytest

import pylhe

python37plus_only = pytest.mark.skipif(
    version_info < (3, 7), reason="requires Python3.7+"
)


@python37plus_only
def test_top_level_api():
    assert dir(pylhe) == [
        "LHEEvent",
        "LHEEventInfo",
        "LHEFile",
        "LHEInit",
        "LHEParticle",
        "LHEProcInfo",
        "loads",
        "readLHE",
        "readLHEInit",
        "readLHEWithAttributes",
        "readNumEvents",
        "visualize",
    ]
