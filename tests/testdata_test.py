# -*- coding: utf-8 -*-
"""
test testdata

link -- http://docs.python.org/library/unittest.html

to run on the command line:
python -m unittest test_testdata[.ClassTest[.test_method]]
"""
from __future__ import unicode_literals, division, print_function, absolute_import
import time

from testdata.compat import *

from . import TestCase, testdata


class TestdataTest(TestCase):
    def test_wait(self):
        start = time.time()
        def callback():
            stop = time.time()
            return (stop - start) > 0.5
        testdata.wait(callback)
        stop = time.time()
        self.assertTrue(stop - start > 0.5)

        start = time.time()
        def callback(): return False
        with self.assertRaises(RuntimeError):
            testdata.wait(callback, timeout=0.5)

