import pylhe


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
