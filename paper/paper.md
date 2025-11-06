---
title: "pylhe: A Lightweight Python interface to read Les Houches Event files"
tags:
  - python
  - high energy physics
authors:
  - name: Matthew Feickert
    orcid: 0000-0003-4124-7862
    equal-contrib: true
    affiliation: 1
  - name: Lukas Heinrich
    orcid: 0000-0002-4048-7584
    equal-contrib: true
    affiliation: 2
  - name: Eduardo Rodrigues
    orcid: 0000-0003-2846-7625
    equal-contrib: true
    affiliation: 3
  - name: Alexander Puck Neuwirth
    orcid: 0000-0002-2484-1328
    equal-contrib: true
    affiliation: "4, 5"

affiliations:
  - name: University of Wisconsin-Madison
    index: 1
  - name: Technical University of Munich
    index: 2
  - name: University of Liverpool
    index: 3
  - name: University of Milan Bicocca
    index: 4
  - name: INFN Milan Bicocca
    index: 5
date: 6 November 2025 # APN TODO: update date
bibliography: paper.bib
---

# Summary
<!-- APN TODO: check that all references in paper.bib are cited in the text -->
Some history/introduction history of different formats. HEPEVT -> LHEF -> HepMC -> HDF5? (since its binary maybe in the future? Unlike hepmc/lhe no need to gzip!)

The format is used by major Monte Carlo event generators such as MadGraph, POWHEG, Sherpa, HERWIG, Pythia ... <!-- APN TODO add references here-->
...

Format is XML-like where the free text is designed to be easily parsed in fortran <!-- APN TODO: copy example form jupyter notebook 00_*.ipynb -->

```xml
```

# Statement of need

...

## Impact

...

# Acknowledgements

We would additionally like to thank the contributors of pylhe and the Scikit-HEP community for their support.

# Reference
