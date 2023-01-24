import gzip
import xml.etree.ElementTree as ET

import graphviz
from particle import latex_to_html_name
from particle.converters.bimap import DirectionalMaps
from particle.exceptions import MatchingIDNotFound

from pylhe._version import version as __version__
from pylhe.awkward import register_awkward, to_awkward

__all__ = [
    "__version__",
    "LHEEvent",
    "LHEEventInfo",
    "LHEFile",
    "LHEInit",
    "LHEParticle",
    "LHEProcInfo",
    "read_lhe",
    "read_lhe_init",
    "read_lhe_with_attributes",
    "read_num_events",
    "register_awkward",
    "to_awkward",
]


# Python 3.7+
def __dir__():
    return __all__


# retrieve mapping of PDG ID to particle name as LaTeX string
_PDGID2LaTeXNameMap, _ = DirectionalMaps("PDGID", "LATEXNAME", converters=(int, str))


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
        self._graph = None

    @property
    def graph(self):
        """
        Get the `graphviz.Digraph` object.
        The user now has full control ...

        E.g., see the source with my_LHEEvent_instance.graph.source.

        When not in notebooks the graph can easily be visualized with the
        `graphviz.Digraph.render` or `graphviz.Digraph.view` functions, e.g.:
        my_LHEEvent_instance.graph.render(filename="test", format="pdf", view=True, cleanup=True)
        """
        if self._graph is None:
            self._build_graph()
        return self._graph

    def _build_graph(self):
        """
        Navigate the particles in the event and produce a Digraph in the DOT language.
        """

        def safe_html_name(name):
            """
            Get a safe HTML name from the LaTex name.
            """
            try:
                return latex_to_html_name(name)
            except Exception:
                return name

        self._graph = graphviz.Digraph()
        for i, p in enumerate(self.particles):
            try:
                iid = int(p.id)
                name = _PDGID2LaTeXNameMap[iid]
                texlbl = f"${name}$"
                label = f'<<table border="0" cellspacing="0" cellborder="0"><tr><td>{safe_html_name(name)}</td></tr></table>>'
            except MatchingIDNotFound:
                texlbl = str(int(p.id))
                label = f'<<table border="0" cellspacing="0" cellborder="0"><tr><td>{texlbl}</td></tr></table>>'
            self._graph.node(
                str(i), label=label, attr_dict=str(p.__dict__), texlbl=texlbl
            )
        for i, p in enumerate(self.particles):
            for mom in p.mothers():
                self._graph.edge(str(self.particles.index(mom)), str(i))

    def _repr_mimebundle_(
        self,
        include=None,
        exclude=None,
        **kwargs,
    ):
        """
        IPython display helper.
        """
        try:
            return self.graph._repr_mimebundle_(
                include=include, exclude=exclude, **kwargs
            )
        except AttributeError:
            return {"image/svg+xml": self.graph._repr_svg_()}  # for graphviz < 0.19


class LHEEventInfo:
    fieldnames = ["nparticles", "pid", "weight", "scale", "aqed", "aqcd"]

    def __init__(self, **kwargs):
        if set(kwargs.keys()) != set(self.fieldnames):
            raise RuntimeError(
                f"LHEEventInfo constructor expects fields {self.fieldnames}! Got {kwargs.keys()}."
            )
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
            raise RuntimeError(
                f"LHEParticle constructor expects fields {self.fieldnames}! Got {kwargs.keys()}."
            )
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
        for event, element in ET.iterparse(fileobj, events=["start", "end"]):
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
                            try:
                                wg_type = child.attrib["name"]
                            except KeyError:
                                print(
                                    "weightgroup must have attribute 'type' or 'name'"
                                )
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
            if element.tag == "LesHouchesEvents":
                initDict["LHEVersion"] = float(element.attrib["version"])
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
                    particles = particles[: int(eventinfo.nparticles)]
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
    except ET.ParseError as excep:
        print("WARNING. Parse Error:", excep)
        return


def read_num_events(filepath):
    """
    Moderately efficient way to get the number of events stored in a file.
    """
    try:
        with _extract_fileobj(filepath) as fileobj:
            return sum(
                element.tag == "event"
                for event, element in ET.iterparse(fileobj, events=["end"])
            )
    except ET.ParseError as excep:
        print("WARNING. Parse Error:", excep)
        return -1
