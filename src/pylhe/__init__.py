"""
Python interface to read Les Houches Event (LHE) files.
"""

from __future__ import annotations

import enum
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
    Protocol,
    TextIO,
    TypeVar,
)
from xml.sax.saxutils import quoteattr

import graphviz  # type: ignore[import-untyped]
import h5py  # type: ignore[import-untyped]
from particle import latex_to_html_name
from particle.converters.bimap import DirectionalMaps
from particle.exceptions import MatchingIDNotFound

from pylhe import lheh5
from pylhe._version import version as __version__

__all__ = [
    "DEFAULT_FORMAT",
    "GZ_FORMAT",
    "HDF5_FORMAT",
    "HDF5_GZ_FORMAT",
    "RWGT_FORMAT",
    "RWGT_GZ_FORMAT",
    "WEIGHTS_FORMAT",
    "WEIGHTS_GZ_FORMAT",
    "LHEEvent",
    "LHEEventInfo",
    "LHEFile",
    "LHEGenerator",
    "LHEHDF5Format",
    "LHEHeader",
    "LHEInit",
    "LHEInitInfo",
    "LHEInitRWGTWeight",
    "LHEInitRWGTWeightGroup",
    "LHEOutputFormat",
    "LHEParticle",
    "LHEProcInfo",
    "LHEWeightFormat",
    "LHEXMLFormat",
    "__version__",
    "to_awkward",
]


def __dir__() -> list[str]:
    return __all__


# retrieve mapping of PDG ID to particle name as LaTeX string
_PDGID2LaTeXNameMap, _ = DirectionalMaps("PDGID", "LATEXNAME", converters=(str, str))

PathLike = str | bytes | os.PathLike[str] | os.PathLike[bytes]


class LHEWeightFormat(enum.Enum):
    """Selects how event weights are serialized in LHE output."""

    RWGT = "rwgt"  # <rwgt><wgt id=...>...</wgt></rwgt> block
    WEIGHTS = "weights"  # <weights>...</weights> block
    NONE = "none"  # no weights block emitted


class LHEVersion(enum.Enum):
    """Selects the LHE XML version."""

    V1 = "1.0"  # Only comment, <header>, <init> and <event> blocks
    # V2 = "2.0" # Not supported as of now since most attributes have been removed in V3 again...
    V3 = "3.0"  # Also <scales>, <initrwgt>, <rwgt>, <weights> and <generator> blocks


@dataclass(slots=True, frozen=True)
class LHEXMLFormat:
    """Selects the XML format."""

    version: LHEVersion = LHEVersion.V3
    indent: str = "  "
    """indentation string for XML output"""
    compress: bool = False
    """compress as gzip"""

    weights: LHEWeightFormat = LHEWeightFormat.RWGT

    eventinfo: str = "{nparticles:3d} {pid:6d} {weight: 15.10e} {scale: 15.10e} {aqed: 15.10e} {aqcd: 15.10e}"
    particle: str = "{id:5d} {status:3d} {mother1:3d} {mother2:3d} {color1:3d} {color2:3d} {px: 15.8e} {py: 15.8e} {pz: 15.8e} {e: 15.8e} {m: 15.8e} {lifetime: 10.4e} {spin: 10.4e}"
    initinfo: str = " {beamA: 6d} {beamB: 6d} {energyA: 14.7e} {energyB: 14.7e} {PDFgroupA: 5d} {PDFgroupB: 5d} {PDFsetA: 5d} {PDFsetB: 5d} {weightingStrategy: 5d} {numProcesses: 5d}"
    procinfo: str = "{xSection: 14.7e} {error: 14.7e} {unitWeight: 14.7e} {procId: 5d}"


@dataclass(slots=True, frozen=True)
class LHEHDF5Format:
    """Selects the HDF5 format."""

    compression: str | None = None
    """Dataset compression filter passed to h5py, e.g. ``\"gzip\"``."""
    compression_opts: int | None = None
    """Optional compression level/options passed to h5py."""
    shuffle: bool = False
    """Whether to enable the HDF5 shuffle filter."""
    event_chunk_rows: int = 1024
    """Chunk size in rows for the events dataset."""
    particle_chunk_rows: int = 8192
    """Chunk size in rows for the particles dataset."""


LHEOutputFormat = LHEXMLFormat | LHEHDF5Format


