"""
Python interface to read Les Houches Event (LHE) files.
"""

import gzip
import io
import os
import warnings
import xml.etree.ElementTree as ET
from abc import ABC
from collections.abc import Iterable, Iterator, MutableMapping
from dataclasses import asdict, dataclass, field, fields
from typing import (
    Any,
    BinaryIO,
    Optional,
    Protocol,
    TextIO,
    TypeVar,
    Union,
)

import graphviz  # type: ignore[import-untyped]
from particle import latex_to_html_name
from particle.converters.bimap import DirectionalMaps
from particle.exceptions import MatchingIDNotFound

from pylhe._version import version as __version__

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


# retrieve mapping of PDG ID to particle name as LaTeX string
_PDGID2LaTeXNameMap, _ = DirectionalMaps("PDGID", "LATEXNAME", converters=(str, str))

PathLike = Union[str, bytes, os.PathLike[str], os.PathLike[bytes]]


class Writeable(Protocol):
    """
    A protocol for writeable objects.
    """

    def write(self, s: str) -> Any:  # pragma: no cover
        """Write a string to the object."""
        ...


TWriteable = TypeVar("TWriteable", bound=Writeable)


@dataclass
class DictCompatibility(MutableMapping[str, Any], ABC):
    """
    Mixin for dataclasses to behave like mutable dictionaries.
    """

    def __getitem__(self, key: str) -> Any:
        """
        Get a dict by fieldname.

        For backward compatibility with versions < 1.0.0.

        .. deprecated:: 1.0.0
            Access by `object['key']` is deprecated and will be removed in a future version. Use `object.key` instead.
        """
        warnings.warn(
            f'Access by `object["{key}"]` is deprecated and will be removed in a future version. '
            f"Use `object.{key}` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return getattr(self, key)

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Set a dict by fieldname.

        For backward compatibility with versions < 1.0.0.

        .. deprecated:: 1.0.0
            Access by `object['key']` is deprecated and will be removed in a future version. Use `object.key` instead.
        """
        warnings.warn(
            f'Access by `object["{key}"]` is deprecated and will be removed in a future version. '
            f"Use `object.{key}` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        setattr(self, key, value)

    def __delitem__(self, key: str) -> None:
        err = f"Cannot delete field {key!r} from dataclass instance"
        raise TypeError(err)

    def __iter__(self) -> Any:
        warnings.warn(
            "Dict-like iteration is deprecated and will be removed in a future version. "
            "Use `asdict(object)` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return iter(asdict(self))

    def __len__(self) -> int:
        warnings.warn(
            "Dict-like length is deprecated and will be removed in a future version. "
            "Use `asdict(object)` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return len(asdict(self))

    @property
    def fieldnames(self) -> list[str]:
        """
        Return the fieldnames.

        For backward compatibility with versions < 1.0.0.

        .. deprecated:: 1.0.0
            Listing fieldnames via `object.fieldnames` is deprecated and will be removed in a future version.
        """
        warnings.warn(
            "The fieldnames property is deprecated and will be removed in a future version. "
            "Use `asdict(object)` instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return [f.name for f in fields(self)]


@dataclass
class LHEEventInfo(DictCompatibility):
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


@dataclass
class LHEParticle(DictCompatibility):
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

    def __post_init__(self) -> None:
        """Initialize the event reference."""
        # we store the circular event reference in a private attribute
        self._event: Optional[LHEEvent] = None

    @property
    def event(self) -> Optional["LHEEvent"]:
        """Reference to the parent event, set when the particle is added to an event."""
        # Previously it was just event so we still allow that for backward compatibility
        return self._event

    @event.setter
    def event(self, value: Optional["LHEEvent"]) -> None:
        """Set the parent event reference."""
        # Previously it was just event so we still allow that for backward compatibility
        self._event = value

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
            err = "Particle is not associated to an event."
            raise ValueError(err)
        first_idx = int(self.mother1) - 1
        second_idx = int(self.mother2) - 1
        return [
            self.event.particles[idx] for idx in (first_idx, second_idx) if idx >= 0
        ]


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
class LHEInitInfo(DictCompatibility):
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


@dataclass
class LHEProcInfo(DictCompatibility):
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


@dataclass
class LHEWeightInfo(DictCompatibility):
    """Information about a single weight in a weight group."""

    attrib: dict[str, str]
    """Weight XML attributes"""
    name: str
    """Weight description text"""
    index: int
    """Sequential index for ordering"""


@dataclass
class LHEWeightGroup(DictCompatibility):
    """Information about a weight group."""

    attrib: dict[str, str]
    """Weight group XML attributes"""
    weights: dict[str, LHEWeightInfo]
    """Dictionary of weight ID to weight information"""


@dataclass
class LHEInit(DictCompatibility):
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
        Get a dict fieldname.

        For backward compatibility with versions < 1.0.0.

        .. deprecated:: 1.0.0
            Access by `lheinit["key"]` is deprecated and will be removed in a future version.
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
        Set a dict fieldname.

        For backward compatibility with versions < 1.0.0.

        .. deprecated:: 1.0.0
            Access by `lheinit["key"]` is deprecated and will be removed in a future version.
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
    def _fromcontext(cls, root: ET.Element, context: Any) -> "LHEInit":
        initInfo = None
        procInfo = []
        weightgroup: dict[str, LHEWeightGroup] = {}
        LHEVersion: str = ""

        if root.tag == "LesHouchesEvents":
            LHEVersion = root.attrib["version"]

        for event, element in context:
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
                        for wc in child:
                            if wc.tag != "weight":
                                continue
                            if "id" not in wc.attrib:
                                ae = "weight must have attribute 'id'"
                                raise AttributeError(ae)
                            wg_id = wc.attrib["id"]
                            _temp.weights[wg_id] = LHEWeightInfo(
                                attrib=wc.attrib,
                                name=wc.text.strip() if wc.text else "",
                                index=index,
                            )
                            index += 1

                        weightgroup[wg_type] = _temp
            if (
                element.tag == "init" and event == "end"
            ):  # text is None before end-tag if event == "start", if there are sub-elements (e.g. MadGraph stores a <generator> tag there)
                if element.text is None:
                    err = "<init> block has no text."
                    raise ValueError(err)
                data = element.text.split("\n")[1:-1]
                initInfo = LHEInitInfo.fromstring(data[0])
                procInfo = [LHEProcInfo.fromstring(d) for d in data[1:]]

            if element.tag == "event":
                break
        if initInfo is None:
            err = "No <init> block found in the LHE file."
            raise ValueError(err)
        return LHEInit(
            initInfo=initInfo,
            procInfo=procInfo,
            weightgroup=weightgroup,
            LHEVersion=LHEVersion,
        )


@dataclass
class LHEEvent(DictCompatibility):
    """
    Store a single event in the LHE format.
    """

    eventinfo: LHEEventInfo
    """Event information"""
    particles: list[LHEParticle]
    """List of particles in the event"""
    weights: dict[str, float] = field(default_factory=dict)
    """Event weights"""
    attributes: dict[str, str] = field(default_factory=dict)
    """Event attributes"""
    optional: list[str] = field(default_factory=list)
    """Optional '#' comments stored in the event"""
    _graph: Optional[graphviz.Digraph] = None
    """Stores the graph representation of the event generated after first access of the property `lheevent.graph`"""

    def __post_init__(self) -> None:
        """Set up a bidirectional relationship between event and particles."""
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

    @classmethod
    def _fromcontext(
        cls,
        root: ET.Element,
        context: Any,
        lheinit: LHEInit,
        with_attributes: bool,
    ) -> Iterator["LHEEvent"]:
        index_map = _get_index_to_id_map(lheinit) if with_attributes else {}
        for event, element in context:
            if event == "end" and element.tag == "event":
                if element.text is None:
                    err = "<event> block has no text."
                    raise ValueError(err)

                data = element.text.strip().split("\n")
                eventdata_str, particles_str = data[0], data[1:]

                eventinfo = LHEEventInfo.fromstring(eventdata_str)
                particles = [
                    LHEParticle.fromstring(p)
                    for p in particles_str
                    if not p.strip().startswith("#")
                ]

                if with_attributes:
                    weights = {}
                    attrib = element.attrib
                    optional = [
                        p.strip() for p in particles_str if p.strip().startswith("#")
                    ]

                    for sub in element:
                        if sub.tag == "weights":
                            if sub.text is None:
                                err = "<weights> block has no text."
                                raise ValueError(err)
                            for i, w in enumerate(sub.text.split()):
                                if w and index_map[i] not in weights:
                                    weights[index_map[i]] = float(w)
                        elif sub.tag == "rwgt":
                            for r in sub:
                                if r.tag == "wgt":
                                    if r.text is None:
                                        err = "<wgt> block has no text."
                                        raise ValueError(err)
                                    weights[r.attrib["id"]] = float(r.text.strip())

                    yield LHEEvent(
                        eventinfo=eventinfo,
                        particles=particles,
                        weights=weights,
                        attributes=attrib,
                        optional=optional,
                    )
                else:
                    yield LHEEvent(eventinfo, particles)

                # Clear memory
                element.clear()
                root.clear()
            if element.tag == "LesHouchesEvents" and event == "end":
                return

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
        self._graph = graphviz.Digraph()
        for i, p in enumerate(self.particles):
            iid = int(p.id)
            sid = str(iid)
            try:
                name = _PDGID2LaTeXNameMap[sid]
                texlbl = f"${name}$"
                label = f'<<table border="0" cellspacing="0" cellborder="0"><tr><td>{latex_to_html_name(name)}</td></tr></table>>'
            except MatchingIDNotFound:
                texlbl = sid
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
        return self.graph._repr_mimebundle_(include=include, exclude=exclude, **kwargs)


@dataclass
class LHEFile(DictCompatibility):
    """
    Represents an LHE file as a dataclass.
    """

    init: LHEInit
    """Init block"""
    events: Iterable[LHEEvent] = ()
    """Event block"""

    def write(
        self, output_stream: TWriteable, rwgt: bool = True, weights: bool = False
    ) -> TWriteable:
        """
        Write the LHE file to an output stream.
        """
        output_stream.write(f'<LesHouchesEvents version="{self.init.LHEVersion}">\n')
        output_stream.write(self.init.tolhe() + "\n")
        for e in self.events:
            output_stream.write(e.tolhe(rwgt=rwgt, weights=weights) + "\n")
        output_stream.write("</LesHouchesEvents>")
        return output_stream

    def tolhe(self, rwgt: bool = True, weights: bool = False) -> str:
        """
        Return the LHE file as a string.
        """
        return self.write(io.StringIO(), rwgt=rwgt, weights=weights).getvalue()

    def tofile(
        self,
        filepath: str,
        gz: bool = False,
        rwgt: bool = True,
        weights: bool = False,
    ) -> None:
        """
        Write the LHE file.

        Args:
            filepath: Path to the output file.
            gz: Whether to gzip the output file (ignored if filepath suffix is .gz/.gzip).
            rwgt: Whether to include weights in 'rwgt' format.
            weights: Whether to include weights in 'weights' format.
        """
        # if filepath suffix is gz, write as gz
        with _open_write_file(filepath, gz=gz) as f:
            self.write(f, rwgt=rwgt, weights=weights)

    @classmethod
    def fromstring(
        cls, string: str, with_attributes: bool = True, generator: bool = True
    ) -> "LHEFile":
        """
        Create an LHEFile instance from a string in LHE format.
        """
        return cls.frombuffer(
            io.StringIO(string), with_attributes=with_attributes, generator=generator
        )

    @classmethod
    def fromfile(
        cls, filepath: PathLike, with_attributes: bool = True, generator: bool = True
    ) -> "LHEFile":
        """
        Read an LHE file and return an LHEFile object.
        """
        return cls.frombuffer(
            _extract_fileobj(filepath),
            with_attributes=with_attributes,
            generator=generator,
        )

    @classmethod
    def frombuffer(
        cls,
        fileobject: Union[
            io.BufferedReader, gzip.GzipFile, io.StringIO, TextIO, BinaryIO
        ],
        with_attributes: bool = True,
        generator: bool = True,
    ) -> "LHEFile":
        """
        Read an LHE file and return an LHEFile object.
        """

        def _generator(lhef: LHEFile) -> Iterator[LHEEvent]:
            try:
                with fileobject as fileobj:
                    context = ET.iterparse(fileobj, events=["start", "end"])
                    _, root = next(context)  # Get the root element

                    lheinit = LHEInit._fromcontext(root, context)
                    lhef.init = lheinit
                    # First yield allows caller to advance generator to read lheinit before consuming real events
                    yield LHEEvent(
                        eventinfo=LHEEventInfo(
                            nparticles=0,
                            pid=0,
                            weight=0.0,
                            scale=0.0,
                            aqed=0.0,
                            aqcd=0.0,
                        ),
                        particles=[],
                    )
                    yield from LHEEvent._fromcontext(
                        root, context, lheinit, with_attributes
                    )

            except ET.ParseError as excep:
                warnings.warn(f"Parse Error: {excep}", RuntimeWarning, stacklevel=1)
                return

        lhef = cls(
            # dummy init, will be replaced
            init=LHEInit(
                initInfo=LHEInitInfo(0, 0, 0.0, 0.0, 0, 0, 0, 0, 0, 0),
                procInfo=[],
                weightgroup={},
                LHEVersion="3.0",
            ),
            events=[],
        )
        events = _generator(lhef)
        try:
            next(events)  # advance to read lheinit
        except StopIteration:
            # If generator stops without yielding, it means no init was read
            err = "No or faulty <init> block found in the LHE file."
            raise ValueError(err) from None

        lhef.events = events if generator else list(events)
        return lhef

    @staticmethod
    def count_events(filepath: PathLike) -> int:
        """
        Efficiently count the number of events in an LHE file without loading them into memory.

        Args:
            filepath: Path to the LHE file.

        Returns:
            Number of events in the file, or -1 if parsing fails.
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
                    if event == "end" and element.tag == "LesHouchesEvents":
                        return count
        except ET.ParseError as excep:
            warnings.warn(f"Parse Error: {excep}", RuntimeWarning, stacklevel=1)
        return -1


def read_lhe_file(filepath: PathLike, with_attributes: bool = True) -> LHEFile:
    """
    Read an LHE file and return an LHEFile object.

    .. deprecated:: 1.0.0
        Use `LHEFile.fromfile` instead.
    """
    warnings.warn(
        "read_lhe_file is deprecated and will be removed in a future version. "
        "Use `LHEFile.fromfile` instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return LHEFile.fromfile(filepath, with_attributes=with_attributes)


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

    .. deprecated:: 1.0.0
        Use `LHEFile.fromfile(...).init` instead.
    """
    warnings.warn(
        "read_lhe_init is deprecated and will be removed in a future version. "
        "Use `LHEFile.fromfile(...).init` instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return LHEFile.fromfile(filepath).init


def read_lhe(filepath: PathLike) -> Iterable[LHEEvent]:
    """
    Read and yield the events in the LHE file.

    .. deprecated:: 1.0.0
        Use `LHEFile.fromfile(...).events` instead.
    """
    warnings.warn(
        "read_lhe is deprecated and will be removed in a future version. "
        "Use `LHEFile.fromfile(...).events` instead",
        DeprecationWarning,
        stacklevel=2,
    )
    yield from LHEFile.fromfile(filepath, with_attributes=False).events


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

    .. deprecated:: 1.0.0
        Use `LHEEvent.fromfile` with the `with_attributes` parameter instead.
    """
    warnings.warn(
        "read_lhe_with_attributes is deprecated and will be removed in a future version. "
        "Use `LHEEvent.fromfile` with the `with_attributes` parameter instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    yield from LHEFile.fromfile(filepath, with_attributes=True).events


def read_num_events(filepath: PathLike) -> int:
    """
    Moderately efficient way to get the number of events stored in a file.

    .. deprecated:: 1.0.0
        Use `LHEFile.count_events` instead.
    """
    warnings.warn(
        "read_num_events is deprecated and will be removed in a future version. "
        "Use `LHEFile.count_events` instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return LHEFile.count_events(filepath)


def write_lhe_file_string(
    lhefile: LHEFile, rwgt: bool = True, weights: bool = False
) -> str:  # pragma: no cover
    """
    Return the LHE file as a string.

    .. deprecated:: 1.0.0
         Use `LHEFile.tolhe` instead.
    """
    warnings.warn(
        "write_lhe_file_string is deprecated and will be removed in a future version. "
        "Use `LHEFile.tolhe` instead.",
        DeprecationWarning,
        stacklevel=2,
    )
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
       Instead of :func:`~pylhe.write_lhe_string(init,events,rwgt,weights)` use `LHEFile(init,events).tolhe(rwgt,weights)`.
    """
    warnings.warn(
        "`write_lhe_string` is deprecated and will be removed in a future version. "
        "Use `LHEFile(...).tolhe(...)` instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return LHEFile(init=lheinit, events=lheevents).tolhe(rwgt=rwgt, weights=weights)


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

    .. deprecated:: 1.0.0
        Use `LHEFile.tofile` instead.
    """
    warnings.warn(
        "write_lhe_file_path is deprecated and will be removed in a future version. "
        "Use `LHEFile.tofile` instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    lhefile.tofile(filepath, gz=gz, rwgt=rwgt, weights=weights)


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
       Instead of :func:`~pylhe.write_lhe_file(init,events,filepath,gz,rwgt,weights)` use `LHEFile(init,events).tofile(filepath,gz,rwgt,weights)`.
    """
    warnings.warn(
        "`write_lhe_file` is deprecated and will be removed in a future version. "
        "Use `LHEFile(...).tofile(...)` instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    LHEFile(init=lheinit, events=lheevents).tofile(
        filepath,
        gz=gz,
        rwgt=rwgt,
        weights=weights,
    )


# we import this later to avoid circular imports
from .awkward import to_awkward  # noqa: E402
