---
title: "pylhe: A Lightweight Python interface to Les Houches Event files"
tags:
  - Python
  - physics
  - high energy physics
authors:
  - name: Alexander Puck Neuwirth^[Corresponding author.]
    orcid: 0000-0002-2484-1328
    affiliation: "1, 2"
  - name: Matthew Feickert
    orcid: 0000-0003-4124-7862
    affiliation: 3
  - name: Lukas Heinrich
    orcid: 0000-0002-4048-7584
    affiliation: 4
  - name: Eduardo Rodrigues
    orcid: 0000-0003-2846-7625
    affiliation: 5

affiliations:
  - name: University of Milan Bicocca
    index: 1
  - name: INFN Milan Bicocca
    index: 2
  - name: University of Wisconsin-Madison
    index: 3
  - name: Technical University of Munich
    index: 4
  - name: University of Liverpool
    index: 5

date: 26 November 2025 # APN TODO: update date
bibliography: paper.bib
---

# Summary

The Les Houches Event File is a standard defined in [@Alwall:2006yp].
It allows for a simple exchange of generated events between different generators and analysis programs.
<!-- APN TODO: check that all references in paper.bib are cited in the text -->
Some history/introduction history of different formats. HEPEVT -> LHEF -> HepMC [@Dobbs:2001ck;@Verbytskyi:2020sus] -> HDF5? (since its binary maybe in the future? Unlike hepmc/lhe no need to gzip!)

...

Format is XML-like where the free text is designed to be easily parsed in Fortran <!-- APN TODO: copy example form jupyter notebook 00_*.ipynb -->

```xml
<LesHouchesEvents version="3.0">
<header></header>
<init>
beam1id beam2id beam1energy beam2energy pdfg1 pdfg2 pdfs1 pdfs2 idweight nproc
crosssection crosssectionerror crosssectionmaximum pid
</init>
<event>
nparticles pid weight scale aqed aqcd
id status mother1 mother2 color1 color2 px py pz E m lifetime spin
...
</event>
...
</LesHouchesEvents>
```

Below we give a table summarizing the main parameters found in LHE files.

| Parameter | Type | Description | Unit |
|-----------|------|-------------|------|
| **Init block** | | | |
| beam1id | int | PDG ID of first beam particle | - |
| beam2id | int | PDG ID of second beam particle | - |
| beam1energy | float | Energy of first beam particle | GeV |
| beam2energy | float | Energy of second beam particle | GeV |
| pdfg1 | int | PDF group ID for first beam | - |
| pdfg2 | int | PDF group ID for second beam | - |
| pdfs1 | int | PDF set ID for first beam | - |
| pdfs2 | int | PDF set ID for second beam | - |
| idweight | int | Weight ID | - |
| nproc | int | Number of processes | - |
| crosssection | float | Cross section | pb |
| crosssectionerror | float | Cross section uncertainty | pb |
| crosssectionmaximum | float | Maximum cross section | pb |
| pid | int | Process ID | - |
| **Event block** | | | |
| nparticles | int | Number of particles in event | - |
| pid | int | Process ID for this event | - |
| weight | float | Event weight | - |
| scale | float | Factorization/renormalization scale | GeV |
| aqed | float | QED coupling constant | - |
| aqcd | float | QCD coupling constant | - |
| **Particle entries** | | | |
| id | int | PDG particle ID | - |
| status | int | Particle status code | - |
| mother1 | int | Index of first mother particle | - |
| mother2 | int | Index of second mother particle | - |
| color1 | int | First color line index | - |
| color2 | int | Second color line index | - |
| px | float | x-component of momentum | GeV |
| py | float | y-component of momentum | GeV |
| pz | float | z-component of momentum | GeV |
| E | float | Energy | GeV |
| m | float | Mass | GeV |
| lifetime | float | Proper lifetime | mm/c |
| spin | float | Spin information | - |

Further details can be found in the original definition of the Les Houches Event File standard in [@Alwall:2006yp].

<!-- APN TODO: different version of lhe files 1.0 vs 3.0 -->

# Statement of need


The format is used by all major Monte Carlo event generators such as MadGraph [@Alwall:2014hca], POWHEG-BOX [@Nason:2004rx;@Frixione:2007vw;@Alioli:2010xd], Sherpa [@Gleisberg:2008ta;@Sherpa:2019gpd], HERWIG [@Corcella:2000bw;@Bahr:2008pv;@Bellm:2015jjp;@Bellm:2019zci;@Bewick:2023tfi], Pythia [@Sjostrand:2006za;@Sjostrand:2007gs;@Sjostrand:2014zea;Bierlich:2022pfr], Whizard [Kilian:2007gr,Moretti:2001zz].
They produce hard scattering events in the LHE format which are then passed to parton shower and hadronization programs or directly to analysis frameworks.

`pylhe` allows for easy reading and writing of LHE files in Python, enabling seamless integration into modern pythonic data analysis workflows in high-energy physics.
The library facilitates quick validation of event files through programmatic access to event structure and particle properties, making it straightforward to perform sanity checks on generated events.
Additionally, `pylhe` serves as a crucial interface for uprising machine learning applications in particle physics, allowing researchers to efficiently extract and preprocess event data for training neural networks and other ML models used in event classification, anomaly detection, and physics analysis.

...

## Impact

<!-- APN TODO: reference usages in past, reverse cite ;) -->

`pylhe` has already been used in various research projects and publications within the high-energy physics.
It has been cited in Higgs studies [@Brehmer:2019gmn;@Stylianou:2023tgg;@Feuerstake:2024uxs], SUSY / BSM / dark matter searches [@Beresford:2018pbt;@Kling:2020iar;@Anisha:2023xmh;@Zhou:2022jgj;@Zhou:2024fjf;@Cheung:2024oxh;@Beresford:2024dsc], forward physics [@Kling:2022ykt;@Kelly:2021mcd;@Kling:2020mch], but also in methodological studies involving machine learning techniques for event generation and analysis [@Brehmer:2019xox;@Kofler:2024efb].

...

# Acknowledgements

We would additionally like to thank the contributors of pylhe and the Scikit-HEP community for their support.

# References
