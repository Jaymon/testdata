# -*- coding: utf-8 -*-
"""
test testdata

link -- http://docs.python.org/library/unittest.html

to run on the command line:
python -m unittest test_testdata[.ClassTest[.test_method]]
"""
from __future__ import unicode_literals, division, print_function, absolute_import
import sys
import logging

from testdata.compat import *
from testdata.output import Capture

from . import TestCase, testdata


class CaptureTest(TestCase):
    def test_filter(self):
        capture = Capture(stdout=False, loggers=False)
        with capture():
            print("stdout")
            print('stderr', file=sys.stderr)

        self.assertTrue("stderr\n" == capture)

        capture = Capture(stderr=False, loggers=False)
        with capture():
            print("stdout")
            print('stderr', file=sys.stderr)

        self.assertTrue("stdout\n" == capture)

        capture = Capture(stdout=False, stderr=False, loggers=False)
        with capture():
            print("stdout")
            print('stderr', file=sys.stderr)

        self.assertTrue("" == capture)

    def test_stream_methods(self):
        with testdata.capture() as c:
            print("foo\nbar\nbaz")

        self.assertTrue(c.count("\n") > 0)
        self.assertTrue(len(c.splitlines(False)) > 0)
        self.assertTrue(len(c) > 0)

        self.assertTrue(str(c))
        self.assertTrue(unicode(c))

    def test_capture_stdout(self):
        capture = Capture()
        with capture():
            print("foo")
            print("bar")

        self.assertTrue("foo" in capture)
        self.assertTrue("bar" in capture)
        self.assertTrue("foo\nbar" in capture)

    def test_capture_mixed(self):
        capture = Capture(loggers=False)
        with capture():
            print("foo stdout")
            print("bar stderr", file=sys.stderr)
            print("baz stdout")
            print("che stderr", file=sys.stderr)

        output = "foo stdout\nbar stderr\nbaz stdout\nche stderr\n"
        self.assertTrue(output in capture)
        self.assertTrue(output == capture)
        self.assertFalse(output < capture)
        self.assertFalse(output > capture)
        self.assertFalse(output != capture)
        self.assertTrue(output <= capture)
        self.assertTrue(output >= capture)
        self.assertTrue(capture)

    def test_function(self):
        with testdata.capture() as c:
            print("foo")
        self.assertTrue("foo" in c)

    def test_passthrough(self):
        # no good way to test this one but by spot checking, but make sure the
        # string is still captured even when it is still being printed
        with testdata.capture(True) as c:
            print("foo")
        self.assertTrue("foo" in c)

    def test_imports(self):
        path = testdata.create_modules({
            "one": [
                "from sys import stdout",
                "from sys import stderr",
                "",
                "stdout.write('one:stdout\\n')",
                "stderr.write('one:stderr\\n')",
            ],
            "two": [
                "import sys",
                "from sys import stderr",
                "",
                "so = sys.stdout",
                "se = stderr",
                "so.write('two:stdout set so\\n')",
                "se.write('two:stderr set se\\n')",
            ],
            "three": [
                "from sys import stdout as o",
                "from sys import stderr as e",
                "",
                "o.write('three:stdout as o\\n')",
                "e.write('three:stderr as e\\n')",
            ],
            "four": [
                "import testdata",
                "",
                "captured = None",
                "with testdata.capture(passthrough=False) as c:",
                "    import one",
                "    import two",
                "    import three",
                "    captured = c",
            ]
        })

        m = path.module("four")
        captured = str(m.captured)
        for s in ["one:stdout", "one:stderr", "as o", "as e", "set so", "set se"]:
            self.assertTrue(s in captured)

    def test_logging(self):
        logger = logging.getLogger("output_test_logging")
        logger.setLevel(logging.DEBUG)
        log_handler = logging.StreamHandler(stream=sys.stderr)
        log_formatter = logging.Formatter('%(message)s')
        log_handler.setFormatter(log_formatter)
        logger.addHandler(log_handler)
        logger.propagate = False

        with testdata.capture() as c:
            logger.debug("foo bar che 1")
        self.assertTrue("foo bar che 1" in c)

        with testdata.capture(passthrough=False) as c:
            logger.debug("foo bar che 2")
        self.assertTrue("foo bar che 2" in c)

