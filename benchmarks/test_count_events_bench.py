"""
Benchmark tests for pylhe event counting performance.
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


def test_read_num_events_benchmark(benchmark):
    """Benchmark using the existing read_num_events function across all test files."""

    def read_num_events_all_files(filepaths):
        total_events = 0
        for filepath in filepaths:
            # Use the existing read_num_events function
            num_events = pylhe.LHEFile.count_events(filepath)
            total_events += num_events
        return total_events

    result = benchmark(read_num_events_all_files, TEST_FILES_LHE_ALL)
    print(f"Total events across all files: {result}")
