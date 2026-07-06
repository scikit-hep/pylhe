LHEH5 Event Format
==================

LHEH5 is an HDF5-based representation of Les Houches Event data.
It preserves the same core physics information as XML-based LHEF while storing
it in dense datasets that are better suited to high-throughput and parallel I/O.
The format was introduced as an HDF5 analogue of LHEF in
:cite:`Hoche:2019flt` and later consolidated into a compact dataset-oriented
layout in :cite:`Bothmann:2023ozs`.

In practice, most LHEH5 files encountered today use a small set of top-level
datasets for run information, per-process metadata, per-event data, and
per-particle data.
Additional datasets and columns may be present for tool-specific extensions,
but the core layout summarized here is the interoperable part that ``pylhe``
targets.

.. seealso::

   `External LHEH5 format note <https://spice-mc.gitlab.io/pepper/reference/lheh5_format.html>`_
   part of the Pepper parton-level event generator documentation.


Column Labels
-------------

The authoritative mapping between on-disk columns and physical quantities is
stored in HDF5 dataset attributes.
Most files use a ``properties`` attribute.
Some older files instead store the same labels in an attribute named after the
dataset itself, for example ``events`` on the ``/events`` dataset.
Robust readers should consult these attributes instead of assuming a fixed
column order.

The ``events`` dataset contains one row per event, while ``particles``
contains one row per particle across the whole file.
The pair ``(start, nparticles)`` identifies the slice of ``particles`` that
belongs to a given event.
Many producers store nearly all numeric values as double precision numbers,
even when their logical meaning is integer, to keep the layout uniform.


Version Dataset
---------------

The ``/version`` dataset stores a three-integer triplet
``[major, minor, patch]``.
It identifies the on-disk layout written by the producer, but version numbers
should not replace attribute-based column discovery.
Writers may normalize output to the latest version they support, while readers
should continue to interpret columns by name.


Dataset Summary
---------------

A typical consolidated LHEH5 file contains the following datasets:

.. code-block:: text

   /version
   /init
   /procInfo
   /events
   /particles
   /ctevents      # optional, for MC@NLO S-events, not in pylhe
   /ctparticles   # optional, for MC@NLO S-events, not in pylhe

.. list-table::
   :header-rows: 1
   :widths: 18 16 10 56

   * - Dataset
     - Typical shape
     - Type
     - Purpose
   * - ``version``
     - ``(3,)``
     - int
     - Format version triplet ``[major, minor, patch]``
   * - ``init``
     - ``(10,)``
     - usually float64
     - Global run properties, analogous to the LHEF ``<init>`` block
   * - ``procInfo``
     - ``(P, 6+)``
     - usually float64
     - Per-process metadata
   * - ``events``
     - ``(N, 10+)``
     - usually float64
     - Per-event record, including the particle slice locator
   * - ``particles``
     - ``(K, 13)``
     - usually float64
     - Per-particle record across all events
   * - ``ctevents``
     - ``(N_ct, 9)``
     - usually float64
     - Counterterm metadata for MC@NLO ``S``-events
   * - ``ctparticles``
     - ``(K_ct, 4)``
     - usually float64
     - Counterterm four-momenta for MC@NLO ``S``-events

Here ``P`` is the number of subprocess entries, ``N`` is the number of events,
and ``K`` is the total number of particle rows.
The ``+`` sign indicates that additional implementation-defined columns may be
appended beyond the common core columns described below.


``init``
--------

``init`` is a one-dimensional dataset containing global run information.
Its common columns are:

.. list-table::
   :header-rows: 1
   :widths: 18 10 52 8

   * - Column
     - Type
     - Description
     - Unit
   * - ``beamA``
     - int
     - PDG ID of the first beam particle
     - -
   * - ``beamB``
     - int
     - PDG ID of the second beam particle
     - -
   * - ``energyA``
     - float
     - Energy of the first beam particle
     - GeV
   * - ``energyB``
     - float
     - Energy of the second beam particle
     - GeV
   * - ``PDFgroupA``
     - int
     - PDF group ID for the first beam
     - -
   * - ``PDFgroupB``
     - int
     - PDF group ID for the second beam
     - -
   * - ``PDFsetA``
     - int
     - PDF set ID for the first beam
     - -
   * - ``PDFsetB``
     - int
     - PDF set ID for the second beam
     - -
   * - ``weightingStrategy``
     - int
     - Event-weighting strategy
     - -
   * - ``numProcesses``
     - int
     - Number of subprocess rows stored in ``procInfo``
     - -


``procInfo``
------------

``procInfo`` is a two-dimensional dataset with one row per subprocess.
Its common core columns are:

