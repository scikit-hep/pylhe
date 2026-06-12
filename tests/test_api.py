import subprocess
import sys

import pylhe


def test_lazy_heavy_imports():
    # Importing pylhe must not eagerly import the heavy optional dependencies.
    # Run in a fresh interpreter so other tests' imports do not pollute sys.modules.
    heavy = ("awkward", "vector", "graphviz", "particle")
    code = (
        "import sys, pylhe\n"
        f"heavy = {heavy!r}\n"
        "loaded = [m for m in heavy if m in sys.modules]\n"
        "assert not loaded, loaded\n"
    )
    subprocess.run([sys.executable, "-c", code], check=True)


def test_top_level_api():
    assert dir(pylhe) == [
        "LHEEvent",
        "LHEEventInfo",
        "LHEFile",
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
