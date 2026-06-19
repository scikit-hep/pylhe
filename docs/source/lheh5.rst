LHEH5 Event Format
==================

The LHEH5 format is an HDF5-based representation of Les Houches event data
designed for large parallel workflows.
It was introduced as an HDF5 analogue of LHEF in :cite:`Hoche:2019flt` and
refined into a more I/O-efficient layout in :cite:`Bothmann:2023ozs`.
The goal is to preserve the physics content of ordinary LHE files while
replacing XML blocks with dense HDF5 datasets that scale better on HPC systems.

The first proposal in :cite:`Hoche:2019flt` mirrored the familiar LHE structure
with HDF5 groups such as ``init``, ``procInfo``, ``event``, and ``particle``
and one dataset per quantity.
The later format definition in :cite:`Bothmann:2023ozs` keeps the same logical
content but consolidates most quantities into a small number of two-dimensional
datasets to reduce metadata overhead.
The consolidated layout is what is usually meant by ``LHEH5`` today and is
summarized below.

A typical LHEH5 file contains the following datasets:

.. code-block:: text

   /version
   /init
   /procInfo
   /events
   /particles
   /ctevents      # optional, only for MC@NLO S-events
   /ctparticles   # optional, only for MC@NLO S-events

The concrete example file shipped in ``tests/test.hdf5`` is a leading-order
sample and therefore contains only the core datasets:

.. code-block:: text

   /
   /events      Dataset {100, 10}
   /init        Dataset {10}
   /particles   Dataset {400, 13}
   /procInfo    Dataset {1, 6}
   /version     Dataset {3}

The second bundled example, ``tests/j7_1.hdf5``, uses the same logical core
layout but with extensible event and particle datasets:

.. code-block:: text

   /
   /events      Dataset {2420/Inf, 10}
   /init        Dataset {10}
   /particles   Dataset {24200/Inf, 13}
   /procInfo    Dataset {1, 6}
   /version     Dataset {3}

The datasets carry per-column labels as HDF5 attributes.
In the bundled examples this is usually a ``properties`` attribute, with the
notable exception that ``tests/j7_1.hdf5`` stores the ``/events`` labels in an
``events`` attribute.
The ``events`` dataset contains one row per event, while ``particles`` contains
one row per particle across all events.
The pair ``(start, nparticles)`` identifies the slice of ``particles`` that
belongs to a given event.
In the optimized layout nearly all values are stored as double precision
numbers, even when their logical meaning is integer, in order to minimize the
number of HDF5 objects and improve parallel I/O.
For the bundled example files, the ``/events`` columns are
``pid, nparticles, start, trials, scale, fscale, rscale, aqed, aqcd, NOMINAL``;
the last column stores the nominal event weight.
``tests/test.hdf5`` stores these labels in a ``properties`` attribute, while
``tests/j7_1.hdf5`` stores the same labels in an ``events`` attribute.

Below, ``init``, ``procInfo``, ``event(s)``, and ``particle(s)`` refer to the
logical blocks of the format.
In the 2019 proposal these were separate HDF5 groups with one dataset per
quantity, while in the 2024 layout they are packed into consolidated datasets
named ``init``, ``procInfo``, ``events``, and ``particles``.

The table below summarizes the main published LHEH5 parameters.

