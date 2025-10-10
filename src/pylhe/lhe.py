"""
Dataclasses defining the LHE format.
"""

import gzip
import io
import warnings
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass, fields
from typing import Any, BinaryIO, Optional, Protocol, TextIO, TypeVar, Union

import graphviz
from particle import latex_to_html_name
from particle.converters.bimap import DirectionalMaps
from particle.exceptions import MatchingIDNotFound


class Writeable(Protocol):
    """
    A protocol for writeable objects.
    """

    def write(self, s: str) -> Any:
        """Write a string to the object."""
        ...


TWriteable = TypeVar("TWriteable", bound=Writeable)

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
    weights: Optional[dict[Union[str, int], float]] = None
    """Event weights"""
    attributes: Optional[dict[str, str]] = None
    """Event attributes"""
    optional: Optional[list[str]] = None
    """Optional '#' comments stored in the event"""
    _graph: Optional[graphviz.Digraph] = None
    """Stores the graph representation of the event generated after first access of the property `lheevent.graph`"""

    def __post_init__(self) -> None:
        """Set up bidirectional relationship between event and particles."""
        for p in self.particles:
            p.event = self

    def tolhe(self, rwgt: bool = True, weights: bool = False) -> str:
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
    def graph(self) -> graphviz.Digraph:
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

    def _build_graph(self) -> None:
        """
        Navigate the particles in the event and produce a Digraph in the DOT language.
        """

        def safe_html_name(name: str) -> Any:
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
        include: Optional[Iterable[str]] = None,
        exclude: Optional[Iterable[str]] = None,
        **kwargs: dict[str, Any],
    ) -> Any:
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

    def tolhe(self) -> str:
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
    def fieldnames(self) -> list[str]:
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
    """Momentum x coordinate of the particle"""
    py: float
    """Momentum y coordinate of the particle"""
    pz: float
    """Momentum z coordinate of the particle"""
    e: float
    """Energy of the particle"""
    m: float
    """Mass of the particle"""
    lifetime: float
    """Lifetime of the particle"""
    spin: float
    """Spin of the particle"""
    event: Optional[LHEEvent] = None
    """Reference to the parent event, set when the particle is added to an event."""

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
        if self.event is None:
            err = "Particle is not associated with an event."
            raise ValueError(err)
        first_idx = int(self.mother1) - 1
        second_idx = int(self.mother2) - 1
        return [
            self.event.particles[idx] for idx in (first_idx, second_idx) if idx >= 0
        ]

    @property
    def fieldnames(self) -> list[str]:
        """Return the fieldnames. For backward compatibility with versions < 1.0.0."""
        # "event" would be more fittingly called "_event" since was never in the fieldnames
        return [f.name for f in fields(self) if f.name != "event"]


