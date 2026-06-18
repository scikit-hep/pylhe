import pylhe


def test_top_level_api():
    assert dir(pylhe) == [
        "LHEEvent",
        "LHEEventInfo",
        "LHEFileFormat",
        "LHEFormat",
        "LHEGenerator",
        "LHEHeader",
        "LHEInit",
        "LHEInitInfo",
        "LHEInitRWGTWeight",
        "LHEInitRWGTWeightGroup",
        "LHEOutputFile",
        "LHEParticle",
        "LHEProcInfo",
        "LHEWeightsFormat",
        "__version__",
        "to_awkward",
    ]


def test_awkward_api():
    assert dir(pylhe.awkward) == ["to_awkward"]


def test_load_version():
    assert pylhe.__version__
