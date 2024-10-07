import pylhe


def test_top_level_api():
    assert dir(pylhe) == [
        "LHEEvent",
        "LHEEventInfo",
        "LHEFile",
        "LHEInit",
        "LHEInitInfo",
        "LHEParticle",
        "LHEProcInfo",
        "__version__",
        "read_lhe",
        "read_lhe_file",
        "read_lhe_init",
        "read_lhe_with_attributes",
        "read_num_events",
        "to_awkward",
        "write_lhe_file",
        "write_lhe_file_path",
        "write_lhe_file_string",
        "write_lhe_string",
    ]


def test_awkward_api():
    assert dir(pylhe.awkward) == ["to_awkward"]


def test_load_version():
    assert pylhe.__version__
