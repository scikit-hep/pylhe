import pytest

import pylhe


def test_lhe_init_info_getitem_deprecation_warning():
    """Test that DeprecationWarning is raised when using __getitem__ on LHEInitInfo."""
    init_info = pylhe.LHEInitInfo(
        beamA=2212,
        beamB=2212,
        energyA=6500.0,
        energyB=6500.0,
        PDFgroupA=10800,
        PDFgroupB=10800,
        PDFsetA=0,
        PDFsetB=0,
        weightingStrategy=3,
        numProcesses=1,
    )

    with pytest.warns(
        DeprecationWarning,
        match=r'Access by `object\["beamA"\]` is deprecated and will be removed in a future version\. Use `object\.beamA` instead\.',
    ):
        _ = init_info["beamA"]


def test_lhe_init_info_setitem_deprecation_warning():
    """Test that DeprecationWarning is raised when using __setitem__ on LHEInitInfo."""
    init_info = pylhe.LHEInitInfo(
        beamA=2212,
        beamB=2212,
        energyA=6500.0,
        energyB=6500.0,
        PDFgroupA=10800,
        PDFgroupB=10800,
        PDFsetA=0,
        PDFsetB=0,
        weightingStrategy=3,
        numProcesses=1,
    )

    with pytest.warns(
        DeprecationWarning,
        match=r'Access by `object\["beamA"\]` is deprecated and will be removed in a future version\. Use `object\.beamA` instead\.',
    ):
        init_info["beamA"] = 11


def test_lhe_proc_info_getitem_deprecation_warning():
    """Test that DeprecationWarning is raised when using __getitem__ on LHEProcInfo."""
    proc_info = pylhe.LHEProcInfo(xSection=1.0, error=0.1, unitWeight=1.0, procId=1)

    with pytest.warns(
        DeprecationWarning,
        match=r'Access by `object\["xSection"\]` is deprecated and will be removed in a future version\. Use `object\.xSection` instead\.',
    ):
        _ = proc_info["xSection"]


def test_lhe_proc_info_setitem_deprecation_warning():
    """Test that DeprecationWarning is raised when using __setitem__ on LHEProcInfo."""
    proc_info = pylhe.LHEProcInfo(xSection=1.0, error=0.1, unitWeight=1.0, procId=1)

    with pytest.warns(
        DeprecationWarning,
        match=r'Access by `object\["xSection"\]` is deprecated and will be removed in a future version\. Use `object\.xSection` instead\.',
    ):
        proc_info["xSection"] = 2.0


def test_lhe_event_fieldnames_deprecation_warning():
    """Test that DeprecationWarning is raised when using fieldnames property on LHEEvent."""
    event_info = pylhe.LHEEventInfo(
        nparticles=1, pid=0, weight=1.0, scale=91.188, aqed=-1.0, aqcd=-1.0
    )
    particle = pylhe.LHEParticle(
        id=21,
        status=-1,
        mother1=0,
        mother2=0,
        color1=501,
        color2=502,
        px=0.0,
        py=0.0,
        pz=456.3,
        e=456.3,
        m=0.0,
        lifetime=0.0,
        spin=9.0,
    )
    event = pylhe.LHEEvent(eventinfo=event_info, particles=[particle])

    with pytest.warns(
        DeprecationWarning,
        match=r"The fieldnames property is deprecated and will be removed in a future version\. Use `asdict\(object\)` instead\.",
    ):
        _ = event.fieldnames


def test_lhe_event_iter_deprecation_warning():
    """Test that DeprecationWarning is raised when using __iter__ on LHEEvent."""
    event_info = pylhe.LHEEventInfo(
        nparticles=1, pid=0, weight=1.0, scale=91.188, aqed=-1.0, aqcd=-1.0
    )
    particle = pylhe.LHEParticle(
        id=21,
        status=-1,
        mother1=0,
        mother2=0,
        color1=501,
        color2=502,
        px=0.0,
        py=0.0,
        pz=456.3,
        e=456.3,
        m=0.0,
        lifetime=0.0,
        spin=9.0,
    )
    event = pylhe.LHEEvent(eventinfo=event_info, particles=[particle])

    with pytest.warns(
        DeprecationWarning,
        match=r"Dict-like iteration is deprecated and will be removed in a future version\. Use `asdict\(object\)` instead\.",
    ):
        _ = list(event)


def test_lhe_event_len_deprecation_warning():
    """Test that DeprecationWarning is raised when using __len__ on LHEEvent."""
    event_info = pylhe.LHEEventInfo(
        nparticles=1, pid=0, weight=1.0, scale=91.188, aqed=-1.0, aqcd=-1.0
    )
    particle = pylhe.LHEParticle(
        id=21,
        status=-1,
        mother1=0,
        mother2=0,
        color1=501,
        color2=502,
        px=0.0,
        py=0.0,
        pz=456.3,
        e=456.3,
        m=0.0,
        lifetime=0.0,
        spin=9.0,
    )
    event = pylhe.LHEEvent(eventinfo=event_info, particles=[particle])

    with pytest.warns(
        DeprecationWarning,
        match=r"Dict-like length is deprecated and will be removed in a future version\. Use `asdict\(object\)` instead\.",
    ):
        _ = len(event)


def test_lhe_init_getitem_deprecation_warning():
    """Test that DeprecationWarning is raised when using __getitem__ on LHEInit."""
    init_info = pylhe.LHEInitInfo(
        beamA=2212,
        beamB=2212,
        energyA=6500.0,
        energyB=6500.0,
        PDFgroupA=10800,
        PDFgroupB=10800,
        PDFsetA=0,
        PDFsetB=0,
        weightingStrategy=3,
        numProcesses=1,
    )

    lhe_init = pylhe.LHEInit(initInfo=init_info, procInfo=[], generators=[])

    with pytest.warns(
        DeprecationWarning, match=r"Access by `lheinit\[\"initInfo\"\]` is deprecated"
    ):
        _ = lhe_init["initInfo"]


def test_lhe_init_setitem_deprecation_warning():
    """Test that DeprecationWarning is raised when using __setitem__ on LHEInit."""
    init_info = pylhe.LHEInitInfo(
        beamA=2212,
        beamB=2212,
        energyA=6500.0,
        energyB=6500.0,
        PDFgroupA=10800,
        PDFgroupB=10800,
        PDFsetA=0,
        PDFsetB=0,
        weightingStrategy=3,
        numProcesses=1,
    )

    lhe_init = pylhe.LHEInit(initInfo=init_info, procInfo=[], generators=[])

    with pytest.warns(
        DeprecationWarning, match=r"Access by `lheinit\[\"InitInfo\"\]` is deprecated"
    ):
        lhe_init["InitInfo"] = init_info


def test_lhe_init_setitem_dataclass_field_deprecation_warning():
    """Test that setting a real LHEInit dataclass field goes through the direct field branch."""
    init_info = pylhe.LHEInitInfo(
        beamA=2212,
        beamB=2212,
        energyA=6500.0,
        energyB=6500.0,
        PDFgroupA=10800,
        PDFgroupB=10800,
        PDFsetA=0,
        PDFsetB=0,
        weightingStrategy=3,
        numProcesses=1,
    )

    lhe_init = pylhe.LHEInit(initInfo=init_info, procInfo=[], generators=[])
    proc_info = [pylhe.LHEProcInfo(xSection=1.0, error=0.1, unitWeight=1.0, procId=1)]

    with pytest.warns(
        DeprecationWarning, match=r"Access by `lheinit\[\"procInfo\"\]` is deprecated"
    ):
        lhe_init["procInfo"] = proc_info

    assert lhe_init.procInfo == proc_info
