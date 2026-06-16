"""
Python interface to read Les Houches Event (LHE) files.
"""

import gzip
import io
import os
import warnings
import xml.etree.ElementTree as ET
from collections.abc import Iterable, Iterator
from copy import deepcopy
from dataclasses import dataclass, field
from typing import (
    Any,
    BinaryIO,
    Optional,
    Protocol,
    TextIO,
    TypeVar,
    Union,
)
from xml.sax.saxutils import quoteattr

import graphviz  # type: ignore[import-untyped]
from particle import latex_to_html_name
from particle.converters.bimap import DirectionalMaps
from particle.exceptions import MatchingIDNotFound

from pylhe._version import version as __version__

__all__ = [
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


def _open_xml_tag(tag: str, attributes: dict[str, str]) -> str:
    """Helper function to open an XML tag with attributes."""
    attrs = ""
    for k, v in attributes.items():
        attrs += f" {k}={quoteattr(v)}"
    return f"<{tag}{attrs}>"


def _copy_xml_element(element: ET.Element) -> ET.Element:
    """Return a detached copy of an XML element."""
    copied = deepcopy(element)
    copied.tail = None
    return copied


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

    def __post_init__(self) -> None:
        """Initialize the event reference."""
        # we store the circular event reference in a private attribute
        self._event: Optional[LHEEvent] = None

    @property
    def event(self) -> Optional["LHEEvent"]:
        """
        Reference to the parent event, set when the particle is added to an event.

        .. deprecated:: 2.0.0
            Access by `particle.event` is deprecated and will be removed in a future version.
        """
        warnings.warn(
            "Access by `particle.event` is deprecated and will be removed in a future version.",
            DeprecationWarning,
            stacklevel=2,
        )
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

        .. deprecated:: 2.0.0
                Accessing mothers via `LHEParticle.mothers()` is deprecated and will be removed in a future version. Use `LHEEvent.mothers(LHEParticle)` method, `LHEParticle.mother1` and `LHEParticle.mother2` instead.
        """
        warnings.warn(
            "Access by `LHEParticle.mothers()` is deprecated and will be removed in a future version. "
            "Use `LHEEvent.mothers(LHEParticle)` method, `LHEParticle.mother1` and `LHEParticle.mother2` instead.",
            DeprecationWarning,
            stacklevel=2,
        )

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


@dataclass
class LHEInitRWGTWeight:
    """Information about a single weight inside or outside of a weight group."""

    id: str
    """ID of the weight"""
    name: str
    """Weight description text"""
    extra_attributes: dict[str, str] = field(default_factory=dict)
    """Weight XML attributes not represented by dedicated fields"""

    def __post_init__(self) -> None:
        """Remove schema typed owned information from attributes dict to avoid duplication and potential inconsistencies."""
        self.extra_attributes.pop("id", None)

    @property
    def attributes(self) -> dict[str, str]:
        """Return all the attributes of the weight, including the ID."""
        # class schema typed attributes take precedence over extra_attributes in case of overlap to avoid inconsistencies
        return {**self.extra_attributes, "id": self.id}


@dataclass
class LHEInitRWGTWeightGroup:
    """Information about a weight group."""

    name: Optional[str] = (
        None  # Normally this is required, i.e. not Optional, but old Madgraph-2.0.0 uses 'type' instead of 'name'...
    )
    """Name of the weight group"""
    combine: Optional[str] = None
    """Combination method of the weight group"""
    weights: list[LHEInitRWGTWeight] = field(default_factory=list)
    """List of weight information"""
    extra_attributes: dict[str, str] = field(default_factory=dict)
    """Weight group XML attributes not represented by dedicated fields"""

    @property
    def attributes(self) -> dict[str, str]:
        """Return all the attributes of the weight group, including the name and combine attributes."""
        attrs = {}
        if self.name is not None:
            attrs["name"] = self.name
        if self.combine is not None:
            attrs["combine"] = self.combine
        # class schema typed attributes take precedence over extra_attributes in case of overlap to avoid inconsistencies
        return {**self.extra_attributes, **attrs}

    def __post_init__(self) -> None:
        """Remove schema typed owned information from attributes dict to avoid duplication and potential inconsistencies."""
        name = self.extra_attributes.pop("name", None)
        if self.name is None:
            self.name = name
        combine = self.extra_attributes.pop("combine", None)
        if self.combine is None:
            self.combine = combine


InitRWGTEntry = Union[LHEInitRWGTWeight, LHEInitRWGTWeightGroup]


@dataclass
class LHEInitRWGT:
    """
    Represents the <initrwgt> block of an LHE file as a dataclass.
    """

    entries: list[InitRWGTEntry] = field(default_factory=list)

    def iter_weights(self) -> Iterator[LHEInitRWGTWeight]:
        """Iterate over all weights in the <initrwgt> block, including those inside weight groups."""
        for entry in self.entries:
            if isinstance(entry, LHEInitRWGTWeight):
                yield entry
            else:
                yield from entry.weights

    def weights_by_id(self) -> dict[str, LHEInitRWGTWeight]:
        """Return a dictionary mapping weight IDs to LHEInitRWGTWeight instances for all weights in the <initrwgt> block."""
        return {w.id: w for w in self.iter_weights()}

    def index_to_id(self) -> dict[int, str]:
        """Return a dictionary mapping weight indices to weight IDs for all weights in the <initrwgt> block."""
        return {i: w.id for i, w in enumerate(self.iter_weights())}

    def tolhe(self) -> str:
        """
        Return the init block as a string in LHE format.

        Returns:
            str: The init block as a string in LHE format.
        """
        # weightgroups to xml
        root = ET.Element("initrwgt")
        for e in self.entries:
            if isinstance(e, LHEInitRWGTWeightGroup):
                weightgroup_elem = ET.SubElement(
                    root, "weightgroup", attrib=e.attributes
                )
                for value in e.weights:
                    weight_elem = ET.SubElement(
                        weightgroup_elem, "weight", attrib=value.attributes
                    )
                    weight_elem.text = value.name
            else:
                weight_elem = ET.SubElement(root, "weight", attrib=e.attributes)
                weight_elem.text = e.name
        _indent(root)
        return ET.tostring(root, encoding="unicode", method="xml")


@dataclass
class LHEHeader:
    """
    Represents the header block of an LHE file as a dataclass.
    """

    initrwgt: LHEInitRWGT
    """<initrwgt> block information"""
    extra_elements: list[ET.Element] = field(default_factory=list)
    """Other XML elements stored directly inside the header block"""
    extra_attributes: dict[str, str] = field(default_factory=dict)
    """Attributes of the header element not represented by dedicated fields"""

    @property
    def attributes(self) -> dict[str, str]:
        """Return all the attributes of the header element"""
        return {**self.extra_attributes}

    def tolhe(self) -> str:
        """Return the header block as a string in LHE format."""
        root = ET.Element("header", attrib=self.attributes)
        for element in self.extra_elements:
            root.append(_copy_xml_element(element))
        if self.initrwgt.entries:
            root.append(ET.fromstring(self.initrwgt.tolhe()))

        _indent(root)
        return ET.tostring(root, encoding="unicode", method="xml")

    @classmethod
    def _fromcontext(cls, _root: ET.Element, context: Any) -> Union["LHEHeader", None]:
        initrwgtentries: list[InitRWGTEntry] = []
        extra_elements: list[ET.Element] = []
        attributes: dict[str, str] = {}

        for event, element in context:
            if (
                element.tag == "header" and event == "end"
            ):  # text is None before end-tag if event == "start", if there are sub-elements (e.g. MadGraph stores a <generator> tag there)
                attributes = element.attrib.copy()
                for child in element:
                    if child.tag == "initrwgt":
                        for weight_child in child:
                            if (
                                weight_child.tag == "weight"
                                and weight_child.attrib != {}
                            ):
                                if "id" not in weight_child.attrib:
                                    ae = "weight must have attribute 'id'"
                                    raise AttributeError(ae)
                                initrwgtentries.append(
                                    LHEInitRWGTWeight(
                                        id=weight_child.attrib["id"],
                                        extra_attributes=weight_child.attrib.copy(),
                                        name=weight_child.text.strip()
                                        if weight_child.text
                                        else "",
                                    )
                                )
                            # Find all weightgroups
                            if (
                                weight_child.tag == "weightgroup"
                                and weight_child.attrib != {}
                            ):
                                if (
                                    "type" not in weight_child.attrib
                                    and "name" not in weight_child.attrib
                                ):
                                    ae = "weightgroup must have attribute 'type' or 'name'."
                                    raise AttributeError(ae)
                                temp_group = LHEInitRWGTWeightGroup(
                                    extra_attributes=weight_child.attrib.copy(),
                                    weights=[],
                                )
                                # Iterate over all weights in this weightgroup
                                for wc in weight_child:
                                    if wc.tag == "weight":
                                        if "id" not in wc.attrib:
                                            ae = "weight must have attribute 'id'"
                                            raise AttributeError(ae)
                                        temp_group.weights.append(
                                            LHEInitRWGTWeight(
                                                id=wc.attrib["id"],
                                                extra_attributes=wc.attrib.copy(),
                                                name=wc.text.strip() if wc.text else "",
                                            )
                                        )
                                initrwgtentries.append(temp_group)
                    else:
                        extra_elements.append(_copy_xml_element(child))
                break
        return LHEHeader(
            initrwgt=LHEInitRWGT(entries=initrwgtentries),
            extra_elements=extra_elements,
            extra_attributes=attributes,
        )


@dataclass
class LHEGenerator:
    """Information about a generator."""

    name: str
    """Name of the generator"""
    version: str
    """Version of the generator"""
    description: str
    """Description of the generator"""
    extra_attributes: dict[str, str] = field(default_factory=dict)
    """Generator XML attributes not represented by dedicated fields"""

    @property
    def attributes(self) -> dict[str, str]:
        """Return all the attributes of the generator element, including the name and version attributes."""
        # class schema typed attributes take precedence over extra_attributes in case of overlap to avoid inconsistencies
        return {**self.extra_attributes, "name": self.name, "version": self.version}

    def __post_init__(self) -> None:
        """Remove schema typed owned information from attributes dict to avoid duplication and potential inconsistencies."""
        self.extra_attributes.pop("name", None)
        self.extra_attributes.pop("version", None)

    def tolhe(self) -> str:
        """
        Return the generator information as a string in LHE format.

        Returns:
            str: The generator information as a string in LHE format.
        """
        opening_tag = _open_xml_tag("generator", self.attributes)
        return f"{opening_tag}{self.description}</generator>"


@dataclass
class LHEInit:
    """Store the <init> block as a dataclass."""

    initInfo: LHEInitInfo
    """Init information"""
    procInfo: list[LHEProcInfo]
    """Process information"""
    generators: list[LHEGenerator]
    """Generator information"""

    def tolhe(self) -> str:
        """
        Return the init block as a string in LHE format.

        Returns:
            str: The init block as a string in LHE format.
        """
        return (
            "<init>\n"
            + self.initInfo.tolhe()
            + "\n"
            + "\n".join(
                [p.tolhe() for p in self.procInfo]
                + [g.tolhe() for g in self.generators]
            )
            + "\n"
            + "</init>"
        )

    @classmethod
    def _fromcontext(cls, _root: ET.Element, context: Any) -> "LHEInit":
        initInfo = None
        procInfo = []
        generators = []

        for event, element in context:
            if (
                element.tag == "generator"
                and "version" in element.attrib
                and event == "end"
            ):
                if "name" in element.attrib:
                    # lhe-v3 has name and version
                    generator = LHEGenerator(
                        name=element.attrib["name"],
                        version=element.attrib["version"],
                        description=""
                        if element.text is None
                        else element.text.strip(),
                        extra_attributes=element.attrib.copy(),
                    )
                    generators.append(generator)
                else:
                    # lhe-v2 has version and name is in the text
                    generator = LHEGenerator(
                        version=element.attrib["version"],
                        name="",
                        description=element.text.strip() if element.text else "",
                        extra_attributes=element.attrib.copy(),
                    )
                    generators.append(generator)
            if (
                element.tag == "init" and event == "end"
            ):  # text is None before end-tag if event == "start", if there are sub-elements (e.g. MadGraph stores a <generator> tag there)
                if element.text is None:
                    err = "<init> block has no text."
                    raise ValueError(err)
                data = element.text.split("\n")[1:-1]
                initInfo = LHEInitInfo.fromstring(data[0])
                procInfo = [LHEProcInfo.fromstring(d) for d in data[1:]]
                break
        if initInfo is None:
            err = "No <init> block found in the LHE file."
            raise ValueError(err)
        return LHEInit(
            initInfo=initInfo,
            procInfo=procInfo,
            generators=generators,
        )


@dataclass
class LHEEvent:
    """
    Store a single event in the LHE format.
    """

    eventinfo: LHEEventInfo
    """Event information"""
    particles: list[LHEParticle]
    """List of particles in the event"""
    weights: dict[str, float] = field(default_factory=dict)
    """Event weights"""
    scales: dict[str, float] = field(default_factory=dict)
    """Event scales"""
    attributes: dict[str, str] = field(default_factory=dict)
    """Event attributes not represented by dedicated fields"""
    optional: list[str] = field(default_factory=list)
    """Optional '#' comments stored in the event"""
    _graph: Optional[graphviz.Digraph] = field(default=None, repr=False, compare=False)
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
        if rwgt and weights:
            err = "Cannot specify both rwgt and weights formats simultaneously."
            raise ValueError(err)
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

        sscales = ""
        if self.scales:
            sscales = (
                "<scales "
                + " ".join(f"{k}='{v}'" for k, v in self.scales.items())
                + "/>\n"
            )

        soptional = ""
        if self.optional:
            soptional = "\n".join(self.optional) + "\n"

        return (
            _open_xml_tag("event", self.attributes)
            + "\n"
            + self.eventinfo.tolhe()
            + "\n"
            + "\n".join([p.tolhe() for p in self.particles])
            + "\n"
            + soptional
            + sweights
            + sscales
            + "</event>"
        )

    @classmethod
    def _fromcontext(
        cls,
        root: ET.Element,
        context: Any,
        lheheader: Optional[LHEHeader] = None,
        with_attributes: bool = True,
    ) -> Iterator["LHEEvent"]:
        index_map = (
            lheheader.initrwgt.index_to_id() if with_attributes and lheheader else {}
        )
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
                    scales = {}
                    attrib = element.attrib.copy()
                    optional = [
                        p.strip() for p in particles_str if p.strip().startswith("#")
                    ]

                    for sub in element:
                        if sub.tag == "weights":
                            if sub.text is None:
                                err = "<weights> block has no text."
                                raise ValueError(err)
                            if not index_map:
                                err = "<initrwgt> is required to parse <weights> block but not found in the header."
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
                        elif sub.tag == "scales":
                            for k, v in sub.attrib.items():
                                scales[k] = float(v)

                    yield LHEEvent(
                        eventinfo=eventinfo,
                        particles=particles,
                        weights=weights,
                        scales=scales,
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
            self._graph.node(str(i), label=label, texlbl=texlbl)
        for i, p in enumerate(self.particles):
            for mother_idx in self.mother_indices(p):
                self._graph.edge(str(mother_idx), str(i))

    def mother_indices(self, particle: LHEParticle) -> list[int]:
        """
        Return the positional indices of the particle's mothers in ``self.particles``.

        The LHE ``mother1``/``mother2`` fields are 1-based; absent mothers (0) are dropped.
        """
        idxs = [particle.mother1 - 1, particle.mother2 - 1]
        out: list[int] = []
        for idx in idxs:
            if idx < 0:
                continue
            if idx >= len(self.particles):
                err = f"Mother index {idx + 1} out of range for event with {len(self.particles)} particles."
                raise IndexError(err)
            out.append(idx)
        return out

    def mothers(self, particle: LHEParticle) -> list[LHEParticle]:
        """
        Return a list of the particle's mothers.
        """
        return [self.particles[idx] for idx in self.mother_indices(particle)]

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
class LesHouchesEvents:
    """
    Represents an LHE file as a dataclass.
    """

    init: LHEInit
    """Init block"""
    events: Iterable[LHEEvent] = field(default_factory=list)
    """Event block"""
    header: Optional[LHEHeader] = None
    """Header block"""
    comment: Optional[str] = None
    """Comment block"""
    version: Optional[str] = None
    """Version of the LHE file"""
    extra_attributes: dict[str, str] = field(default_factory=dict)
    """Attributes of the root LesHouchesEvents element"""

    def __post_init__(self) -> None:
        """Remove schema typed owned information from attributes dict to avoid duplication and potential inconsistencies."""
        version = self.extra_attributes.pop("version", None)
        if self.version is None:
            self.version = version

    @property
    def attributes(self) -> dict[str, str]:
        """Return all the attributes of the root LesHouchesEvents element, including the version."""
        attrs = {}
        if self.version is not None:
            attrs["version"] = self.version
        # class schema typed attributes take precedence over extra_attributes in case of overlap to avoid inconsistencies
        return {**self.extra_attributes, **attrs}

    def write(
        self, output_stream: TWriteable, rwgt: bool = True, weights: bool = False
    ) -> TWriteable:
        """
        Write the LHE file to an output stream.
        """
        output_stream.write(_open_xml_tag("LesHouchesEvents", self.attributes) + "\n")
        if self.comment is not None:
            output_stream.write(f"<!-- {self.comment} -->\n")
        if self.header is not None:
            output_stream.write(self.header.tolhe() + "\n")
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
                    context = ET.iterparse(fileobj, events=["start", "end", "comment"])
                    _, root = next(context)  # Get the root element

                    if root.tag != "LesHouchesEvents":
                        err = "Root element is not <LesHouchesEvents>."
                        raise ValueError(err)
                    else:
                        lhef.extra_attributes = root.attrib.copy()
                        # Re-run post-init now that extra_attributes is populated;
                        # construction used an empty dict so version was not set yet.
                        lhef.__post_init__()

                    # We do not allow other xml tags before <header> or <init>
                    event, element = next(context)  # Get the first element in the file
                    # look for optional header first
                    if event == "comment":
                        # Here we extract e.g. the POWHEG run card stored in first <!-- ... --> comment block before the header
                        lhef.comment = element.text.strip() if element.text else None
                        event, element = next(
                            context
                        )  # Get the next element in the file after the comment
                    if element.tag == "header" and event == "start":
                        lhef.header = LHEHeader._fromcontext(root, context)
                        event, element = next(
                            context
                        )  # Get the second element in the file
                    else:
                        lhef.header = None
                    if element.tag == "init" and event == "start":
                        lheinit = LHEInit._fromcontext(root, context)
                        lhef.init = lheinit
                    else:
                        err = "No <init> block found in the LHE file."
                        raise ValueError(err)

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
                        root, context, lhef.header, with_attributes
                    )

            except ET.ParseError as excep:
                warnings.warn(f"Parse Error: {excep}", RuntimeWarning, stacklevel=1)
                return

        lhef = cls(
            version=None,  # dummy version, will be replaced
            # dummy init, will be replaced
            init=LHEInit(
                initInfo=LHEInitInfo(0, 0, 0.0, 0.0, 0, 0, 0, 0, 0, 0),
                procInfo=[],
                generators=[],
            ),
            header=None,
            events=[],
            comment=None,
        )
        events = _generator(lhef)
        try:
            next(events)  # advance to read lheinit and version
        except StopIteration:
            # If generator stops without yielding, it means no init was read
            err = "No or faulty <header>/<init> block found in the LHE file."
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


# Backwards compatibility
LHEFile = LesHouchesEvents


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


def _open_write_file(filepath: str, gz: bool = False) -> TextIO:
    if filepath.endswith((".gz", ".gzip")) or gz:
        return gzip.open(filepath, "wt")
    return open(filepath, "w")


# we import this later to avoid circular imports
from .awkward import to_awkward  # noqa: E402