.. list-table::
   :header-rows: 1
   :widths: 16 16 10 44 6

   * - Dataset
     - Parameter
     - Type
     - Description
     - Unit
   * - ``version``
     - version
     - int[3]
     - Format version triplet
     - -
   * - ``init``
     - beamA
     - int
     - PDG ID of first beam particle
     - -
   * - ``init``
     - beamB
     - int
     - PDG ID of second beam particle
     - -
   * - ``init``
     - energyA
     - float
     - Energy of first beam particle
     - GeV
   * - ``init``
     - energyB
     - float
     - Energy of second beam particle
     - GeV
   * - ``init``
     - PDFgroupA
     - int
     - PDF group ID for first beam
     - -
   * - ``init``
     - PDFgroupB
     - int
     - PDF group ID for second beam
     - -
   * - ``init``
     - PDFsetA
     - int
     - PDF set ID for first beam
     - -
   * - ``init``
     - PDFsetB
     - int
     - PDF set ID for second beam
     - -
   * - ``init``
     - weightingStrategy
     - int
     - Event-weighting strategy
     - -
   * - ``init``
     - numProcesses
     - int
     - Number of subprocesses stored in the file
     - -
   * - ``procInfo``
     - procId
     - int
     - Process ID
     - -
   * - ``procInfo``
     - xSection
     - float
     - Cross section
     - pb
   * - ``procInfo``
     - error
     - float
     - Cross section uncertainty
     - pb
   * - ``procInfo``
     - unitWeight
     - float
     - Unit weight / maximum weight for unweighting
     - pb
   * - ``procInfo``
     - npLO
     - int
     - LO final-state multiplicity tag
     - -
   * - ``procInfo``
     - npNLO
     - int
     - Born-level multiplicity tag for NLO samples
     - -
   * - ``event(s)``
     - nparticles
     - int
     - Number of particles in the event
     - -
   * - ``event(s)``
     - start
     - int
     - Offset of the first particle record
     - -
   * - ``event(s)``
     - pid
     - int
     - Process ID for this event
     - -
   * - ``event(s)``
     - weight / ``NOMINAL``
     - float
     - Nominal event weight; the example file names this column ``NOMINAL``
     - -
   * - ``event(s)``
     - scale
     - float
     - Nominal event scale
     - GeV
   * - ``event(s)``
     - fscale
     - float
     - Factorization scale
     - GeV
   * - ``event(s)``
     - rscale
     - float
     - Renormalization scale
     - GeV
   * - ``event(s)``
     - aqed
     - float
     - QED coupling constant
     - -
   * - ``event(s)``
     - aqcd
     - float
     - QCD coupling constant
     - -
   * - ``event(s)``
     - npLO
     - int
     - LO multiplicity tag for this event
     - -
   * - ``event(s)``
     - npNLO
     - int
     - NLO/Born multiplicity tag for this event
     - -
   * - ``event(s)``
     - trials
     - float
     - Number of trials used during unweighting
     - -
   * - ``particle(s)``
     - id
     - int
     - PDG particle ID
     - -
   * - ``particle(s)``
     - status
     - int
     - Particle status code
     - -
   * - ``particle(s)``
     - mother1
     - int
     - Index of first mother particle
     - -
   * - ``particle(s)``
     - mother2
     - int
     - Index of second mother particle
     - -
   * - ``particle(s)``
     - color1
     - int
     - First color line index
     - -
   * - ``particle(s)``
     - color2
     - int
     - Second color line index
     - -
   * - ``particle(s)``
     - px
     - float
     - x-component of momentum
     - GeV
   * - ``particle(s)``
     - py
     - float
     - y-component of momentum
     - GeV
   * - ``particle(s)``
     - pz
     - float
     - z-component of momentum
     - GeV
   * - ``particle(s)``
     - e
     - float
     - Energy
     - GeV
   * - ``particle(s)``
     - m
     - float
     - Mass
     - GeV
   * - ``particle(s)``
     - lifetime
     - float
     - Proper lifetime
     - mm
   * - ``particle(s)``
     - spin
     - float
     - Spin information
     - -
   * - ``ctevents``
     - ijt
     - int
     - Born-level dipole index for the counterterm
     - -
   * - ``ctevents``
     - kt
     - int
     - Counterterm kinematics or dipole label
     - -
   * - ``ctevents``
     - i
     - int
     - Real-emission particle index ``i``
     - -
   * - ``ctevents``
     - j
     - int
     - Real-emission particle index ``j``
     - -
   * - ``ctevents``
     - k
     - int
     - Spectator particle index ``k``
     - -
   * - ``ctevents``
     - z1
     - float
     - First KP integration variable
     - -
   * - ``ctevents``
     - z2
     - float
     - Second KP integration variable
     - -
   * - ``ctevents``
     - bbpsw
     - float
     - Single-emission phase-space weight
     - -
   * - ``ctevents``
     - tlpsw
     - float
     - Born phase-space weight
     - -
   * - ``ctparticles``
     - px
     - float
     - x-component of counterterm momentum
     - GeV
   * - ``ctparticles``
     - py
     - float
     - y-component of counterterm momentum
     - GeV
   * - ``ctparticles``
     - pz
     - float
     - z-component of counterterm momentum
     - GeV
   * - ``ctparticles``
     - e
     - float
     - Energy of counterterm momentum
     - GeV

For concrete files the column-label attribute should always be treated as
authoritative for the exact on-disk column order and field naming.
In the examples bundled with this repository that means consulting
``properties`` for most datasets, but also allowing for the event-column labels
to appear under ``events`` as in ``tests/j7_1.hdf5``.
This matters because the 2019 and 2024 papers describe the same logical event
content with different levels of packing and optimization, and the bundled
example files store the event weight under the property name ``NOMINAL``.

Compared to XML-based LHE files, LHEH5 is less flexible for arbitrary metadata
but better suited to high-throughput parallel I/O.
The 2024 paper also adds the explicit ``version`` dataset and the optional
``ctevents`` and ``ctparticles`` datasets needed for MC@NLO ``S``-events,
while ordinary leading-order and hard-remainder events can be described by the
core ``init``, ``procInfo``, ``events``, and ``particles`` content alone.

``pylhe`` does not currently implement LHEH5 parsing or writing, but the
summary above documents the published format proposals and their relationship
to the ordinary LHE structure.