.. list-table::
   :header-rows: 1
   :widths: 18 10 52 8

   * - Column
     - Type
     - Description
     - Unit
   * - ``procId``
     - int
     - Process identifier
     - -
   * - ``npLO``
     - int
     - LO final-state multiplicity tag
     - -
   * - ``npNLO``
     - int
     - NLO or Born-level multiplicity tag
     - -
   * - ``xSection``
     - float
     - Cross section for this process
     - pb
   * - ``error``
     - float
     - Cross section uncertainty
     - pb
   * - ``unitWeight``
     - float
     - Unit weight or maximum weight used for unweighting
     - pb

Some producers append further process-level metadata.
As with all LHEH5 datasets, the attribute labels should be treated as
authoritative for the exact on-disk layout.


``events``
----------

``events`` is a two-dimensional dataset with one row per event.
The most common event-level columns are:

.. list-table::
   :header-rows: 1
   :widths: 18 10 52 8

   * - Column
     - Type
     - Description
     - Unit
   * - ``pid``
     - int
     - Process ID for this event
     - -
   * - ``nparticles``
     - int
     - Number of particles belonging to this event
     - -
   * - ``start``
     - int
     - Offset of the first particle row for this event in ``particles``
     - -
   * - ``trials``
     - float
     - Number of trials used during unweighting
     - -
   * - ``scale``
     - float
     - Nominal hard-process scale
     - GeV
   * - ``fscale``
     - float
     - Factorization scale
     - GeV
   * - ``rscale``
     - float
     - Renormalization scale
     - GeV
   * - ``aqed``
     - float
     - QED coupling constant
     - -
   * - ``aqcd``
     - float
     - QCD coupling constant
     - -
   * - ``weight`` or ``NOMINAL``
     - float
     - Nominal event weight
     - pb

Some files append further event-level columns, for example multiplicity tags or
auxiliary weights.
Readers should discover such columns from the dataset attributes rather than
assuming a fixed width.


``particles``
-------------

``particles`` is a two-dimensional dataset with one row per particle.
Its standard columns mirror the ordinary LHE particle record:

.. list-table::
   :header-rows: 1
   :widths: 18 10 52 8

   * - Column
     - Type
     - Description
     - Unit
   * - ``id``
     - int
     - PDG particle ID
     - -
   * - ``status``
     - int
     - Particle status code
     - -
   * - ``mother1``
     - int
     - Index of the first mother particle
     - -
   * - ``mother2``
     - int
     - Index of the second mother particle
     - -
   * - ``color1``
     - int
     - First color-line index
     - -
   * - ``color2``
     - int
     - Second color-line index
     - -
   * - ``px``
     - float
     - x-component of momentum
     - GeV
   * - ``py``
     - float
     - y-component of momentum
     - GeV
   * - ``pz``
     - float
     - z-component of momentum
     - GeV
   * - ``e``
     - float
     - Energy
     - GeV
   * - ``m``
     - float
     - Mass
     - GeV
   * - ``lifetime``
     - float
     - Proper lifetime
     - mm
   * - ``spin``
     - float
     - Spin information
     - -

.. note::

   ``mother1`` and ``mother2`` use the usual LHE convention: indices are
   1-based within the event, and ``0`` denotes an absent mother.


``ctevents`` and ``ctparticles``
--------------------------------

These optional datasets are used for MC@NLO ``S``-events in the extended
LHEH5 layout described in :cite:`Bothmann:2023ozs`.

``ctevents`` stores one counterterm row per record:

.. list-table::
   :header-rows: 1
   :widths: 18 10 52 8

   * - Column
     - Type
     - Description
     - Unit
   * - ``ijt``
     - int
     - Born-level dipole index used for the counterterm
     - -
   * - ``kt``
     - int
     - Counterterm kinematics or dipole label
     - -
   * - ``i``
     - int
     - Real-emission particle index ``i``
     - -
   * - ``j``
     - int
     - Real-emission particle index ``j``
     - -
   * - ``k``
     - int
     - Spectator particle index ``k``
     - -
   * - ``z1``
     - float
     - First KP integration variable
     - -
   * - ``z2``
     - float
     - Second KP integration variable
     - -
   * - ``bbpsw``
     - float
     - Born-level phase-space weight
     - -
   * - ``tlpsw``
     - float
     - Single-emission phase-space weight
     - -

``ctparticles`` stores the corresponding counterterm four-momenta:

.. list-table::
   :header-rows: 1
   :widths: 18 10 52 8

   * - Column
     - Type
     - Description
     - Unit
   * - ``px``
     - float
     - x-component of counterterm momentum
     - GeV
   * - ``py``
     - float
     - y-component of counterterm momentum
     - GeV
   * - ``pz``
     - float
     - z-component of counterterm momentum
     - GeV
   * - ``e``
     - float
     - Energy of counterterm momentum
     - GeV


Support in ``pylhe``
--------------------

``pylhe`` implements reading and writing of the core consolidated LHEH5 datasets
(``/version``, ``/init``, ``/procInfo``, ``/events``, ``/particles``) via
:py:meth:`pylhe.LesHouchesEvents.fromfile` and :py:meth:`pylhe.LesHouchesEvents.tofile`.
