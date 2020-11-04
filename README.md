# pylhe: Python LHE interface

[![GitHub Project](https://img.shields.io/badge/GitHub--blue?style=social&logo=GitHub)](https://github.com/scikit-hep/pylhe)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1217031.svg)](https://doi.org/10.5281/zenodo.1217031)
[![Scikit-HEP](https://scikit-hep.org/assets/images/Scikit--HEP-Project-blue.svg)](https://scikit-hep.org/)

[![PyPI version](https://badge.fury.io/py/pylhe.svg)](https://badge.fury.io/py/pylhe)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/pylhe.svg)](https://pypi.org/project/pylhe/)

[![GitHub Actions Status](https://github.com/lukasheinrich/pylhe/workflows/CI/CD/badge.svg)](https://github.com/lukasheinrich/pylhe/actions)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Code Coverage](https://codecov.io/gh/scikit-hep/pylhe/graph/badge.svg?branch=master)](https://codecov.io/gh/scikit-hep/pylhe?branch=master)

Small and thin Python interface to read [Les Houches Event (LHE)](https://inspirehep.net/record/725284) files

## Install

To install `pylhe` from PyPI you can just do

```
python -m pip install pylhe
```

and to get the required libraries to be able to visualize events install with the "viz" extra

```
python -m pip install pylhe[viz]
```

The visualization capabilities require external dependencies of [Graphviz](https://graphviz.org/) and LaTeX.

## Citation

The preferred BibTeX entry for citation of `pylhe` is

```
@software{pylhe,
  author = "{Heinrich, Lukas}",
  title = "{pylhe: v0.2.0}",
  version = {v0.2.0},
  doi = {10.5281/zenodo.1217031},
  url = {https://github.com/scikit-hep/pylhe},
}
```
