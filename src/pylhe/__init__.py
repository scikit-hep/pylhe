import os
import xml.etree.ElementTree as ET
import networkx as nx
import tex2pix
import subprocess
from particle.converters.bimap import DirectionalMaps


class LHEFile(object):
    def __init__(self):
        pass


class LHEEvent(object):
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


class LHEEventInfo(object):
    fieldnames = ["nparticles", "pid", "weight", "scale", "aqed", "aqcd"]

    def __init__(self, **kwargs):
        if not set(kwargs.keys()) == set(self.fieldnames):
            raise RuntimeError
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def fromstring(cls, string):
        return cls(**dict(zip(cls.fieldnames, map(float, string.split()))))


class LHEParticle(object):
    fieldnames = fieldnames = [
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
        if not set(kwargs.keys()) == set(self.fieldnames):
            raise RuntimeError
        for k, v in kwargs.items():
            setattr(self, k, v)

    @classmethod
    def fromstring(cls, string):
        obj = cls(**dict(zip(cls.fieldnames, map(float, string.split()))))
        return obj

    def mothers(self):
        mothers = []
        first_idx = int(self.mother1) - 1
        second_idx = int(self.mother2) - 1
        for idx in set([first_idx, second_idx]):
            if idx >= 0:
                mothers.append(self.event.particles[idx])
        return mothers


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


def readLHEInit(thefile):
    """
    Read the init blocks. Return dict. This encodes the weight group
    and related things according to https://arxiv.org/abs/1405.1067
    This function returns a dict.
    """
    initDict = {}
    for event, element in ET.iterparse(thefile, events=["end"]):
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
                    _temp = {"attrib": child.attrib}
                    _temp["weights"] = {}
                    # Iterate over all weights in this weightgroup
                    for w in child:
                        if not w.tag == "weight":
                            continue
                        try:
                            wg_id = w.attrib["id"]
                        except KeyError:
                            print("weight must have attribute 'id'")
                            raise
                        _w = {"attrib": w.attrib}
                        _w["name"] = w.text.strip()
                        _temp["weights"][wg_id] = _w

                    initDict["weightgroup"][wg_type] = _temp
        if element.tag == "event":
            break
    return initDict


def readLHE(thefile):
    try:
        for event, element in ET.iterparse(thefile, events=["end"]):
            if element.tag == "event":
                data = element.text.split("\n")[1:-1]
                eventdata, particles = data[0], data[1:]
                eventinfo = LHEEventInfo.fromstring(eventdata)
                particle_objs = []
                for p in particles:
                    particle_objs += [LHEParticle.fromstring(p)]
                yield LHEEvent(eventinfo, particle_objs)
    except ET.ParseError as e:
        print("WARNING. Parse Error:", e)
        return


def readLHEWithAttributes(thefile):
    """
    Iterate through file, similar to readLHE but also set
    weights and attributes.
    """
    try:
        for event, element in ET.iterparse(thefile, events=["end"]):
            if element.tag == "event":
                eventdict = {}
                data = element.text.split("\n")[1:-1]
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


def readNumEvents(file):
    """
    Moderately efficent way to get the number of events stored in file.
    """
    N = 0
    for event, element in ET.iterparse(file, events=["end"]):
        if element.tag == "event":
            N += 1
    return N


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
            texlbl = "${}$".format(name)
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
