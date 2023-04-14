import awkward as ak
import vector

__all__ = ["register_awkward", "to_awkward"]


# Python 3.7+
def __dir__():
    return __all__


def register_awkward():
    """This function does nothing and is merely here for backwards compatibility
    of the pylhe API

    The registration is done automatically when pylhe is imported since awkward
    is a required dependency of pylhe.

    .. deprecated:: 0.5.3
       Simply remove calls since the registration happens automatically now.
    .. warning:: :func:`~pylhe.register_awkward` will be removed in
     ``pylhe`` ``v0.7.0``.
    """
    import warnings

    warnings.warn(
        """The `pylhe.register_awkward` function does nothing and has been deprecated
            as of pylhe v0.5.3 and will be removed in pylhe v0.7.0.
            The registration now happens automatically when `pylhe` is imported,
            so calls to `pylhe.register_awkward` can be safely removed.""",
        category=DeprecationWarning,
        stacklevel=3,
    )
    pass


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
