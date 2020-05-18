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

import pytest
import pylhe
from os.path import dirname, join

TEST_DATA_DIR = join(dirname(__file__), 'test_data')
TEST_FILE = join(TEST_DATA_DIR, 'EventOutput.Pert.00000001.lhe')


def test_event_count():
    assert pylhe.readNumEvents(TEST_FILE) == 791


def test_lhe_init():
    init_data = pylhe.readLHEInit(TEST_FILE)
    init_info = init_data['initInfo']
    assert init_info['beamA'] == pytest.approx(1.0)
    assert init_info['beamB'] == pytest.approx(2.0)
    assert init_info['energyA'] == pytest.approx(1.234567)
    assert init_info['energyB'] == pytest.approx(2.345678)
    assert init_info['PDFgroupA'] == pytest.approx(3.0)
    assert init_info['PDFgroupB'] == pytest.approx(4.0)
    assert init_info['PDFsetA'] == pytest.approx(5.0)
    assert init_info['PDFsetB'] == pytest.approx(6.0)
    assert init_info['weightingStrategy'] == pytest.approx(7.0)
    assert init_info['numProcesses'] == pytest.approx(8.0)

