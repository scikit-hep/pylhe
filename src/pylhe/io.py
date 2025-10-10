"""
Functions to read and write LHE files.
"""

import gzip
import io
import os
import warnings
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from typing import Any, TextIO, Union

from pylhe.lhe import LHEEvent, LHEEventInfo, LHEFile, LHEInit, LHEParticle

PathLike = Union[str, bytes, os.PathLike[str], os.PathLike[bytes]]


def read_lhe_file(filepath: PathLike, with_attributes: bool = True) -> LHEFile:
    """
    Read an LHE file and return an LHEFile object.
    """
    lheinit = read_lhe_init(filepath)
    lheevents = (
        read_lhe_with_attributes(filepath) if with_attributes else read_lhe(filepath)
    )
    return LHEFile(init=lheinit, events=lheevents)


def _extract_fileobj(filepath: PathLike) -> Union[io.BufferedReader, gzip.GzipFile]:
    """
    Checks to see if a file is compressed, and if so, extract it with gzip
    so that the uncompressed file can be returned.
    It returns a file object containing XML data that will be ingested by
    ``xml.etree.ElementTree.iterparse``.

    Args:
        filepath: A path-like object or str.

    Returns:
        _io.BufferedReader or gzip.GzipFile: A file object containing XML data.
    """
    with open(filepath, "rb") as gzip_file:
        header = gzip_file.read(2)
    gzip_magic_number = b"\x1f\x8b"

    return (
        gzip.GzipFile(filepath) if header == gzip_magic_number else open(filepath, "rb")
    )


def read_lhe_init(filepath: PathLike) -> LHEInit:
    """
    Read and return the init blocks. This encodes the weight group
    and related things according to https://arxiv.org/abs/1405.1067

    Args:
        filepath: A path-like object or str.

    Returns:
        dict: Dictionary containing the init blocks of the LHE file.
    """
    with _extract_fileobj(filepath) as fileobj:
        return LHEInit.frombuffer(fileobj)


def read_lhe(filepath: PathLike) -> Iterable[LHEEvent]:
    """
    Read and yield the events in the LHE file.
    """
    try:
        with _extract_fileobj(filepath) as fileobj:
            context = ET.iterparse(fileobj, events=["start", "end"])
            _, root = next(context)  # Get the root element
            for event, element in context:
                if event == "end" and element.tag == "event":
                    data = element.text.strip().split("\n")
                    eventdata, particles = data[0], data[1:]
                    eventinfo = LHEEventInfo.fromstring(eventdata)
                    particles = particles[: int(eventinfo.nparticles)]
                    particle_objs = [LHEParticle.fromstring(p) for p in particles]
                    yield LHEEvent(eventinfo, particle_objs)
                    # Clear the element to free memory
                    element.clear()
                    # Root tracks sub-elements -> clear all sub-elements
                    root.clear()
    except ET.ParseError as excep:
        print("WARNING. Parse Error:", excep)
        return


def _get_index_to_id_map(init: LHEInit) -> dict[int, str]:
    """
    Produce a dictionary to map weight indices to the id of the weight.

    It is used for LHE files where there is only a list of weights per event.
    This dictionary is then used to map the list of weights to their weight id.
    Ideally, this needs to be done only once and the dictionary can be reused.

    Args:
        init (LHEInit): init block as returned by read_lhe_init

    Returns:
        dict: {weight index: weight id}
    """
    ret = {}
    for wg in init.weightgroup.values():
        for id, w in wg.weights.items():
            ret[w.index] = id
    return ret


