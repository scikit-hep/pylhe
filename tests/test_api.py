import pylhe


def test_top_level_api():
    assert dir(pylhe) == [
        "DEFAULT_FORMAT",
        "GZ_FORMAT",
        "HDF5_FORMAT",
        "HDF5_GZ_FORMAT",
        "LHEEvent",
        "LHEEventInfo",
        "LHEFile",
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
        "from_numpy",
        "to_awkward",
        "to_numpy",
    ]


def test_awkward_api():
    assert dir(pylhe.awkward) == ["to_awkward"]


def test_numpy_api():
    assert dir(pylhe.numpy) == [
        "EVENT_DTYPE",
        "PARTICLE_DTYPE",
        "from_numpy",
        "to_numpy",
    ]


def test_load_version():
    assert pylhe.__version__
