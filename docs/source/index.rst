.. pylhe documentation master file, created by
   sphinx-quickstart on Thu Jul 31 09:01:00 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

|project| |version| documentation
=================================

.. include:: ../../README.md
   :parser: myst_parser.sphinx_


.. autosummary::
   :toctree: _autosummary
   :template: custom-module-template.rst
   :recursive:
   :caption: Modules:

   pylhe
   pylhe.lhe
   pylhe.io
   pylhe.awkward


.. toctree::
   :glob:
   :maxdepth: 3
   :caption: Examples:

   examples/*

.. toctree::
   :glob:
   :hidden:
   :caption: Links:
   :maxdepth: 3

   GitHub <https://github.com/scikit-hep/pylhe>



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