# User convenience presets for common formats
DEFAULT_FORMAT = LHEXMLFormat()
"""Default output format with indentation, RWGT weights block and plain text file format."""
GZ_FORMAT = LHEXMLFormat(compress=True)
"""Output format for gzip compressed files, with (default) RWGT weights block."""
RWGT_FORMAT = LHEXMLFormat(weights=LHEWeightFormat.RWGT)
"""Output format with RWGT weights block and (default) plain text file format."""
WEIGHTS_FORMAT = LHEXMLFormat(weights=LHEWeightFormat.WEIGHTS)
"""Output format with WEIGHTS weights block and (default) plain text file format."""
RWGT_GZ_FORMAT = LHEXMLFormat(weights=LHEWeightFormat.RWGT, compress=True)
"""Output format with RWGT weights block and gzip compressed file format."""
WEIGHTS_GZ_FORMAT = LHEXMLFormat(weights=LHEWeightFormat.WEIGHTS, compress=True)
"""Output format with WEIGHTS weights block and gzip compressed file format."""
NO_WEIGHTS_FORMAT = LHEXMLFormat(weights=LHEWeightFormat.NONE)
"""Output format with no WEIGHTS weights block and (default) plain text file format."""
HDF5_FORMAT = LHEHDF5Format()
"""Output format for HDF5-based LHEH5 files."""
HDF5_GZ_FORMAT = LHEHDF5Format(compression="gzip", compression_opts=4, shuffle=True)
"""Output format for HDF5-based LHEH5 files with gzip-compressed datasets."""


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


@dataclass(slots=True)
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

    def tolhe(self, lheformat: LHEXMLFormat = DEFAULT_FORMAT) -> str:
        """
        Return the event info as a string in LHE XML format.

        Returns:
            str: The event info as a string in LHE XML format.
        """
        return lheformat.eventinfo.format(
            nparticles=self.nparticles,
            pid=self.pid,
            weight=self.weight,
            scale=self.scale,
            aqed=self.aqed,
            aqcd=self.aqcd,
        )

    @classmethod
    def fromstring(cls, string: str) -> LHEEventInfo:
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


@dataclass(slots=True)
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

    @classmethod
    def fromstring(cls, string: str) -> LHEParticle:
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

    def tolhe(self, lheformat: LHEXMLFormat = DEFAULT_FORMAT) -> str:
        """
        Return the particle as a string in LHE XML format.

        Returns:
            str: The particle as a string in LHE XML format.
        """
        return lheformat.particle.format(
            id=self.id,
            status=self.status,
            mother1=self.mother1,
            mother2=self.mother2,
            color1=self.color1,
            color2=self.color2,
            px=self.px,
            py=self.py,
            pz=self.pz,
            e=self.e,
            m=self.m,
            lifetime=self.lifetime,
            spin=self.spin,
        )


def _indent(root: ET.Element, lheformat: LHEXMLFormat = DEFAULT_FORMAT) -> None:
    ET.indent(root, space=lheformat.indent)
    root.tail = "\n"


@dataclass(slots=True)
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

    def tolhe(self, lheformat: LHEXMLFormat = DEFAULT_FORMAT) -> str:
        """
        Return the init info block as a string in LHE XML format.

        Returns:
            str: The init info block as a string in LHE XML format.
        """
        return lheformat.initinfo.format(
            beamA=self.beamA,
            beamB=self.beamB,
            energyA=self.energyA,
            energyB=self.energyB,
            PDFgroupA=self.PDFgroupA,
            PDFgroupB=self.PDFgroupB,
            PDFsetA=self.PDFsetA,
            PDFsetB=self.PDFsetB,
            weightingStrategy=self.weightingStrategy,
            numProcesses=self.numProcesses,
        )

    @classmethod
    def fromstring(cls, string: str) -> LHEInitInfo:
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


@dataclass(slots=True)
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
    npLO: int | None = None
    """LO final-state multiplicity tag for HDF5 procInfo tables"""
    npNLO: int | None = None
    """Born-level multiplicity tag for HDF5 procInfo tables"""

    def tolhe(self, lheformat: LHEXMLFormat = DEFAULT_FORMAT) -> str:
        """
        Return the process info block as a string in LHE XML format.

        Returns:
            str: The process info block as a string in LHE XML format.
        """
        if self.npLO is not None:
            warnings.warn(
                "LHEH5 field npLO has no equivalent in the LHE XML format and will be ignored.",
                UserWarning,
                stacklevel=2,
            )
        if self.npNLO is not None:
            warnings.warn(
                "LHEH5 field npNLO has no equivalent in the LHE XML format and will be ignored.",
                UserWarning,
                stacklevel=2,
            )
        return lheformat.procinfo.format(
            xSection=self.xSection,
            error=self.error,
            unitWeight=self.unitWeight,
            procId=self.procId,
        )

    @classmethod
    def fromstring(cls, string: str) -> LHEProcInfo:
        """
        Create an `LHEProcInfo` instance from a string in LHE format.
        """
        values = string.split()
        return cls(
            xSection=float(values[0]),
            error=float(values[1]),
            unitWeight=float(values[2]),
            procId=int(float(values[3])),
            npLO=None,
            npNLO=None,
        )


