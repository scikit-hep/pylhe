"""
Python interface to read Les Houches Event (LHE) files.
"""

import gzip
import io
import warnings
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass, fields
from typing import Optional

import graphviz
from particle import latex_to_html_name
from particle.converters.bimap import DirectionalMaps
from particle.exceptions import MatchingIDNotFound

from pylhe._version import version as __version__
from pylhe.awkward import to_awkward

__all__ = [
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


def __dir__():
    return __all__


# retrieve mapping of PDG ID to particle name as LaTeX string
_PDGID2LaTeXNameMap, _ = DirectionalMaps("PDGID", "LATEXNAME", converters=(int, str))


@dataclass
class LHEEvent:
    """
    Store a single event in the LHE format.
    """

    eventinfo: "LHEEventInfo"
    """Event information"""
    particles: list["LHEParticle"]
    """List of particles in the event"""
    weights: Optional[dict] = None
    """Event weights"""
    attributes: Optional[dict] = None
    """Event attributes"""
    optional: Optional[list] = None
    """Optional '#' comments stored in the event"""
    _graph: Optional[graphviz.Digraph] = None
    """Stores the graph representation of the event generated after first access of the property `lheevent.graph`"""

    def __post_init__(self):
        """Set up bidirectional relationship between event and particles."""
        for p in self.particles:
            p.event = self

    def tolhe(self, rwgt=True, weights=False):
        """
        Return the event as a string in LHE format.

        Args:
            rwgt (bool): Include the weights in the 'rwgt' format.
            weights (bool): Include the weights in the 'weights' format.

        Returns:
            str: The event as a string in LHE format.
        """
        sweights = ""
        if rwgt and self.weights:
            sweights = "<rwgt>\n"
            for k, v in self.weights.items():
                sweights += f" <wgt id='{k}'>{v:11.4e}</wgt>\n"
            sweights += "</rwgt>\n"
        if weights and self.weights:
            sweights = "<weights>\n"
            for v in self.weights.values():
                sweights += f"{v:11.4e}\n"
            sweights += "</weights>\n"

        return (
            "<event>\n"
            + self.eventinfo.tolhe()
            + "\n"
            + "\n".join([p.tolhe() for p in self.particles])
            + "\n"
            + sweights
            + "</event>"
        )

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


@dataclass
class LHEEventInfo:
    """
    Store the event information in the LHE format.
    """

    nparticles: int
    """Number of particles in the event"""
    pid: int
    """Process ID for the event"""
    weight: float
    """Event weight"""
    scale: float
    """Energy scale of the event"""
    aqed: float
    """QED coupling constant alpha_QED"""
    aqcd: float
    """QCD coupling constant alpha_QCD"""

    def tolhe(self):
        """
        Return the event info as a string in LHE format.

        Returns:
            str: The event info as a string in LHE format.
        """
        return f"{self.nparticles:3d} {self.pid:6d} {self.weight: 15.10e} {self.scale: 15.10e} {self.aqed: 15.10e} {self.aqcd: 15.10e}"

    @classmethod
    def fromstring(cls, string: str) -> "LHEEventInfo":
        """
        Create an `LHEEventInfo` instance from a string in LHE format.
        """
        values = string.split()
        return cls(
            nparticles=int(float(values[0])),
            pid=int(float(values[1])),
            weight=float(values[2]),
            scale=float(values[3]),
            aqed=float(values[4]),
            aqcd=float(values[5]),
        )

    @property
    def fieldnames(self):
        """Return the fieldnames. For backward compatibility with versions < 1.0.0."""
        return [f.name for f in fields(self)]


@dataclass
class LHEParticle:
    """
    Represents a single particle in the LHE format.
    """

    id: int
    """PDG ID of the particle"""
    status: int
    """Status code of the particle"""
    mother1: int
    """First mother particle ID"""
    mother2: int
    """Second mother particle ID"""
    color1: int
    """First color line ID"""
    color2: int
    """Second color line ID"""
    px: float
    """Momentum component in x direction"""
    py: float
    """Momentum component in y direction"""
    pz: float
    """Momentum component in z direction"""
    e: float
    """Energy of the particle"""
    m: float
    """Mass of the particle"""
    lifetime: float
    """Lifetime of the particle"""
    spin: float
    """Spin of the particle"""

    @classmethod
    def fromstring(cls, string: str) -> "LHEParticle":
        """
        Create an `LHEParticle` instance from a string in LHE format.
        """
        values = string.split()
        return cls(
            id=int(float(values[0])),
            status=int(float(values[1])),
            mother1=int(float(values[2])),
            mother2=int(float(values[3])),
            color1=int(float(values[4])),
            color2=int(float(values[5])),
            px=float(values[6]),
            py=float(values[7]),
            pz=float(values[8]),
            e=float(values[9]),
            m=float(values[10]),
            lifetime=float(values[11]),
            spin=float(values[12]),
        )

    def tolhe(self) -> str:
        """
        Return the particle as a string in LHE format.

        Returns:
            str: The particle as a string in LHE format.
        """
        return f"{self.id:5d} {self.status:3d} {self.mother1:3d} {self.mother2:3d} {self.color1:3d} {self.color2:3d} {self.px: 15.8e} {self.py: 15.8e} {self.pz: 15.8e} {self.e: 15.8e} {self.m: 15.8e} {self.lifetime: 10.4e} {self.spin: 10.4e}"

    def mothers(self) -> list["LHEParticle"]:
        """
        Return a list of the particle's mothers.
        """
        first_idx = int(self.mother1) - 1
        second_idx = int(self.mother2) - 1
        return [
            self.event.particles[idx] for idx in (first_idx, second_idx) if idx >= 0
        ]

    @property
    def fieldnames(self):
        """fieldnames backwards compatibility."""
        return [f.name for f in fields(self)]


def _indent(elem, level=0):
    """
    XML indentation helper from https://stackoverflow.com/a/33956544.
    """
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for inner_elem in elem:
            _indent(inner_elem, level + 1)
        elem = inner_elem
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    elif level and (not elem.tail or not elem.tail.strip()):
        elem.tail = i


@dataclass
class LHEInitInfo:
    """Store the first line of the <init> block as dict."""

    beamA: int
    """Beam A PDG ID"""
    beamB: int
    """Beam B PDG ID"""
    energyA: float
    """Beam A energy"""
    energyB: float
    """Beam B energy"""
    PDFgroupA: int
    """PDF group for beam A"""
    PDFgroupB: int
    """PDF group for beam B"""
    PDFsetA: int
    """PDF set for beam A"""
    PDFsetB: int
    """PDF set for beam B"""
    weightingStrategy: int
    """Weighting strategy"""
    numProcesses: int
    """Number of processes"""

    def tolhe(self) -> str:
        """
        Return the init info block as a string in LHE format.

        Returns:
            str: The init info block as a string in LHE format.
        """
        return f" {self.beamA: 6d} {self.beamB: 6d} {self.energyA: 14.7e} {self.energyB: 14.7e} {self.PDFgroupA: 5d} {self.PDFgroupB: 5d} {self.PDFsetA: 5d} {self.PDFsetB: 5d} {self.weightingStrategy: 5d} {self.numProcesses: 5d}"

    @classmethod
    def fromstring(cls, string: str) -> "LHEInitInfo":
        """
        Create an `LHEInitInfo` instance from a string in LHE format.
        """
        values = string.split()
        return cls(
            beamA=int(float(values[0])),
            beamB=int(float(values[1])),
            energyA=float(values[2]),
            energyB=float(values[3]),
            PDFgroupA=int(float(values[4])),
            PDFgroupB=int(float(values[5])),
            PDFsetA=int(float(values[6])),
            PDFsetB=int(float(values[7])),
            weightingStrategy=int(float(values[8])),
            numProcesses=int(float(values[9])),
        )

    def __getitem__(self, key):
        """Dict backwards compatibility."""
        warnings.warn(
            f'Access by `lheinitinfo["{key}"]` is deprecated and will be removed in a future version. '
            f"Use `lheinitinfo.{key}` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Dict backwards compatibility."""
        warnings.warn(
            f'Access by `lheinitinfo["{key}"]` is deprecated and will be removed in a future version. '
            f"Use `lheinitinfo.{key}` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return setattr(self, key, value)

    @property
    def fieldnames(self):
        """fieldnames backwards compatibility."""
        return [f.name for f in fields(self)]


@dataclass
class LHEProcInfo:
    """Store the process info block as dict."""

    xSection: float
    """Cross section of the process"""
    error: float
    """Uncertainty/error of the cross section"""
    unitWeight: float
    """Unit weight of the process"""
    procId: int
    """Process ID"""

    def tolhe(self) -> str:
        """
        Return the process info block as a string in LHE format.

        Returns:
            str: The process info block as a string in LHE format.
        """
        return f"{self.xSection: 14.7e} {self.error: 14.7e} {self.unitWeight: 14.7e} {self.procId: 5d}"

    @classmethod
    def fromstring(cls, string: str) -> "LHEProcInfo":
        """
        Create an `LHEProcInfo` instance from a string in LHE format.
        """
        values = string.split()
        return cls(
            xSection=float(values[0]),
            error=float(values[1]),
            unitWeight=float(values[2]),
            procId=int(float(values[3])),
        )

    def __getitem__(self, key):
        """Dict backwards compatibility."""
        warnings.warn(
            f'Access by `lheprocinfo["{key}"]` is deprecated and will be removed in a future version. '
            f"Use `lheprocinfo.{key}` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(self, key)

    def __setitem__(self, key, value):
        """Dict backwards compatibility."""
        warnings.warn(
            f'Access by `lheprocinfo["{key}"]` is deprecated and will be removed in a future version. '
            f"Use `lheprocinfo.{key}` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return setattr(self, key, value)

    @property
    def fieldnames(self):
        """fieldnames backwards compatibility."""
        return [f.name for f in fields(self)]


@dataclass
class LHEInit:
    """Store the <init> block as dict."""

    initInfo: LHEInitInfo
    """Init information"""
    procInfo: list[LHEProcInfo]
    """Process information"""
    weightgroup: dict
    """Weight group information"""
    LHEVersion: str
    """LHE version"""

    def tolhe(self) -> str:
        """
        Return the init block as a string in LHE format.

        Returns:
            str: The init block as a string in LHE format.
        """
        # weightgroups to xml
        root = ET.Element("initrwgt")
        for _k, v in self.weightgroup.items():
            weightgroup_elem = ET.SubElement(root, "weightgroup", **v["attrib"])
            for _key, value in v["weights"].items():
                weight_elem = ET.SubElement(
                    weightgroup_elem, "weight", **value["attrib"]
                )
                weight_elem.text = value["name"]
        _indent(root)
        sweightgroups = ET.tostring(root, encoding="unicode", method="xml")

        return (
            "<init>\n"
            + self.initInfo.tolhe()
            + "\n"
            + "\n".join([p.tolhe() for p in self.procInfo])
            + "\n"
            + f"{sweightgroups}"
            + "</init>"
        )

    def __getitem__(self, key):
        """
        custom backwards compatibility get for dict
        """
        warnings.warn(
            f'Access by `lheinit["{key}"]` is deprecated and will be removed in a future version. '
            f"Use `lheinit.{key}` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Map field names to dataclass attributes
        if key in self.fieldnames:
            return getattr(self, key)
        # Try to get from initInfo for backward compatibility
        return getattr(self.initInfo, key)

    def __setitem__(self, key, value):
        """
        custom backwards compatibility set for dict
        """
        warnings.warn(
            f'Access by `lheinit["{key}"]` is deprecated and will be removed in a future version. '
            f"Use `lheinit.{key}` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Map field names to dataclass attributes
        if key in self.fieldnames:
            setattr(self, key, value)
        else:
            # Try to set on initInfo for backward compatibility
            setattr(self.initInfo, key, value)

    @classmethod
    def frombuffer(cls, fileobj):
        """Create an instance from a file-like object (buffer)."""
        initInfo = None
        procInfo = []
        weightgroup = {}
        LHEVersion = None

        for _event, element in ET.iterparse(fileobj, events=["start", "end"]):
            if element.tag == "init":
                data = element.text.split("\n")[1:-1]
                initInfo = LHEInitInfo.fromstring(data[0])
                procInfo = [LHEProcInfo.fromstring(d) for d in data[1:]]
            if element.tag == "initrwgt":
                weightgroup = {}
                index = 0
                for child in element:
                    # Find all weightgroups
                    if child.tag == "weightgroup" and child.attrib != {}:
                        if "type" in child.attrib:
                            wg_type = child.attrib["type"]
                        elif "name" in child.attrib:
                            wg_type = child.attrib["name"]
                        else:
                            ae = "weightgroup must have attribute 'type' or 'name'."
                            raise AttributeError(ae)
                        _temp = {"attrib": child.attrib, "weights": {}}
                        # Iterate over all weights in this weightgroup
                        for w in child:
                            if w.tag != "weight":
                                continue
                            if "id" not in w.attrib:
                                ae = "weight must have attribute 'id'"
                                raise AttributeError(ae)
                            wg_id = w.attrib["id"]
                            _temp["weights"][wg_id] = {
                                "attrib": w.attrib,
                                "name": w.text.strip() if w.text else "",
                                "index": index,
                            }
                            index += 1

                        weightgroup[wg_type] = _temp
            if element.tag == "LesHouchesEvents":
                LHEVersion = element.attrib["version"]
            if element.tag == "event":
                break
        return cls(
            initInfo=initInfo,
            procInfo=procInfo,
            weightgroup=weightgroup,
            LHEVersion=LHEVersion,
        )

    @classmethod
    def fromstring(cls, string: str) -> "LHEInit":
        """
        Create an `LHEEventInfo` instance from a string in LHE format.
        """
        return cls.frombuffer(io.StringIO(string))

    @property
    def fieldnames(self):
        """fieldnames backwards compatibility."""
        return [f.name for f in fields(self)]


@dataclass
class LHEFile:
    """
    Represents an LHE file.
    """

    init: Optional[LHEInit] = None
    """Init block"""
    events: Optional[Iterable[LHEEvent]] = None
    """Event block"""

    def write(self, output_stream, rwgt=True, weights=False):
        """
        Write the LHE file to an output stream.
        """
        output_stream.write(f'<LesHouchesEvents version="{self.init["LHEVersion"]}">\n')
        output_stream.write(self.init.tolhe() + "\n")
        for e in self.events:
            output_stream.write(e.tolhe(rwgt=rwgt, weights=weights) + "\n")
        output_stream.write("</LesHouchesEvents>")
        return output_stream

    def tolhe(self, rwgt=True, weights=False) -> str:
        """
        Return the LHE file as a string.
        """
        return self.write(io.StringIO(), rwgt=rwgt, weights=weights).getvalue()


def read_lhe_file(filepath, with_attributes=True) -> LHEFile:
    """
    Read an LHE file and return an LHEFile object.
    """
    lheinit = read_lhe_init(filepath)
    lheevents = (
        read_lhe_with_attributes(filepath) if with_attributes else read_lhe(filepath)
    )
    return LHEFile(init=lheinit, events=lheevents)


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


def read_lhe_init(filepath) -> LHEInit:
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


def read_lhe(filepath) -> Iterable[LHEEvent]:
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


def _get_index_to_id_map(init):
    """
    Produce a dictionary to map weight indices to the id of the weight.

    It is used for LHE files where there is only a list of weights per event.
    This dictionary is then used to map the list of weights to their weight id.
    Ideally, this needs to be done only once and the dictionary can be reused.

    Args:
        init (dict): init block as returned by read_lhe_init

    Returns:
        dict: {weight index: weight id}
    """
    ret = {}
    for wg in init["weightgroup"].values():
        for id, w in wg["weights"].items():
            ret[w["index"]] = id
    return ret


def read_lhe_with_attributes(filepath) -> Iterable[LHEEvent]:
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
                        eventdict["eventinfo"],
                        eventdict["particles"],
                        eventdict["weights"],
                        eventdict["attrib"],
                        eventdict["optional"],
                    )
                    # Clear processed elements
                    element.clear()
                    # Root tracks sub-elements -> clear all sub-elements
                    root.clear()
    except ET.ParseError as excep:
        print("WARNING. Parse Error:", excep)
        return


def read_num_events(filepath) -> int:
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


def write_lhe_string(lheinit, lheevents, rwgt=True, weights=False):
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


def _open_write_file(filepath: str, gz: bool = False):
    if filepath.endswith((".gz", ".gzip")) or gz:
        return gzip.open(filepath, "wt")
    return open(filepath, "w")


def write_lhe_file_path(
    lhefile: LHEFile,
    filepath: str,
    gz: bool = False,
    rwgt: bool = True,
    weights: bool = False,
):
    """
    Write the LHE file.
    """
    # if filepath suffix is gz, write as gz
    with _open_write_file(filepath, gz=gz) as f:
        lhefile.write(f, rwgt=rwgt, weights=weights)


def write_lhe_file(lheinit, lheevents, filepath, gz=False, rwgt=True, weights=False):
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
