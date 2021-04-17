from sys import version_info

import pylhe


def test_top_level_api():
    if version_info > (3, 6):
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
    else:
        print(dir(pylhe))
        assert dir(pylhe)