@dataclass(slots=True)
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


@dataclass(slots=True)
class LHEInitRWGTWeightGroup:
    """Information about a weight group."""

    name: str | None = (
        None  # Normally this is required, i.e. not Optional, but old Madgraph-2.0.0 uses 'type' instead of 'name'...
    )
    """Name of the weight group"""
    combine: str | None = None
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


InitRWGTEntry = LHEInitRWGTWeight | LHEInitRWGTWeightGroup


@dataclass(slots=True)
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

    def tolhe(self, lheformat: LHEXMLFormat = DEFAULT_FORMAT) -> str:
        """
        Return the init block as a string in LHE XML format.

        Returns:
            str: The init block as a string in LHE XML format.
        """
        match lheformat.version:
            case LHEVersion.V3:
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
                _indent(root, lheformat)
                return ET.tostring(root, encoding="unicode", method="xml")
            case LHEVersion.V1:
                return ""


@dataclass(slots=True)
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

    def tolhe(self, lheformat: LHEXMLFormat = DEFAULT_FORMAT) -> str:
        """Return the header block as a string in LHE XML format."""
        root = ET.Element("header", attrib=self.attributes)
        for element in self.extra_elements:
            root.append(_copy_xml_element(element))
        if self.initrwgt.entries:
            sinit = self.initrwgt.tolhe(lheformat=lheformat)
            if sinit:
                root.append(ET.fromstring(sinit))

        _indent(root, lheformat=lheformat)
        return ET.tostring(root, encoding="unicode", method="xml")

    @classmethod
    def _fromcontext(
        cls, _root: ET.Element, context: Iterator[tuple[str, ET.Element]]
    ) -> LHEHeader:
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


@dataclass(slots=True)
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

    def tolhe(self, lheformat: LHEXMLFormat = DEFAULT_FORMAT) -> str:
        """
        Return the generator information as a string in LHE XML format.

        Returns:
            str: The generator information as a string in LHE XML format.
        """
        match lheformat.version:
            case LHEVersion.V3:
                opening_tag = _open_xml_tag("generator", self.attributes)
                return f"{opening_tag}{self.description}</generator>"
            case LHEVersion.V1:
                return ""


