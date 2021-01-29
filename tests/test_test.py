# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from testdata.compat import *
from testdata.utils import ByteString, String
from testdata.path import Modulepath
from testdata import environ

from . import TestCase



import testdata

modpath = testdata.create_module(contents=[
    "def get_foo(*args, **kwargs):",
    "    return (args, kwargs)"
])







class TestCaseTest(TestCase):
    testdata = testdata
    @classmethod
    def setUpClass(cls):
        #cls.get_words()
        pout.v(id(cls.testdata))

    def test_class_set(self):
        pout.v(id(self.testdata))
#         with self.assertRaises(AttributeError):
#             self.get_words()


    def test_self_testdata(self):
        #s = self.get_string()
        #return


        s = type(self).get_string()
        self.assertTrue(s)

        s = self.get_string()
        self.assertTrue(s)

        w = self.get_words(10)
        self.assertEqual(10, len(w.split(" ")))

        modpath = self.create_module(contents=[
            "def get_foo(*args, **kwargs):",
            "    return (args, kwargs)"
        ])

        type(self).testdata = None
        environ.TESTDATA_MODULEPATH = modpath
        with self.assertRaises(AttributeError):
            self.get_words()
        r = self.get_foo(1, 2)
        self.assertEqual((1, 2), r[0])
        self.assertEqual(self.testdata.__name__, modpath)

        type(self).testdata = None
        environ.TESTDATA_MODULEPATH = ""

        w = type(self).get_words()
        self.assertTrue(w)

        type(self).testdata = modpath.module
        with self.assertRaises(AttributeError):
            self.get_words()
        r = self.get_foo(1, 3)
        self.assertEqual((1, 3), r[0])

        type(self).testdata = None



