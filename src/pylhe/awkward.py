import awkward as ak
import vector

__all__ = ["register_awkward", "to_awkward"]


# Python 3.7+
def __dir__():
    return __all__


def register_awkward():
    """
    .. deprecated:: 0.6.0
       Remove use of :func:`~pylhe.awkward.register_awkward` as registration
       is automatic.
    .. warning:: :func:`~pylhe.awkward.register_awkward` will be removed in
     ``pylhe`` ``v0.8.0``.
    """
    import warnings

    warnings.warn(
        "pylhe.awkward.register_awkward is deprecated as of pylhe v0.6.0 and will be removed in pylhe v0.8.0."
        + " Please remove use of pylhe.awkward.register_awkward in favor of automatic registration.",
        category=DeprecationWarning,
        stacklevel=2,  # Raise to user level
    )


def to_awkward(event_iterable):
    """Convert iterable of LHEEvent instances to Awkward-Array."""

    builder = ak.ArrayBuilder()
    for event in event_iterable:
        with builder.record(name="Event"):
            builder.field("eventinfo")
            with builder.record(name="EventInfo"):
                for fname in event.eventinfo.fieldnames:
                    builder.field(fname).real(getattr(event.eventinfo, fname))
            builder.field("particles")
            with builder.list():
                for particle in event.particles:
                    with builder.record(name="Particle"):
                        builder.field("vector")
                        with builder.record(name="Momentum4D"):
                            spatial_momentum_map = {
                                "x": "px",
                                "y": "py",
                                "z": "pz",
                                "t": "e",
                            }
                            for key, value in spatial_momentum_map.items():
                                builder.field(key).real(getattr(particle, value))
                        for fname in particle.fieldnames:
                            if fname not in ["px", "py", "pz", "e"]:
                                builder.field(fname).real(getattr(particle, fname))
    return builder.snapshot()  # awkward array


class Particle:
    pass


class Event:
    pass


class EventInfo:
    pass


# Register Awkward behaviors
vector.register_awkward()
ak.mixin_class(ak.behavior)(Particle)
ak.mixin_class(ak.behavior)(Event)
ak.mixin_class(ak.behavior)(EventInfo)
