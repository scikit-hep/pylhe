Les Houches Event Format
========================

The Les Houches Event (LHE) format uses an XML-like structure, but the content within the ``<init>` and ``<event>`` blocks consists of whitespace-separated values designed for straightforward parsing in Fortran.
It's first version was defined in :cite:`Alwall:2006yp`.
The ``<header>`` block can contain arbitrary XML content, usually metadata or comments explaining how the events were generated.
The following skeleton example illustrates the overall structure of an LHE file using the ``pylhe`` naming of the attributes

.. code-block:: xml

   <LesHouchesEvents version="1.0">
   <header></header>
   <init>
   beamA beamB energyA energyB PDFgroupA PDFgroupB PDFsetA PDFsetB weightingStrategy numProcesses
   xSection error unitWeight procId
   ...
   # additional hash-commented information can go here
   </init>
   <event>
   nparticles pid weight scale aqed aqcd
   id status mother1 mother2 color1 color2 px py pz e m lifetime spin
   ...
   # additional hash-commented information can go here
   </event>
   ...
   </LesHouchesEvents>

The table below summarizes the main parameters found in LHE files grouped by their ``dataclass`` representation in ``pylhe``.

+-------------------+-------+--------------------------------------+------+
| Parameter         | Type  | Description                          | Unit |
+===================+=======+======================================+======+
| :py:class:`pylhe.LHEInitInfo`                                           |
+-------------------+-------+--------------------------------------+------+
| beamA             | int   | PDG ID of first beam particle        | -    |
+-------------------+-------+--------------------------------------+------+
| beamB             | int   | PDG ID of second beam particle       | -    |
+-------------------+-------+--------------------------------------+------+
| energyA           | float | Energy of first beam particle        | GeV  |
+-------------------+-------+--------------------------------------+------+
| energyB           | float | Energy of second beam particle       | GeV  |
+-------------------+-------+--------------------------------------+------+
| PDFgroupA         | int   | PDF group ID for first beam          | -    |
+-------------------+-------+--------------------------------------+------+
| PDFgroupB         | int   | PDF group ID for second beam         | -    |
+-------------------+-------+--------------------------------------+------+
| PDFsetA           | int   | PDF set ID for first beam            | -    |
+-------------------+-------+--------------------------------------+------+
| PDFsetB           | int   | PDF set ID for second beam           | -    |
+-------------------+-------+--------------------------------------+------+
| weightingStrategy | int   | Weighting strategy                   | -    |
+-------------------+-------+--------------------------------------+------+
| numProcesses      | int   | Number of processes                  | -    |
+-------------------+-------+--------------------------------------+------+
| :py:class:`pylhe.LHEProcInfo`                                           |
+-------------------+-------+--------------------------------------+------+
| xSection          | float | Cross section                        | pb   |
+-------------------+-------+--------------------------------------+------+
| error             | float | Cross section uncertainty            | pb   |
+-------------------+-------+--------------------------------------+------+
| unitWeight        | float | Maximum cross section.               | pb   |
+-------------------+-------+--------------------------------------+------+
| procId            | int   | Process ID                           | -    |
+-------------------+-------+--------------------------------------+------+
| :py:class:`pylhe.LHEEventInfo`                                          |
+-------------------+-------+--------------------------------------+------+
| nparticles        | int   | Number of particles in event         | -    |
+-------------------+-------+--------------------------------------+------+
| pid               | int   | Process ID for this event            | -    |
+-------------------+-------+--------------------------------------+------+
| weight            | float | Event weight                         | -    |
+-------------------+-------+--------------------------------------+------+
| scale             | float | Factorization/renormalization scale  | GeV  |
+-------------------+-------+--------------------------------------+------+
| aqed              | float | QED coupling constant                | -    |
+-------------------+-------+--------------------------------------+------+
| aqcd              | float | QCD coupling constant                | -    |
+-------------------+-------+--------------------------------------+------+
| :py:class:`pylhe.LHEParticle`                                           |
+-------------------+-------+--------------------------------------+------+
| id                | int   | PDG particle ID                      | -    |
+-------------------+-------+--------------------------------------+------+
| status            | int   | Particle status code                 | -    |
+-------------------+-------+--------------------------------------+------+
| mother1           | int   | Index of first mother particle       | -    |
+-------------------+-------+--------------------------------------+------+
| mother2           | int   | Index of second mother particle      | -    |
+-------------------+-------+--------------------------------------+------+
| color1            | int   | First color line index               | -    |
+-------------------+-------+--------------------------------------+------+
| color2            | int   | Second color line index              | -    |
+-------------------+-------+--------------------------------------+------+
| px                | float | x-component of momentum              | GeV  |
+-------------------+-------+--------------------------------------+------+
| py                | float | y-component of momentum              | GeV  |
+-------------------+-------+--------------------------------------+------+
| pz                | float | z-component of momentum              | GeV  |
+-------------------+-------+--------------------------------------+------+
| e                 | float | Energy                               | GeV  |
+-------------------+-------+--------------------------------------+------+
| m                 | float | Mass                                 | GeV  |
+-------------------+-------+--------------------------------------+------+
| lifetime          | float | Proper lifetime                      | mm   |
+-------------------+-------+--------------------------------------+------+
| spin              | float | Spin information. 9.0 for unpolarized| -    |
+-------------------+-------+--------------------------------------+------+

Further details can be found in the original definition of the Les Houches Event file standard.
Besides the original publication there were two extensions to the LHE format, version 2.0 in 2009 :cite:`Butterworth:2010ym` and version 3.0 in 2012 :cite:`Andersen:2014efa`.
However, ``pylhe`` currently only implements the widely adopted extension from version 1.0, that is the addition of multiple weights via ``<initrwgt>``, ``<rwgt>``, ``<weight>``, ``<weights>``, ``<wgt>``, and ``<weightgroup>``.
If in the future there is a demand for ``<scales>``, ``<generator>``, ``<pdfinfo>``, or ``<clustering>`` support these can be added as well.
