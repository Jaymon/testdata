# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import time

from testdata.compat import *
from testdata.client import HTTP, Command

from . import TestCase, testdata



class ClientTest(TestCase):
    """These are a bit different than similar tests in datatypes's tests.command
    module because they make sure testdata.run_command and testdata's Path.run
    work as expected"""
    def test_unicode_output(self):
        mod1 = testdata.create_module(modpath="foo.bar.__main__", data=[
            "import testdata",
            "print(testdata.get_unicode_words().encode('utf8'))",
        ])

        r = testdata.run_command(mod1)

    def test_return_code(self):
        path1 = testdata.create_file(data=["print('foo')", "exit(1)"])
        r = testdata.run_command(path1, code=1)
        self.assertTrue("foo" in r)

        with self.assertRaises(Exception):
            r = testdata.run_command(path1)

    def test_run_file(self):
        path1 = testdata.create_file(data="print(1)")
        path2 = testdata.get_file(path1.fileroot, tmpdir=path1.basedir)

        r1 = testdata.run_command(path1)
        r2 = testdata.run_command(path2)
        r3 = path1.run()
        r4 = path2.run()
        self.assertTrue(r1 == r2 == r3 == r4)

    def test_run_module(self):
        mod1 = testdata.create_module(modpath="foo.bar.__main__", data="print(1)")
        #pout.v(mod1.parent, mod1.relpath, mod1)
        r1 = testdata.run_command(mod1)
        r2 = mod1.run()
        self.assertEqual(r1, r2)

