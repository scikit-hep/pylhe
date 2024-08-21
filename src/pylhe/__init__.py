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
    "LHEInitInfo",
    "LHEParticle",
    "LHEProcInfo",
    "read_lhe",
    "read_lhe_init",
    "read_lhe_with_attributes",
    "read_num_events",
    "register_awkward",
    "to_awkward",
]


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
        if rwgt:
            if self.weights:
                sweights = "<rwgt>\n"
                for k, v in self.weights.items():
                    sweights += f" <wgt id='{k}'>{v:11.4e}</wgt>\n"
                sweights += "</rwgt>\n"
        if weights:
            if self.weights:
                sweights = "<weights>\n"
                for k, v in self.weights.items():
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


class LHEEventInfo:
    fieldnames = ["nparticles", "pid", "weight", "scale", "aqed", "aqcd"]

    def __init__(self, **kwargs):
        if set(kwargs.keys()) != set(self.fieldnames):
            raise RuntimeError(
                f"LHEEventInfo constructor expects fields {self.fieldnames}! Got {kwargs.keys()}."
            )
        for k, v in kwargs.items():
            setattr(self, k, v)

    def tolhe(self):
        """
        Return the event info as a string in LHE format.

        Returns:
            str: The event info as a string in LHE format.
        """
        return "{:3d} {:6d} {: 15.10e} {: 15.10e} {: 15.10e} {: 15.10e}".format(
            *[int(getattr(self, f)) for f in self.fieldnames[:2]],
            *[getattr(self, f) for f in self.fieldnames[2:]],
        )

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

    def tolhe(self):
        """
        Return the particle as a string in LHE format.

        Returns:
            str: The particle as a string in LHE format.
        """
        return "{:5d} {:3d} {:3d} {:3d} {:3d} {:3d} {: 15.8e} {: 15.8e} {: 15.8e} {: 15.8e} {: 15.8e} {: 10.4e} {: 10.4e}".format(
            *[int(getattr(self, f)) for f in self.fieldnames[:6]],
            *[getattr(self, f) for f in self.fieldnames[6:]],
        )

    def mothers(self):
        first_idx = int(self.mother1) - 1
        second_idx = int(self.mother2) - 1
        return [
            self.event.particles[idx] for idx in {first_idx, second_idx} if idx >= 0
        ]


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
        for elem in elem:
            _indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


class LHEInit(dict):
    """Store the <init> block as dict."""

    fieldnames = ["initInfo", "procInfo" "weightgroup", "LHEVersion"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tolhe(self):
        """
        Return the init block as a string in LHE format.

        Returns:
            str: The init block as a string in LHE format.
        """
        # weightgroups to xml
        root = ET.Element("initrwgt")
        for k, v in self["weightgroup"].items():
            weightgroup_elem = ET.SubElement(root, "weightgroup", **v["attrib"])
            for key, value in v["weights"].items():
                weight_elem = ET.SubElement(
                    weightgroup_elem, "weight", **value["attrib"]
                )
                weight_elem.text = value["name"]
        _indent(root)
        sweightgroups = ET.tostring(root, encoding="unicode", method="xml")

        return (
            "<init>\n"
            + self["initInfo"].tolhe()
            + "\n"
            + "\n".join([p.tolhe() for p in self["procInfo"]])
            + "\n"
            + f"{sweightgroups}"
            + "</init>"
        )

    # custom backwards compatibility get for dict
    def __getitem__(self, key):
        if key not in self:
            return self["initInfo"][key]
        else:
            return super().__getitem__(key)

    # custom backwards compatibility set for dict
    def __setitem__(self, key, value):
        if key not in self:
            self["initInfo"][key] = value
        else:
            self.super().__setitem__(key, value)


class LHEInitInfo(dict):
    """Store the first line of the <init> block as dict."""

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tolhe(self):
        """
        Return the init info block as a string in LHE format.

        Returns:
            str: The init info block as a string in LHE format.
        """
        return (
            " {: 6d} {: 6d} {: 14.7e} {: 14.7e} {: 5d} {: 5d} {: 5d} {: 5d} {: 5d} {: 5d}"
        ).format(
            int(self["beamA"]),
            int(self["beamB"]),
            self["energyA"],
            self["energyB"],
            int(self["PDFgroupA"]),
            int(self["PDFgroupB"]),
            int(self["PDFsetA"]),
            int(self["PDFsetB"]),
            int(self["weightingStrategy"]),
            int(self["numProcesses"]),
        )

    @classmethod
    def fromstring(cls, string):
        return cls(**dict(zip(cls.fieldnames, map(float, string.split()))))


class LHEProcInfo(dict):
    """Store the process info block as dict."""

    fieldnames = ["xSection", "error", "unitWeight", "procId"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def tolhe(self):
        """
        Return the process info block as a string in LHE format.

        Returns:
            str: The process info block as a string in LHE format.
        """
        return ("{: 14.7e} {: 14.7e} {: 14.7e} {: 5d}").format(
            self["xSection"], self["error"], self["unitWeight"], int(self["procId"])
        )

    @classmethod
    def fromstring(cls, string):
        return cls(**dict(zip(cls.fieldnames, map(float, string.split()))))


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
                initDict["initInfo"] = LHEInitInfo.fromstring(data[0])
                initDict["procInfo"] = [LHEProcInfo.fromstring(d) for d in data[1:]]
            if element.tag == "initrwgt":
                initDict["weightgroup"] = {}
                index = 0
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
                                "index": index,
                            }
                            index += 1

                        initDict["weightgroup"][wg_type] = _temp
            if element.tag == "LesHouchesEvents":
                initDict["LHEVersion"] = float(element.attrib["version"])
            if element.tag == "event":
                break
    return LHEInit(**initDict)


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


def read_lhe_with_attributes(filepath):
    """
    Iterate through file, similar to read_lhe but also set
    weights and attributes.
    """
    index_map = None
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
                        if sub.tag == "weights":
                            if not index_map:
                                index_map = _get_index_to_id_map(
                                    read_lhe_init(filepath)
                                )
                            for i, w in enumerate(sub.text.split()):
                                if w and not index_map[i] in eventdict["weights"]:
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


def write_lhe_string(lheinit, lheevents, rwgt=True, weights=False):
    """
    Return the LHE file as a string.
    """
    s = f"<LesHouchesEvents version=\"{lheinit['LHEVersion']}\">\n"
    s += lheinit.tolhe() + "\n"
    for e in lheevents:
        s += e.tolhe(rwgt=rwgt, weights=weights) + "\n"
    s += "</LesHouchesEvents>"
    return s


def write_lhe_file(lheinit, lheevents, filepath, gz=False, rwgt=True, weights=False):
    """
    Write the LHE file.
    """
    # if filepath suffix is gz, write as gz
    if filepath.endswith(".gz") or filepath.endswith(".gzip") or gz:
        with gzip.open(filepath, "wt") as f:
            f.write(write_lhe_string(lheinit, lheevents, rwgt=rwgt, weights=weights))
    else:
        with open(filepath, "w") as f:
            f.write(write_lhe_string(lheinit, lheevents, rwgt=rwgt, weights=weights))
