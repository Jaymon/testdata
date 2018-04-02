# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
from unittest import \
    TestCase as BaseTestCase, \
    SkipTest, \
    skip, \
    skipIf, \
    skipUnless, \
    expectedFailure
from contextlib import contextmanager
import time

from .compat import *


# https://docs.python.org/3/library/unittest.html#unittest.skip
skip_if = skipIf # Skip the decorated test if condition is true.
skip_unless = skipUnless # Skip the decorated test unless condition is true.
expected_failure = expectedFailure # Mark the test as an expected failure.
expect_failure = expectedFailure


class TestCase(BaseTestCase):
    @staticmethod
    def skip(reason=""):
        return skip(reason)

    @staticmethod
    def skipIf(condition, reason=""):
        return skipIf(condition, reason)
    skip_if = skipIf

    @staticmethod
    def skipUnless(condition, reason=""):
        return skipUnless(condition, reason)
    skip_unless = skipUnless
    skipUnless = skipUnless

    @staticmethod
    def expectedFailure():
        return expectedFailure
        #return expectedFailure(*args, **kwargs)
    expected_failure = expectedFailure
    expect_failure = expectedFailure

    @classmethod
    def skip_test(cls, *args, **kwargs):
        """just some syntactic sugar to make skipping tests easier
        sadly, there is a self.skipTest but you can't use it from a method like
        setUp(), which is just a shame
        """
        raise SkipTest(*args, **kwargs)

    @contextmanager
    def assertWithin(self, seconds):
        try:
            start = time.time()
            yield self

        finally:
            stop = time.time()
            total = stop - start
            if total > seconds:
                self.fail("Runtime of {:.2f} seconds > {} seconds".format(total, seconds))

    if is_py2:
        def assertRegex(self, s, r):
            """brings py3 assert to py2

            https://docs.python.org/3/library/unittest.html#unittest.TestCase.assertRegex
            """
            self.assertRegexpMatches(s, r)

        def assertNotRegex(self, s, r):
            """brings py3 assert to py2

            https://docs.python.org/3/library/unittest.html#unittest.TestCase.assertNotRegex
            """
            self.assertNotRegexpMatches(s, r)

        def assertRaisesRegex(self, exception, regex, callable, *args, **kwds):
            """brings py3 assert to py2

            https://docs.python.org/3/library/unittest.html#unittest.TestCase.assertRaisesRegex
            """
            self.assertRaisesRegexp(exception, regex, callable, *args, **kwds)

        def assertLogs(logger=None, level=None):
            # TODO -- make this work with testdata.output so we can use this
            # method in py2
            # https://docs.python.org/3/library/unittest.html#unittest.TestCase.assertLogs
            # this is the class py2 uses:
            # https://github.com/python/cpython/blob/d918bbda4bb201c35d1ded3dde686d8b00a91851/Lib/unittest/case.py#L297
            raise NotImplementedError()

