# pylhe: Python LHE interface

[![GitHub Project](https://img.shields.io/badge/GitHub--blue?style=social&logo=GitHub)](https://github.com/scikit-hep/pylhe)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1217031.svg)](https://doi.org/10.5281/zenodo.1217031)
[![Scikit-HEP](https://scikit-hep.org/assets/images/Scikit--HEP-Project-blue.svg)](https://scikit-hep.org/)

[![PyPI version](https://badge.fury.io/py/pylhe.svg)](https://badge.fury.io/py/pylhe)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/pylhe.svg)](https://pypi.org/project/pylhe/)

[![GitHub Actions Status](https://github.com/lukasheinrich/pylhe/workflows/CI/CD/badge.svg)](https://github.com/lukasheinrich/pylhe/actions)
[![Code Coverage](https://codecov.io/gh/scikit-hep/pylhe/graph/badge.svg?branch=master)](https://codecov.io/gh/scikit-hep/pylhe?branch=master)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/scikit-hep/pylhe/master.svg)](https://results.pre-commit.ci/latest/github/scikit-hep/pylhe/master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

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

## Get started

The example below provides a simple overview.
Full functionality can be inspected from the functions provided in the `pylhe` module.

```python
import itertools

# You can use LHE files from scikit-hep-testdata
from skhep_testdata import data_path

import pylhe

lhe_file = data_path("pylhe-testlhef3.lhe")
events = pylhe.read_lhe_with_attributes(lhe_file)
print(f"Number of events: {pylhe.read_num_events(lhe_file)}")

# Get event 1
event = next(itertools.islice(events, 1, 2))

# A DOT language graph of the event can be inspected as follows
print(event.graph.source)

# The graph is nicely displayed as SVG in Jupyter notebooks
event

# To save a DOT graph render the graph to a supported image format
# (refer to the Graphviz documentation for more)
event.graph.render(filename="test", format="png", cleanup=True)
event.graph.render(filename="test", format="pdf", cleanup=True)
```

## Citation

The preferred BibTeX entry for citation of `pylhe` is

```
@software{pylhe,
  author = {Lukas Heinrich and Matthew Feickert and Eduardo Rodrigues},
  title = "{pylhe: v0.3.0}",
  version = {v0.3.0},
  doi = {10.5281/zenodo.1217031},
  url = {https://github.com/scikit-hep/pylhe},
}
```