def _indent(elem: ET.Element, level: int = 0) -> None:
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
    """Store the first line of the <init> block as a dataclass."""

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

    def __getitem__(self, key: str) -> Any:
        """Return a dict of the fieldnames. For backward compatibility with versions < 1.0.0."""
        warnings.warn(
            f'Access by `lheinitinfo["{key}"]` is deprecated and will be removed in a future version. '
            f"Use `lheinitinfo.{key}` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a dict fieldname. For backward compatibility with versions < 1.0.0."""
        warnings.warn(
            f'Access by `lheinitinfo["{key}"]` is deprecated and will be removed in a future version. '
            f"Use `lheinitinfo.{key}` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        setattr(self, key, value)

    @property
    def fieldnames(self) -> list[str]:
        """Return the fieldnames. For backward compatibility with versions < 1.0.0."""
        return [f.name for f in fields(self)]


@dataclass
class LHEProcInfo:
    """Store the process info block as a dataclass."""

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

    def __getitem__(self, key: str) -> Any:
        """Return a dict item. For backward compatibility with versions < 1.0.0."""
        warnings.warn(
            f'Access by `lheprocinfo["{key}"]` is deprecated and will be removed in a future version. '
            f"Use `lheprocinfo.{key}` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a dict item. For backward compatibility with versions < 1.0.0."""
        warnings.warn(
            f'Access by `lheprocinfo["{key}"]` is deprecated and will be removed in a future version. '
            f"Use `lheprocinfo.{key}` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        setattr(self, key, value)

    @property
    def fieldnames(self) -> list[str]:
        """Return the fieldnames. For backward compatibility with versions < 1.0.0."""
        return [f.name for f in fields(self)]


@dataclass
class LHEWeightInfo:
    """Information about a single weight in a weight group."""

    attrib: dict[str, str]
    """Weight XML attributes"""
    name: str
    """Weight description text"""
    index: int
    """Sequential index for ordering"""

    def __getitem__(self, key: str) -> Any:
        """Get a weight attribute by its key. Backward compatibility for < 1.0.0."""
        warnings.warn(
            "Access by `lheweightinfo['key']` is deprecated and will be removed in a future version. Use `lheweightinfo.key` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Set a weight attribute by its key. Backward compatibility for < 1.0.0."""
        warnings.warn(
            "Access by `lheweightinfo['key']` is deprecated and will be removed in a future version. Use `lheweightinfo.key` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        setattr(self, key, value)


@dataclass
class LHEWeightGroup:
    """Information about a weight group."""

    attrib: dict[str, str]
    """Weight group XML attributes"""
    weights: dict[str, LHEWeightInfo]
    """Dictionary of weight ID to weight information"""

    def __getitem__(self, key: str) -> Any:
        """Get a weight by its ID. Backward compatibility for < 1.0.0."""
        warnings.warn(
            "Access by `lheweightgroup['key']` is deprecated and will be removed in a future version. Use `lheweightgroup.key` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(self, key)

    def __setitem__(self, key: str, value: LHEWeightInfo) -> None:
        """Set a weight by its ID. Backward compatibility for < 1.0.0."""
        warnings.warn(
            "Access by `lheweightgroup['key']` is deprecated and will be removed in a future version. Use `lheweightgroup.key` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        setattr(self, key, value)


@dataclass
class LHEInit:
    """Store the <init> block as a dataclass."""

    initInfo: LHEInitInfo
    """Init information"""
    procInfo: list[LHEProcInfo]
    """Process information"""
    weightgroup: dict[str, LHEWeightGroup]
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
            weightgroup_elem = ET.SubElement(root, "weightgroup", attrib=v.attrib)
            for _key, value in v.weights.items():
                weight_elem = ET.SubElement(
                    weightgroup_elem, "weight", attrib=value.attrib
                )
                weight_elem.text = value.name
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

    def __getitem__(self, key: str) -> Any:
        """
        Get a dict fieldname. For backward compatibility with versions < 1.0.0.
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

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set a dict fieldname. For backward compatibility with versions < 1.0.0.
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
    def frombuffer(cls, fileobj: Union[TextIO, BinaryIO, gzip.GzipFile]) -> "LHEInit":
        """Create an instance from a file-like object (buffer)."""
        initInfo = None
        procInfo = []
        weightgroup: dict[str, LHEWeightGroup] = {}
        LHEVersion: str = ""

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
                        _temp = LHEWeightGroup(attrib=child.attrib, weights={})
                        # Iterate over all weights in this weightgroup
                        for w in child:
                            if w.tag != "weight":
                                continue
                            if "id" not in w.attrib:
                                ae = "weight must have attribute 'id'"
                                raise AttributeError(ae)
                            wg_id = w.attrib["id"]
                            _temp.weights[wg_id] = LHEWeightInfo(
                                attrib=w.attrib,
                                name=w.text.strip() if w.text else "",
                                index=index,
                            )
                            index += 1

                        weightgroup[wg_type] = _temp
            if element.tag == "LesHouchesEvents":
                LHEVersion = element.attrib["version"]
            if element.tag == "event":
                break
        if initInfo is None:
            err = "No <init> block found in the LHE file."
            raise ValueError(err)
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
    def fieldnames(self) -> list[str]:
        """Return the fieldnames. For backward compatibility with versions < 1.0.0."""
        return [f.name for f in fields(self)]


@dataclass
class LHEFile:
    """
    Represents an LHE file as a dataclass.
    """

    init: Optional[LHEInit] = None
    """Init block"""
    events: Optional[Iterable[LHEEvent]] = None
    """Event block"""

    def write(
        self, output_stream: TWriteable, rwgt: bool = True, weights: bool = False
    ) -> TWriteable:
        """
        Write the LHE file to an output stream.
        """
        output_stream.write("<LesHouchesEvents")
        if self.init is not None:
            output_stream.write(f' version="{self.init.LHEVersion}"')
        output_stream.write(">\n")
        if self.init is not None:
            output_stream.write(self.init.tolhe() + "\n")
        if self.events is not None:
            for e in self.events:
                output_stream.write(e.tolhe(rwgt=rwgt, weights=weights) + "\n")
        output_stream.write("</LesHouchesEvents>")
        return output_stream

    def tolhe(self, rwgt: bool = True, weights: bool = False) -> str:
        """
        Return the LHE file as a string.
        """
        return self.write(io.StringIO(), rwgt=rwgt, weights=weights).getvalue()