def read_lhe_with_attributes(filepath: PathLike) -> Iterable[LHEEvent]:
    """
    Iterate through file, similar to read_lhe but also set
    weights and attributes.
    """
    index_map = None
    try:
        with _extract_fileobj(filepath) as fileobj:
            context = ET.iterparse(fileobj, events=["start", "end"])
            _, root = next(context)  # Get the root element
            for event, element in context:
                if event == "end" and element.tag == "event":
                    eventdict: dict[str, Any] = {}
                    data = element.text.strip().split("\n")
                    eventdata, particles = data[0], data[1:]
                    eventdict["eventinfo"] = LHEEventInfo.fromstring(eventdata)
                    eventdict["particles"] = []
                    eventdict["weights"] = {}
                    eventdict["attrib"] = element.attrib
                    eventdict["optional"] = []
                    for p in particles:
                        if not p.strip().startswith("#"):
                            eventdict["particles"] += [LHEParticle.fromstring(p)]
                        else:
                            eventdict["optional"].append(p.strip())
                    for sub in element:
                        if sub.tag == "weights":
                            if not index_map:
                                index_map = _get_index_to_id_map(
                                    read_lhe_init(filepath)
                                )
                            for i, w in enumerate(sub.text.split()):
                                if w and index_map[i] not in eventdict["weights"]:
                                    eventdict["weights"][index_map[i]] = float(w)
                        if sub.tag == "rwgt":
                            for r in sub:
                                if r.tag == "wgt":
                                    eventdict["weights"][r.attrib["id"]] = float(
                                        r.text.strip()
                                    )
                    # yield eventdict
                    yield LHEEvent(
                        eventinfo=eventdict["eventinfo"],
                        particles=eventdict["particles"],
                        weights=eventdict["weights"],
                        attributes=eventdict["attrib"],
                        optional=eventdict["optional"],
                    )
                    # Clear processed elements
                    element.clear()
                    # Root tracks sub-elements -> clear all sub-elements
                    root.clear()
    except ET.ParseError as excep:
        print("WARNING. Parse Error:", excep)
        return


def read_num_events(filepath: PathLike) -> int:
    """
    Moderately efficient way to get the number of events stored in a file.
    """
    try:
        with _extract_fileobj(filepath) as fileobj:
            context = ET.iterparse(fileobj, events=["start", "end"])
            _, root = next(context)  # Get the root element
            count = 0
            for event, element in context:
                if event == "end" and element.tag == "event":
                    count += 1
                    # Clear the element to free memory
                    element.clear()
                    # Root tracks sub-elements -> clear all sub-elements
                    root.clear()
            return count
    except ET.ParseError as excep:
        print("WARNING. Parse Error:", excep)
        return -1


def write_lhe_file_string(
    lhefile: LHEFile, rwgt: bool = True, weights: bool = False
) -> str:
    """
    Return the LHE file as a string.
    """
    return lhefile.tolhe(rwgt=rwgt, weights=weights)


def write_lhe_string(
    lheinit: LHEInit,
    lheevents: Iterable[LHEEvent],
    rwgt: bool = True,
    weights: bool = False,
) -> str:
    """
    Return the LHE file as a string.

    .. deprecated:: 0.9.1
       Instead of :func:`~pylhe.write_lhe_string` use :func:`~pylhe.write_lhe_file_string`
    .. warning:: :func:`~pylhe.write_lhe_string` will be removed in
     ``pylhe`` ``v0.11.0``.
    """
    warnings.warn(
        "`write_lhe_string` is deprecated and will be removed in a future version. "
        "Use `write_lhe_file_string` instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return write_lhe_file_string(
        LHEFile(init=lheinit, events=lheevents), rwgt=rwgt, weights=weights
    )


def _open_write_file(filepath: str, gz: bool = False) -> TextIO:
    if filepath.endswith((".gz", ".gzip")) or gz:
        return gzip.open(filepath, "wt")
    return open(filepath, "w")


def write_lhe_file_path(
    lhefile: LHEFile,
    filepath: str,
    gz: bool = False,
    rwgt: bool = True,
    weights: bool = False,
) -> None:
    """
    Write the LHE file.
    """
    # if filepath suffix is gz, write as gz
    with _open_write_file(filepath, gz=gz) as f:
        lhefile.write(f, rwgt=rwgt, weights=weights)


def write_lhe_file(
    lheinit: LHEInit,
    lheevents: Iterable[LHEEvent],
    filepath: str,
    gz: bool = False,
    rwgt: bool = True,
    weights: bool = False,
) -> None:
    """
    Write the LHE file.

    .. deprecated:: 0.9.1
       Instead of :func:`~pylhe.write_lhe_file` use :func:`~pylhe.write_lhe_file_path`
    .. warning:: :func:`~pylhe.write_lhe_file` will be removed in
     ``pylhe`` ``v0.11.0``.
    """
    warnings.warn(
        "`write_lhe_file` is deprecated and will be removed in a future version. "
        "Use `write_lhe_file_path` instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    write_lhe_file_path(
        LHEFile(init=lheinit, events=lheevents),
        filepath,
        gz=gz,
        rwgt=rwgt,
        weights=weights,
    )
