"""
`Awkward array <https://github.com/scikit-hep/awkward>`_ interface for `pylhe`.
"""

from collections.abc import Iterable

import awkward as ak  # type: ignore[import-untyped]
import vector

from pylhe import LHEEvent

__all__ = ["to_awkward"]


def __dir__() -> list[str]:
    return __all__


def to_awkward(event_iterable: Iterable[LHEEvent]) -> ak.Array:
    """Convert an iterable of LHEEvent instances to an Awkward-Array.

    Uses Awkward's ArrayBuilder to construct the array by iterating over the events.
    The events_iterable should yield instances of LHEEvent.
    This is typically created by one of the reading functions pylhe provides like
    pylhe.LHEFile.fromfile(filepath).events.

    Args:
        event_iterable (iterable): An iterable of LHEEvent instances.

    Returns:
        awkward.Array: An Awkward array of all the events.
    """

    builder = ak.ArrayBuilder()
    for event in event_iterable:
        with builder.record(name="Event"):
            builder.field("eventinfo")
            with builder.record(name="EventInfo"):
                ei = event.eventinfo
                builder.field("nparticles").integer(ei.nparticles)
                builder.field("pid").integer(ei.pid)
                builder.field("weight").real(ei.weight)
                builder.field("scale").real(ei.scale)
                builder.field("aqed").real(ei.aqed)
                builder.field("aqcd").real(ei.aqcd)
            if event.weights != {}:
                builder.field("weights")
                with builder.record(name="Weights"):
                    for label, w in event.weights.items():
                        builder.field(label).real(w)
            builder.field("particles")
            with builder.list():
                for particle in event.particles:
                    with builder.record(name="Particle"):
                        builder.field("vector")
                        with builder.record(name="Momentum4D"):
                            builder.field("px").real(particle.px)
                            builder.field("py").real(particle.py)
                            builder.field("pz").real(particle.pz)
                            builder.field("e").real(particle.e)
                        builder.field("id").integer(particle.id)
                        builder.field("status").integer(particle.status)
                        builder.field("mother1").integer(particle.mother1)
                        builder.field("mother2").integer(particle.mother2)
                        builder.field("color1").integer(particle.color1)
                        builder.field("color2").integer(particle.color2)
                        builder.field("m").real(particle.m)
                        builder.field("lifetime").real(particle.lifetime)
                        builder.field("spin").real(particle.spin)
    return builder.snapshot()  # build the final awkward array


# Used to register Awkward behaviors
class Particle:
    pass


class Event:
    pass


class EventInfo:
    pass


class Weights:
    pass


# Register Awkward behaviors
# See https://awkward-array.org/doc/main/reference/generated/ak.mixin_class.html
# and https://awkward-array.org/doc/main/reference/ak.behavior.html#mixin-decorators
vector.register_awkward()
ak.mixin_class(ak.behavior)(Particle)
ak.mixin_class(ak.behavior)(Event)
ak.mixin_class(ak.behavior)(EventInfo)
ak.mixin_class(ak.behavior)(Weights)
