Les Houches Event Format
========================

The Les Houches Event (LHE) format uses an XML-like structure, but the content within the ``<init>` and ``<event>`` blocks consists of whitespace-separated values designed for straightforward parsing in Fortran.
Its first version was defined in :cite:`Alwall:2006yp`.
The ``<header>`` block can contain arbitrary XML content, usually metadata or comments explaining how the events were generated.
The following skeleton example illustrates the overall structure of an LHE file using the ``pylhe`` naming of the attributes for version 1.0:

.. code-block:: xml

   <LesHouchesEvents version="1.0">
   <!-- optional non XML content such as a powheg/madgraph input card go here -->
   <header>
   </header>
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

And for version 3.0 in rwgt mode:

.. code-block:: xml

   <LesHouchesEvents version="3.0">
   <!-- optional non XML content such as a powheg/madgraph input card go here -->
   <header>
   <initrwgt>
   <weight id="weightname"></weight>
   <weightgroup name="groupname" combine="method">
      <weight id="weightname2"></weight>
   </weightgroup>
   </initrwgt>
   </header>
   <init>
   beamA beamB energyA energyB PDFgroupA PDFgroupB PDFsetA PDFsetB weightingStrategy numProcesses
   xSection error unitWeight procId
   ...
   <generator name="GeneratorName" version="X.Y.Z"> Description of the generator </generator>
   # additional hash-commented information can go here
   </init>
   <event>
   nparticles pid weight scale aqed aqcd
   id status mother1 mother2 color1 color2 px py pz e m lifetime spin
   ...
   # additional hash-commented information can go here
   <rwgt>
   <wgt id="weightname"> 1.1 </weight>
   <wgt id="weightname2"> 2.2 </weight>
   </rwgt>
   <scales scalename="1.0" scalename2="2.0"> </scales>
   </event>
   ...
   </LesHouchesEvents>

Or in weights mode:


.. code-block:: xml

   <LesHouchesEvents version="3.0">
   <!-- optional non XML content such as a powheg/madgraph input card go here -->
   <header>
   <initrwgt>
   <weight id="weightname"></weight>
   <weightgroup name="groupname" combine="method">
      <weight id="weightname2"></weight>
   </weightgroup>
   </initrwgt>
   </header>
   <init>
   beamA beamB energyA energyB PDFgroupA PDFgroupB PDFsetA PDFsetB weightingStrategy numProcesses
   xSection error unitWeight procId
   ...
   <generator name="GeneratorName" version="X.Y.Z"> Description of the generator </generator>
   # additional hash-commented information can go here
   </init>
   <event>
   nparticles pid weight scale aqed aqcd
   id status mother1 mother2 color1 color2 px py pz e m lifetime spin
   ...
   # additional hash-commented information can go here
   <weights>
   1.1
   2.2
   </weights>
   <scales scalename="1.0" scalename2="2.0"> </scales>
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
| unitWeight        | float | Maximum cross section                | pb   |
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

Further details can be found in the original definition of the LHE file standard.
Besides the original publication there were two extensions to the LHE format, version 2.0 in 2009 :cite:`Butterworth:2010ym` and version 3.0 in 2013 :cite:`Andersen:2014efa`.
However, ``pylhe`` implements the widely adopted version 3.0 and thus also the subset version 1.0, that is the addition ``<scales>``, ``<generator>``, and of multiple weights via ``<initrwgt>``, ``<rwgt>``, ``<weight>``, ``<weights>``, ``<wgt>``, and ``<weightgroup>``.
