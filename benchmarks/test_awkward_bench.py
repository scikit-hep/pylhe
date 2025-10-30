"""
Benchmark tests for pylhe awkward array conversion performance.
"""

import skhep_testdata

import pylhe

# Test data files from skhep_testdata - all LHE and LHE.gz files
TEST_FILES_LHE_ALL = [
    skhep_testdata.data_path("pylhe-testfile-pr29.lhe"),
    skhep_testdata.data_path("pylhe-testlhef3.lhe"),
    *[
        skhep_testdata.data_path(f"pylhe-testfile-powheg-box-v2-{proc}.lhe")
        for proc in ["Z", "W", "Zj", "trijet", "directphoton", "hvq"]
    ],
    skhep_testdata.data_path("pylhe-testfile-madgraph-2.0.0-wbj.lhe"),
    skhep_testdata.data_path("pylhe-testfile-madgraph-2.2.1-Z-ckkwl.lhe.gz"),
    skhep_testdata.data_path("pylhe-testfile-madgraph-2.2.1-Z-fxfx.lhe.gz"),
    skhep_testdata.data_path("pylhe-testfile-madgraph-2.2.1-Z-mlm.lhe.gz"),
    skhep_testdata.data_path("pylhe-testfile-madgraph5-3.5.8-pp_to_jj.lhe.gz"),
    skhep_testdata.data_path("pylhe-testfile-pythia-6.413-ttbar.lhe"),
    skhep_testdata.data_path("pylhe-testfile-pythia-8.3.14-weakbosons.lhe"),
    skhep_testdata.data_path("pylhe-testfile-sherpa-3.0.1-eejjj.lhe"),
    skhep_testdata.data_path("pylhe-testfile-whizard-3.1.4-eeWW.lhe"),
]


def test_fromfile_and_to_awkward_benchmark_collective(benchmark):
    """Benchmark LHEFile.fromfile and to_awkward conversion across all test files."""

    def fromfile_and_to_awkward_all_files(filepaths):
        for filepath in filepaths:
            # Load LHE file using fromfile
            lhe_file = pylhe.LHEFile.fromfile(filepath)

            # Convert events to awkward array
            pylhe.to_awkward(lhe_file.events)

    benchmark(fromfile_and_to_awkward_all_files, TEST_FILES_LHE_ALL)
