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
        "__version__",
        "loads",
        "read_lhe",
        "read_lhe_init",
        "read_lhe_with_attributes",
        "read_num_events",
        "register_awkward",
        "to_awkward",
    ]


@python37plus_only
def test_awkward_api():
    assert dir(pylhe.awkward) == ["register_awkward", "to_awkward"]


def test_load_version():
    assert pylhe.__version__