@dataclass(slots=True)
class LHEInit:
    """Store the <init> block as a dataclass."""

    initInfo: LHEInitInfo
    """Init information"""
    procInfo: list[LHEProcInfo]
    """Process information"""
    generators: list[LHEGenerator]
    """Generator information"""

    def tolhe(self, lheformat: LHEXMLFormat = DEFAULT_FORMAT) -> str:
        """
        Return the init block as a string in LHE XML format.

        Returns:
            str: The init block as a string in LHE XML format.
        """
        return (
            "<init>\n"
            + self.initInfo.tolhe(lheformat=lheformat)
            + "\n"
            + "\n".join(
                [p.tolhe(lheformat=lheformat) for p in self.procInfo]
                + [
                    s for g in self.generators if (s := g.tolhe(lheformat=lheformat))
                ]  # We remove empty strings here since otherwise empty lines would be added to the init block, which is not allowed
            )
            + "\n"
            + "</init>"
        )

    @classmethod
    def _fromcontext(
        cls, _root: ET.Element, context: Iterator[tuple[str, ET.Element]]
    ) -> LHEInit:
        initInfo = None
        procInfo = []
        generators = []

        for event, element in context:
            if (
                element.tag == "generator"
                and "version" in element.attrib
                and event == "end"
            ):
                # lhe-v3 has name and version attributes; some lhe-v2 files only provide version as an attribute (text is stored in `description`)
                generator = LHEGenerator(
                    name=element.attrib.get("name", ""),
                    version=element.attrib["version"],
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


@dataclass(slots=True)
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
    _graph: graphviz.Digraph | None = field(default=None, repr=False, compare=False)
    """Stores the graph representation of the event generated after first access of the property `lheevent.graph`"""

    def tolhe(self, lheformat: LHEXMLFormat = DEFAULT_FORMAT) -> str:
        """
        Return the event as a string in LHE XML format.

        Args:
            lheformat (LHEXMLFormat): How to serialize the event, see the `LHEXMLFormat` class.

        Returns:
            str: The event as a string in LHE XML format.
        """
        sweights = ""
        sscales = ""
        match lheformat.version:
            case LHEVersion.V3:
                if lheformat.weights is LHEWeightFormat.RWGT and self.weights:
                    sweights = "<rwgt>\n"
                    for k, v in self.weights.items():
                        sweights += f" <wgt id='{k}'>{v:11.4e}</wgt>\n"
                    sweights += "</rwgt>\n"
                elif lheformat.weights is LHEWeightFormat.WEIGHTS and self.weights:
                    sweights = "<weights>\n"
                    for v in self.weights.values():
                        sweights += f"{v:11.4e}\n"
                    sweights += "</weights>\n"

                if self.scales:
                    sscales = (
                        "<scales "
                        + " ".join(f"{k}='{v}'" for k, v in self.scales.items())
                        + "/>\n"
                    )
            case LHEVersion.V1:
                sweights = ""
                sscales = ""

        soptional = ""
        if self.optional:
            soptional = "\n".join(self.optional) + "\n"

        return (
            _open_xml_tag("event", self.attributes)
            + "\n"
            + self.eventinfo.tolhe(lheformat=lheformat)
            + "\n"
            + "\n".join([p.tolhe(lheformat=lheformat) for p in self.particles])
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
        context: Iterator[tuple[str, ET.Element]],
        lheheader: LHEHeader | None = None,
        with_attributes: bool = True,
    ) -> Iterator[LHEEvent]:
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
                            weight_values = sub.text.split()
                            if len(weight_values) > len(index_map):
                                err = (
                                    f"event <weights> block has {len(weight_values)} entries"
                                    f" but <initrwgt> declares only {len(index_map)}"
                                )
                                raise ValueError(err)
                            for i, w in enumerate(weight_values):
                                if index_map[i] not in weights:
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
        include: Iterable[str] | None = None,
        exclude: Iterable[str] | None = None,
        **kwargs: dict[str, Any],
    ) -> Any:
        """
        IPython display helper.
        """
        return self.graph._repr_mimebundle_(include=include, exclude=exclude, **kwargs)


@dataclass(slots=True)
class LesHouchesEvents:
    """
    Represents an LHE file as a dataclass.
    """

    init: LHEInit
    """Init block"""
    events: Iterable[LHEEvent] = field(default_factory=list)
    """Event block"""
    header: LHEHeader | None = None
    """Header block"""
    comment: str | None = None
    """Comment block"""
    version: str | None = None  # None for undefined or LHEH5
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
        self, output_stream: TWriteable, lheformat: LHEXMLFormat = DEFAULT_FORMAT
    ) -> TWriteable:
        """
        Write the LHE file to an output stream as LHE XML.

        Args:
            output_stream (TWriteable): Output stream to write the LHE file to.
            lheformat (LHEXMLFormat): How to serialize the event, see the `LHEXMLFormat` class.

        Returns:
            TWriteable: The output stream with the LHE file written to it.

        """
        write_attributes = self.attributes.copy()
        # Write the LHE file as v3.0, regardless of the version attribute in the LesHouchesEvents object, since pylhe always writes LHE v3.0 files as of now.
        # Later it could be an option in LHEXMLFormat to set the version.
        write_attributes["version"] = lheformat.version.value
        output_stream.write(_open_xml_tag("LesHouchesEvents", write_attributes) + "\n")
        if self.comment is not None:
            output_stream.write(f"<!-- {self.comment} -->\n")
        if self.header is not None:
            output_stream.write(self.header.tolhe(lheformat=lheformat) + "\n")
        output_stream.write(self.init.tolhe(lheformat=lheformat) + "\n")
        for e in self.events:
            output_stream.write(e.tolhe(lheformat=lheformat) + "\n")
        output_stream.write("</LesHouchesEvents>")
        return output_stream

    def tolhe(self, lheformat: LHEXMLFormat = DEFAULT_FORMAT) -> str:
        """
        Return the LHE file as a string.

        Args:
            lheformat (LHEXMLFormat): How to serialize the event, see the `LHEXMLFormat` class.
        """
        return self.write(io.StringIO(), lheformat=lheformat).getvalue()

    def tofile(
        self,
        filepath: PathLike,
        lheformat: LHEOutputFormat
        | None = None,  # default format is None because we do file name suffix detection in _open_write_file
    ) -> None:
        """
        Write the LHE file as LHE.

        Args:
            filepath (PathLike): Path to the output file.
            lheformat (LHEOutputFormat): How to serialize the event, see the `LHEOutputFormat` class.
        """
        # autodetect default format from suffix if not provided
        if lheformat is None:
            lheformat = _parse_lheformat_from_filepath(filepath)
        if isinstance(lheformat, LHEHDF5Format):
            with h5py.File(filepath, "w") as f:
                lheh5.write(self, f, lheformat=lheformat)
        else:
            with _open_write_file(filepath, lheformat=lheformat) as f:
                self.write(f, lheformat=lheformat)

    @classmethod
    def fromstring(
        cls, string: str, with_attributes: bool = True, generator: bool = True
    ) -> LHEFile:
        """
        Create an LHEFile instance from a string in LHE format.

        Args:
            string (str): String containing the LHE file content.
            with_attributes (bool): Whether to parse attributes from the LHE file. Default is True.
            generator (bool): Whether to return a generator for events. Default is True.

        """
        return cls.frombuffer(
            io.StringIO(string), with_attributes=with_attributes, generator=generator
        )

    @classmethod
    def fromfile(
        cls, filepath: PathLike, with_attributes: bool = True, generator: bool = True
    ) -> LHEFile:
        """
        Read an LHE file and return an LHEFile object.

        Args:
            filepath (PathLike): Path to the LHE file.
            with_attributes (bool): Whether to parse attributes from the LHE file. Default is True.
            generator (bool): Whether to return a generator for events. Default is True.

        """
        return cls.frombuffer(
            _extract_fileobj(filepath),
            with_attributes=with_attributes,
            generator=generator,
        )

    @classmethod
    def frombuffer(
        cls,
        fileobject: io.BufferedReader
        | gzip.GzipFile
        | h5py.File
        | io.StringIO
        | TextIO
        | BinaryIO,
        with_attributes: bool = True,
        generator: bool = True,
    ) -> LHEFile:
        """
        Read an LHE file and return an LHEFile object.
        """

        if isinstance(fileobject, h5py.File):
            init = lheh5.read_init(fileobject)

            def _hdf5_generator() -> Iterator[LHEEvent]:
                with fileobject as h5:
                    yield from lheh5.read_iter_events(h5)

            events = _hdf5_generator()
            return LesHouchesEvents(
                init=init,
                events=events if generator else list(events),
                version=None,  # We leave the version as None since HDF5 versioning is unrelated to LHE XML versioning.
            )

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
                if isinstance(fileobj, h5py.File):
                    return lheh5.count_events(fileobj)
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


