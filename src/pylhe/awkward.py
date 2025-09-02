"""
`Awkward array <https://github.com/scikit-hep/awkward>`_ interface for `pylhe`.
"""

import awkward as ak
import vector

__all__ = ["to_awkward"]


def __dir__():
    return __all__


def to_awkward(event_iterable):
    """Convert an iterable of LHEEvent instances to an Awkward-Array.

    Uses Awkward's ArrayBuilder to construct the array by iterating over the events.
    The events_iterable should yield instances of LHEEvent.
    This is typically created by one of the reading functions pylhe provides like
    pylhe.read_lhe(filepath), pylhe.read_lhe_with_attributes(filepath), or pylhe.read_lhe_file(filepath).events.

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
                for fname in event.eventinfo.fieldnames:
                    builder.field(fname).real(getattr(event.eventinfo, fname))
            if (event.weights is not None) and (event.weights != {}):
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
                            for fname in ["px", "py", "pz", "e"]:
                                builder.field(fname).real(getattr(particle, fname))
                        for fname in particle.fieldnames:
                            if fname not in ["px", "py", "pz", "e"]:
                                builder.field(fname).real(getattr(particle, fname))
    return builder.snapshot()  # awkward array


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
