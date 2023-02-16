# -*- coding: utf-8 -*-
"""
test testdata

link -- http://docs.python.org/library/unittest.html

to run on the command line:
python -m unittest test_testdata[.ClassTest[.test_method]]
"""
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import time

from testdata.compat import *

from . import TestCase, testdata


class TestdataTest(TestCase):
    def test_environment(self):
        self.assertFalse("TDT_ENVIRON_VAL" in os.environ)
        with testdata.environment(TDT_ENVIRON_VAL="foobar"):
            self.assertEqual("foobar", os.environ["TDT_ENVIRON_VAL"])
        self.assertFalse("TDT_ENVIRON_VAL" in os.environ)

        self.assertFalse(hasattr(testdata, "TDT_ENVIRON_VAL"))
        with testdata.environment(testdata, TDT_ENVIRON_VAL="foobar"):
            self.assertEqual("foobar", testdata.TDT_ENVIRON_VAL)
        self.assertFalse(hasattr(testdata, "TDT_ENVIRON_VAL"))

        class Foo(object):
            bar = 1
            che = 2

        f = Foo()
        with testdata.environment(f, bar=3):
            self.assertEqual(3, f.bar)
        self.assertEqual(1, f.bar)
        self.assertEqual(2, f.che)

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

