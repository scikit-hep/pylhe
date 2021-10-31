import gzip
import os
import subprocess
import xml.etree.ElementTree as ET

import networkx as nx
import tex2pix
from particle.converters.bimap import DirectionalMaps

from ._version import version as __version__
from .awkward import register_awkward, to_awkward

__all__ = [
    "__version__",
    "LHEEvent",
    "LHEEventInfo",
    "LHEFile",
    "LHEInit",
    "LHEParticle",
    "LHEProcInfo",
    "loads",
    "read_lhe",
    "read_lhe_init",
    "read_lhe_with_attributes",
    "read_num_events",
    "register_awkward",
    "to_awkward",
    "visualize",
]


# Python 3.7+
def __dir__():
    return __all__


class LHEFile:
    def __init__(self):
        pass


class LHEEvent:
    def __init__(
        self, eventinfo, particles, weights=None, attributes=None, optional=None
    ):
        self.eventinfo = eventinfo
        self.particles = particles
        self.weights = weights
        self.attributes = attributes
        self.optional = optional
        for p in self.particles:
            p.event = self

    def visualize(self, outputname):
        visualize(self, outputname)


class LHEEventInfo:
    fieldnames = ["nparticles", "pid", "weight", "scale", "aqed", "aqcd"]

    def __init__(self, **kwargs):
        if set(kwargs.keys()) != set(self.fieldnames):
            raise RuntimeError
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def fromstring(cls, string):
        return cls(**dict(zip(cls.fieldnames, map(float, string.split()))))


class LHEParticle:
    fieldnames = [
        "id",
        "status",
        "mother1",
        "mother2",
        "color1",
        "color2",
        "px",
        "py",
        "pz",
        "e",
        "m",
        "lifetime",
        "spin",
    ]

    def __init__(self, **kwargs):
        if set(kwargs.keys()) != set(self.fieldnames):
            raise RuntimeError
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def fromstring(cls, string):
        return cls(**dict(zip(cls.fieldnames, map(float, string.split()))))

    def mothers(self):
        first_idx = int(self.mother1) - 1
        second_idx = int(self.mother2) - 1
        return [
            self.event.particles[idx] for idx in {first_idx, second_idx} if idx >= 0
        ]


class LHEInit(dict):
    """Store the <init> block as dict."""

    fieldnames = [
        "beamA",
        "beamB",
        "energyA",
        "energyB",
        "PDFgroupA",
        "PDFgroupB",
        "PDFsetA",
        "PDFsetB",
        "weightingStrategy",
        "numProcesses",
    ]

    def __init__(self):
        pass

    @classmethod
    def fromstring(cls, string):
        return dict(zip(cls.fieldnames, map(float, string.split())))


class LHEProcInfo(dict):
    """Store the process info block as dict."""

    fieldnames = ["xSection", "error", "unitWeight", "procId"]

    def __init__(self):
        pass

    @classmethod
    def fromstring(cls, string):
        return dict(zip(cls.fieldnames, map(float, string.split())))


def loads():
    pass


def _extract_fileobj(filepath):
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


def read_lhe_init(filepath):
    """
    Read and return the init blocks. This encodes the weight group
    and related things according to https://arxiv.org/abs/1405.1067

    Args:
        filepath: A path-like object or str.

    Returns:
        dict: Dictionary containing the init blocks of the LHE file.
    """
    initDict = {}
    with _extract_fileobj(filepath) as fileobj:
        for event, element in ET.iterparse(fileobj, events=["end"]):
            if element.tag == "init":
                data = element.text.split("\n")[1:-1]
                initDict["initInfo"] = LHEInit.fromstring(data[0])
                initDict["procInfo"] = [LHEProcInfo.fromstring(d) for d in data[1:]]
            if element.tag == "initrwgt":
                initDict["weightgroup"] = {}
                for child in element:
                    # Find all weightgroups
                    if child.tag == "weightgroup" and child.attrib != {}:
                        try:
                            wg_type = child.attrib["type"]
                        except KeyError:
                            print("weightgroup must have attribute 'type'")
                            raise
                        _temp = {"attrib": child.attrib, "weights": {}}
                        # Iterate over all weights in this weightgroup
                        for w in child:
                            if w.tag != "weight":
                                continue
                            try:
                                wg_id = w.attrib["id"]
                            except KeyError:
                                print("weight must have attribute 'id'")
                                raise
                            _temp["weights"][wg_id] = {
                                "attrib": w.attrib,
                                "name": w.text.strip(),
                            }

                        initDict["weightgroup"][wg_type] = _temp
            if element.tag == "event":
                break
    return initDict


