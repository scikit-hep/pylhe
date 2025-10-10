"""
Python interface to read Les Houches Event (LHE) files.
"""

from pylhe._version import version as __version__
from pylhe.io import (
    read_lhe,
    read_lhe_file,
    read_lhe_init,
    read_lhe_with_attributes,
    read_num_events,
    write_lhe_file,
    write_lhe_file_path,
    write_lhe_file_string,
    write_lhe_string,
)
from pylhe.lhe import (
    LHEEvent,
    LHEEventInfo,
    LHEFile,
    LHEInit,
    LHEInitInfo,
    LHEParticle,
    LHEProcInfo,
    LHEWeightGroup,
    LHEWeightInfo,
)

from .awkward import to_awkward

__all__ = [
    "LHEEvent",
    "LHEEventInfo",
    "LHEFile",
    "LHEInit",
    "LHEInitInfo",
    "LHEParticle",
    "LHEProcInfo",
    "LHEWeightGroup",
    "LHEWeightInfo",
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


def __dir__() -> list[str]:
    return __all__
