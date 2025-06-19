# pylhe: Python LHE interface

<img src="https://raw.githubusercontent.com/scikit-hep/pylhe/main/docs/_static/img/pylhe-logo.png" alt="pylhe logo" width="250"/>

[![GitHub Project](https://img.shields.io/badge/GitHub--blue?style=social&logo=GitHub)](https://github.com/scikit-hep/pylhe)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1217031.svg)](https://doi.org/10.5281/zenodo.1217031)
[![Scikit-HEP](https://scikit-hep.org/assets/images/Scikit--HEP-Project-blue.svg)](https://scikit-hep.org/)

[![PyPI version](https://img.shields.io/pypi/v/pylhe.svg)](https://pypi.org/project/pylhe/)
[![Conda-forge version](https://img.shields.io/conda/vn/conda-forge/pylhe.svg)](https://github.com/conda-forge/pylhe-feedstock)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/pylhe.svg)](https://pypi.org/project/pylhe/)

[![GitHub Actions Status](https://github.com/scikit-hep/pylhe/actions/workflows/ci.yml/badge.svg)](https://github.com/scikit-hep/pylhe/actions/workflows/ci.yml?query=branch%3Amain)
[![Code Coverage](https://codecov.io/gh/scikit-hep/pylhe/graph/badge.svg?branch=main)](https://codecov.io/gh/scikit-hep/pylhe?branch=main)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/scikit-hep/pylhe/main.svg)](https://results.pre-commit.ci/latest/github/scikit-hep/pylhe/main)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Small and thin Python interface to read [Les Houches Event (LHE)](https://inspirehep.net/record/725284) files

## Install

To install `pylhe` from PyPI you can just do

```
python -m pip install pylhe
```

The visualization capabilities require the external dependency of [Graphviz](https://graphviz.org/).

## Get started

The example below provides a simple overview.
Full functionality can be inspected from the functions provided in the `pylhe` module.

### Reading

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

### Writing

For a full example see [write](examples/write_monte_carlo_example.ipynb) or [filter](examples/filter_events_example.ipynb).
The values in the sketch below are intentionally left empty since they depend on the use-case.
The data structure of `pylhe` is:

```python
import pylhe

file=pylhe.LHEFile(
    init=pylhe.LHEInit(
        initInfo=pylhe.LHEInitInfo(
            beamA=,
            beamB=,
            energyA=,
            energyB=,
            PDFgroupA=,
            PDFgroupB=,
            PDFsetA=,
            PDFsetB=,
            weightinStrategy=,
            numProcesses=,
        ),
        procInfo=pylhe.LHEProcInfo(
            xSection=,
            error=,
            unitWeight=,
            procId=,
        ),
    ),
    events=[
        pylhe.LHEEvent(
            eventinfo=pylhe.LHEEventInfo(
                nparticles=,
                pid=,
                weight=,
                scale=,
                aqed=,
                aqcd=,
            ),
            particles=[
                pylhe.LHEParticle(
                    id=,
                    status=,
                    mother1=,
                    mother2=,
                    color1=,
                    color2=,
                    px=,
                    py=,
                    pz=,
                    e=,
                    m=,
                    lifetime=,
                    spin=,
                ),
                ...
            ],
            weights=None,
            attributes=None,
            optional=None,
        ),
        ...
    ]
)

# write to file, compressed if gz/gzip suffix
write_lhe_file(file.init, file.events, "myevents.lhe.gz", rwgt=True, weights=False)

```


## Citation

The preferred BibTeX entry for citation of `pylhe` is

```
@software{pylhe,
  author = {Lukas Heinrich and Matthew Feickert and Eduardo Rodrigues and Alexander Puck Neuwirth},
  title = "{pylhe: v0.9.1}",
  version = {v0.9.1},
  doi = {10.5281/zenodo.1217031},
  url = {https://github.com/scikit-hep/pylhe},
}
```

## Contributors

We hereby acknowledge the contributors that made this project possible ([emoji key](https://allcontributors.org/docs/en/emoji-key)):
<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tbody>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="http://www.matthewfeickert.com/"><img src="https://avatars.githubusercontent.com/u/5142394?v=4?s=100" width="100px;" alt="Matthew Feickert"/><br /><sub><b>Matthew Feickert</b></sub></a><br /><a href="#maintenance-matthewfeickert" title="Maintenance">🚧</a> <a href="#design-matthewfeickert" title="Design">🎨</a> <a href="https://github.com/scikit-hep/pylhe/commits?author=matthewfeickert" title="Code">💻</a> <a href="https://github.com/scikit-hep/pylhe/commits?author=matthewfeickert" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://www.lukasheinrich.com"><img src="https://avatars.githubusercontent.com/u/2318083?v=4?s=100" width="100px;" alt="Lukas"/><br /><sub><b>Lukas</b></sub></a><br /><a href="#maintenance-lukasheinrich" title="Maintenance">🚧</a> <a href="#design-lukasheinrich" title="Design">🎨</a> <a href="https://github.com/scikit-hep/pylhe/commits?author=lukasheinrich" title="Code">💻</a> <a href="https://github.com/scikit-hep/pylhe/commits?author=lukasheinrich" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://cern.ch/eduardo.rodrigues"><img src="https://avatars.githubusercontent.com/u/5013581?v=4?s=100" width="100px;" alt="Eduardo Rodrigues"/><br /><sub><b>Eduardo Rodrigues</b></sub></a><br /><a href="#maintenance-eduardo-rodrigues" title="Maintenance">🚧</a> <a href="https://github.com/scikit-hep/pylhe/commits?author=eduardo-rodrigues" title="Code">💻</a> <a href="https://github.com/scikit-hep/pylhe/commits?author=eduardo-rodrigues" title="Documentation">📖</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/8me"><img src="https://avatars.githubusercontent.com/u/17862090?v=4?s=100" width="100px;" alt="Johannes Schumann"/><br /><sub><b>Johannes Schumann</b></sub></a><br /><a href="https://github.com/scikit-hep/pylhe/commits?author=8me" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="http://iscinumpy.dev"><img src="https://avatars.githubusercontent.com/u/4616906?v=4?s=100" width="100px;" alt="Henry Schreiner"/><br /><sub><b>Henry Schreiner</b></sub></a><br /><a href="https://github.com/scikit-hep/pylhe/commits?author=henryiii" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/ariaradick"><img src="https://avatars.githubusercontent.com/u/53235605?v=4?s=100" width="100px;" alt="ariaradick"/><br /><sub><b>ariaradick</b></sub></a><br /><a href="https://github.com/scikit-hep/pylhe/commits?author=ariaradick" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/jhgoh"><img src="https://avatars.githubusercontent.com/u/4388926?v=4?s=100" width="100px;" alt="Junghwan John Goh"/><br /><sub><b>Junghwan John Goh</b></sub></a><br /><a href="https://github.com/scikit-hep/pylhe/commits?author=jhgoh" title="Code">💻</a></td>
    </tr>
    <tr>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/fuenfundachtzig"><img src="https://avatars.githubusercontent.com/u/8006302?v=4?s=100" width="100px;" alt="fuenfundachtzig"/><br /><sub><b>fuenfundachtzig</b></sub></a><br /><a href="https://github.com/scikit-hep/pylhe/commits?author=fuenfundachtzig" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://shantanu-gontia.github.io"><img src="https://avatars.githubusercontent.com/u/4872525?v=4?s=100" width="100px;" alt="Shantanu Gontia"/><br /><sub><b>Shantanu Gontia</b></sub></a><br /><a href="https://github.com/scikit-hep/pylhe/commits?author=shantanu-gontia" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/tomeichlersmith"><img src="https://avatars.githubusercontent.com/u/31970302?v=4?s=100" width="100px;" alt="Tom Eichlersmith"/><br /><sub><b>Tom Eichlersmith</b></sub></a><br /><a href="https://github.com/scikit-hep/pylhe/commits?author=tomeichlersmith" title="Code">💻</a></td>
      <td align="center" valign="top" width="14.28%"><a href="https://github.com/APN-Pucky"><img src="https://avatars.githubusercontent.com/u/4533248?v=4?s=100" width="100px;" alt="Alexander Puck Neuwirth"/><br /><sub><b>Alexander Puck Neuwirth</b></sub></a><br /><a href="https://github.com/scikit-hep/pylhe/commits?author=APN-Pucky" title="Code">💻</a></td>
    </tr>
  </tbody>
</table>

<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->

<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification.
