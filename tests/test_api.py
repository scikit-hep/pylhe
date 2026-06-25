import pylhe


def test_top_level_api():
    assert dir(pylhe) == [
        "DEFAULT_FORMAT",
        "GZ_FORMAT",
        "LHEEvent",
        "LHEEventInfo",
        "LHEFile",
        "LHEFileFormat",
        "LHEGenerator",
        "LHEHDF5Format",
        "LHEHeader",
        "LHEInit",
        "LHEInitInfo",
        "LHEInitRWGTWeight",
        "LHEInitRWGTWeightGroup",
        "LHEOutputFormat",
        "LHEParticle",
        "LHEProcInfo",
        "LHEWeightFormat",
        "LHEXMLFormat",
        "RWGT_FORMAT",
        "RWGT_GZ_FORMAT",
        "WEIGHTS_FORMAT",
        "WEIGHTS_GZ_FORMAT",
        "__version__",
        "to_awkward",
    ]


def test_awkward_api():
    assert dir(pylhe.awkward) == ["to_awkward"]


def test_load_version():
    assert pylhe.__version__