def _extract_fileobj(
    filepath: PathLike,
) -> io.BufferedReader | gzip.GzipFile | h5py.File:
    """
    Checks to see if a file is compressed, and if so, extract it with gzip
    so that the uncompressed file can be returned.
    It returns a file object containing XML data that will be ingested by
    ``xml.etree.ElementTree.iterparse``.

    Args:
        filepath: A path-like object or str.

    Returns:
        _io.BufferedReader or gzip.GzipFile or h5py.File: A file object containing XML or HDF5 data.
    """
    is_gzip = False
    is_hdf5 = False

    with open(filepath, "rb") as gzip_file:
        # GZIP magic number per RFC 1952 section 2.3.1
        is_gzip = gzip_file.read(2) == b"\x1f\x8b"

    with open(filepath, "rb") as f:
        # HDF magic number per The HDF5 Field Guide II.A.
        is_hdf5 = f.read(8) == b"\x89HDF\r\n\x1a\n"

    if is_gzip:
        return gzip.GzipFile(filepath)
    if is_hdf5:
        return h5py.File(filepath, "r")
    return open(filepath, "rb")


def _parse_lheformat_from_filepath(
    filepath: PathLike,
) -> LHEOutputFormat:
    """
    Determine the LHEOutputFormat based on the file extension.

    Args:
        filepath: A path-like object or str.

    Returns:
        LHEOutputFormat: The determined output format.
    """
    filepath_str = os.fsdecode(os.fspath(filepath))
    # TODO think about potential .hdf5.gz
    if filepath_str.endswith((".h5", ".hdf5", "lheh5")):
        return HDF5_FORMAT
    if filepath_str.endswith((".gz", ".gzip")):
        return GZ_FORMAT
    return DEFAULT_FORMAT


def _open_write_file(filepath: PathLike, lheformat: LHEXMLFormat) -> TextIO:
    """
    Open a file for writing, determining the format based on the file extension or provided LHEXMLFormat.

    Args:
        filepath: A path-like object or str.
        lheformat: The LHEXMLFormat to use for writing.
    """
    if lheformat.compress:
        return gzip.open(filepath, "wt")
    return open(filepath, "w")


# we import this later to avoid circular imports
from .awkward import to_awkward  # noqa: E402