def read_lhe(filepath):
    try:
        with _extract_fileobj(filepath) as fileobj:
            for event, element in ET.iterparse(fileobj, events=["end"]):
                if element.tag == "event":
                    data = element.text.strip().split("\n")
                    eventdata, particles = data[0], data[1:]
                    eventinfo = LHEEventInfo.fromstring(eventdata)
                    particles = particles[:int(eventinfo.nparticles)]
                    particle_objs = [LHEParticle.fromstring(p) for p in particles]
                    yield LHEEvent(eventinfo, particle_objs)
    except ET.ParseError as excep:
        print("WARNING. Parse Error:", excep)
        return


def read_lhe_with_attributes(filepath):
    """
    Iterate through file, similar to read_lhe but also set
    weights and attributes.
    """
    try:
        with _extract_fileobj(filepath) as fileobj:
            for event, element in ET.iterparse(fileobj, events=["end"]):
                if element.tag == "event":
                    eventdict = {}
                    data = element.text.strip().split("\n")
                    eventdata, particles = data[0], data[1:]
                    eventdict["eventinfo"] = LHEEventInfo.fromstring(eventdata)
                    eventinfo.nparticles = int(eventinfo.nparticles)
                    eventdict["particles"] = [LHEParticle.fromstring(p) for p in particles[:eventinfo.nparticles]]
                    eventdict["weights"] = {}
                    eventdict["attrib"] = element.attrib
                    eventdict["optional"] = []
                    if len(particles) > eventinfo.nparticles:
                        eventdict["optional"] = [p.strip() for p in eventinfo.nparticles[eventinfo.nparticles:]]
                    for sub in element:
                        if sub.tag == "rwgt":
                            for r in sub:
                                if r.tag == "wgt":
                                    eventdict["weights"][r.attrib["id"]] = float(
                                        r.text.strip()
                                    )
                    # yield eventdict
                    yield LHEEvent(
                        eventdict["eventinfo"],
                        eventdict["particles"],
                        eventdict["weights"],
                        eventdict["attrib"],
                        eventdict["optional"],
                    )
    except ET.ParseError:
        print("WARNING. Parse Error.")
        return


def read_num_events(filepath):
    """
    Moderately efficient way to get the number of events stored in file.
    """
    with _extract_fileobj(filepath) as fileobj:
        return sum(
            element.tag == "event"
            for event, element in ET.iterparse(fileobj, events=["end"])
        )


def visualize(event, outputname):
    """
    Create a PDF with a visualisation of the LHE event record as a directed graph
    """

    # retrieve mapping of PDG ID to particle name as LaTeX string
    _PDGID2LaTeXNameMap, _ = DirectionalMaps(
        "PDGID", "LATEXNAME", converters=(int, str)
    )
    # draw graph
    g = nx.DiGraph()
    for i, p in enumerate(event.particles):
        g.add_node(i, attr_dict=p.__dict__)
        try:
            iid = int(p.id)
            name = _PDGID2LaTeXNameMap[iid]
            texlbl = f"${name}$"
        except KeyError:
            texlbl = str(int(p.id))
        g.nodes[i].update(texlbl=texlbl)
    for i, p in enumerate(event.particles):
        for mom in p.mothers():
            g.add_edge(event.particles.index(mom), i)
    nx.nx_pydot.write_dot(g, "event.dot")

    p = subprocess.Popen(["dot2tex", "event.dot"], stdout=subprocess.PIPE)
    tex = p.stdout.read().decode()
    tex2pix.Renderer(tex).mkpdf(outputname)
    subprocess.check_call(["pdfcrop", outputname, outputname])
    os.remove("event.dot")
