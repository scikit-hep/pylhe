import numpy as np
import vector as vc
import awkward as ak


def register_awkward():
    vc.register_awkward()
    ak.mixin_class(ak.behavior)(Particle)
    ak.mixin_class(ak.behavior)(Event)
    ak.mixin_class(ak.behavior)(EventInfo)


def to_akward(event_iterable):
    builder = ak.ArrayBuilder()
    for e in event_iterable:
        with builder.record(name="Event"):
            builder.field("eventinfo")
            with builder.record(name="EventInfo"):
                for fname in e.eventinfo.fieldnames:
                    builder.field(fname).real(getattr(e.eventinfo, fname))
            builder.field("particles")
            with builder.list():
                for p in e.particles:
                    with builder.record(name="Particle"):
                        builder.field("vector")
                        with builder.record(name="Momentum4D"):
                            for f, k in {
                                "x": "px",
                                "y": "py",
                                "z": "pz",
                                "t": "e",
                            }.items():
                                builder.field(f).real(getattr(p, k))
                        for fname in p.fieldnames:
                            if not fname in ["px", "py", "pz", "e"]:
                                builder.field(fname).real(getattr(p, fname))
    arr = builder.snapshot()
    return arr


class Particle:
    pass


class Event:
    pass


class EventInfo:
    pass
