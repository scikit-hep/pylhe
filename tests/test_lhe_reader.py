#!/usr/bin/env python
# coding=utf-8
# Filename: test_lhe_reader.py

__author__ = "Johannes Schumann"
__copyright__ = "Copyright 2020, Johannes Schumann"
__credits__ = []
__license__ = "MIT"
__maintainer__ = "Johannes Schumann"
__email__ = "jschumann@km3net.de"
__status__ = "Development"

import unittest
import pylhe
from os.path import dirname, join

TEST_DATA_DIR = join(dirname(__file__), 'test_data')

class TestLHEFile(unittest.TestCase):
    def setUp(self):
        self.test_file = join(TEST_DATA_DIR, 'EventOutput.Pert.00000001.lhe')

    def test_event_count(self):
        assert pylhe.readNumEvents(self.test_file) == 791

    def test_lhe_init(self):
        init_data = pylhe.readLHEInit(self.test_file)
        init_info = init_data['initInfo']
        self.assertAlmostEqual(init_info['beamA'], 1.0)
        self.assertAlmostEqual(init_info['beamB'], 2.0)
        self.assertAlmostEqual(init_info['energyA'], 1.234567)
        self.assertAlmostEqual(init_info['energyB'], 2.345678)
        self.assertAlmostEqual(init_info['PDFgroupA'], 3.0)
        self.assertAlmostEqual(init_info['PDFgroupB'], 4.0)
        self.assertAlmostEqual(init_info['PDFsetA'], 5.0)
        self.assertAlmostEqual(init_info['PDFsetB'], 6.0)
        self.assertAlmostEqual(init_info['weightingStrategy'], 7.0)
        self.assertAlmostEqual(init_info['numProcesses'], 8.0)
