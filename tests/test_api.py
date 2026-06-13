import pylhe


def test_top_level_api():
    assert dir(pylhe) == [
        "LHEEvent",
        "LHEEventInfo",
        "LHEFile",
        "LHEFormat",
        "LHEGenerator",
        "LHEHeader",
        "LHEInit",
        "LHEInitInfo",
        "LHEInitRWGTWeight",
        "LHEInitRWGTWeightGroup",
        "LHEParticle",
        "LHEProcInfo",
        "__version__",
        "to_awkward",
    ]


def test_awkward_api():
    assert dir(pylhe.awkward) == ["to_awkward"]


def test_load_version():
    assert pylhe.__version__
