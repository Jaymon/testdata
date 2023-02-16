# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
from unittest import(
    TestCase as BaseTestCase,
    SkipTest,
    skip,
    skipIf,
    skipUnless,
    expectedFailure,
)
from contextlib import contextmanager
import time
import importlib

from .compat import *
from .config import environ


# https://docs.python.org/3/library/unittest.html#unittest.skip
skip_if = skipIf # Skip the decorated test if condition is true.
skip_unless = skipUnless # Skip the decorated test unless condition is true.
expected_failure = expectedFailure # Mark the test as an expected failure.
expect_failure = expectedFailure


def get_testdata_module():
    """Find and return the testdata module that will be used to proxy testdata
    methods through this class

    :returns: module, the testdata module that should be used
    """
    td = None
    if environ.TESTDATA_MODULEPATH:
        td = importlib.import_module(environ.TESTDATA_MODULEPATH)

    if not td:
        path = __name__.split(".")[0]
        td = sys.modules[path]

    return td


class _TestCaseMixin(object):
    """The mixin for both the TestCase and the TestCase metaclass that provides the
    passthrough to the testdata functions if the called method doesn't exist"""

    def __getattr__(self, k):
        """If the attribute isn't defined on this class try and proxy k to a testdata
        module function, if that fails then an AttributeError is raised like normal

        this allows self.<TESTDATA_FUNCTION_NAME>(*args, **kwargs) to be called from
        any method. If the method is a class method, you'll have to use cls.get_testdata()
        to get the testdata module since this only works with instance methods
        """
        td = self.testdata
        if td:
            return getattr(td, k)

        else:
            raise AttributeError(k)


class _TestCaseMeta(_TestCaseMixin, type):
    """The MetaClass needs a __getattr__ in order for the testdata passthrough to
    work in both class methods and instance methods"""
    pass


class _TestCase(_TestCaseMixin, BaseTestCase):
    testdata = get_testdata_module()
    """Set this to whatever tesdata module you want to proxy"""

    @staticmethod
    def skip(reason=""):
        raise SkipTest(reason)

    @staticmethod
    def skipIf(condition, reason=""):
        if condition:
            raise SkipTest(reason)
    skip_if = skipIf

    @staticmethod
    def skipUnless(condition, reason=""):
        if not condition:
            raise SkipTest(reason)
    skip_unless = skipUnless

    @classmethod
    def skip_test(cls, *args, **kwargs):
        """just some syntactic sugar to make skipping tests easier
        sadly, there is a self.skipTest but you can't use it from a method like
        setUp(), which is just a shame
        """
        raise SkipTest(*args, **kwargs)

    @classmethod
    def skipTest(cls, *args, **kwargs):
        """This overrides the default skipTest method to work in things like setUpClass()"""
        raise SkipTest(*args, **kwargs)

    def assertEventuallyEqual(self, v1, callback, msg="", count=30, wait=0.25):
        """Will run callback up to count times waiting wait seconds between each
        check or until callback's return value equals v1

        Moved here from morp's base test interface class on 2-6-2023

        :param v1: mixed, the value to check against callback
        :param callback: callable, this will be called up to count times or until
            the return value equals v1
        :param msg: str, the message to print on failure
        :param count: int, how many times to run callback
        :param wait: float, how many seconds to wait before attempts
        """
        ret = False
        for x in range(count - 1):
            if callback() == v1:
                ret = True
                break

            else:
                time.sleep(wait)

        if not ret:
            self.assertEqual(v1, callback(), msg)

    def assertUntilTrue(self, callback, cb_args=None, cb_kwargs=None, timeout=30.0, interval=0.1): 
        """will run callback every interval until timeout is exceeded or until callback
        returns True

        see testdata.wait()
        """
        td = self.get_testdata()
        td.wait(callback, cb_args, cb_kwargs, timeout, interval)

    def assertAscii(self, s):
        """checks if the entire string only contains ASCII characters

        https://stackoverflow.com/a/196392/5006
        """
        return self.assertTrue(all(ord(c) < 128 for c in s))
    assertNotUnicode = assertAscii

    def assertUnicode(self, s):
        """Checks if the string has at least one non-ASCII character"""
        return self.assertTrue(any(ord(c) > 128 for c in s))
    assertNotAscii = assertUnicode

    @contextmanager
    def assertWithin(self, *seconds):
        """checks if the code executes within seconds

        :Example:
            with self.assertWithin(1):
                foo() # if returns within 1 second we're good, otherwise AssertError

            with self.assertWithin(.75, 1.25):
                foo() # if returns between .75-1.25 seconds then it's good

        :param *seconds: float(s), how many seconds before considered a failure, if
            only one is passed in then it is max seconds, if two values are passed
            in then it is min, max and the value has to be between them
        """
        try:
            start = time.time()
            yield self

        finally:
            stop = time.time()
            total = stop - start
            if len(seconds) > 1:
                if total <= seconds[0] or total >= seconds[1]:
                    self.fail("Runtime of {:.2f} seconds was not within {} - {} seconds".format(
                        total,
                        seconds[0],
                        seconds[1]
                    ))

            else:
                if total > seconds[0]:
                    self.fail("Runtime of {:.2f} seconds > {} seconds".format(total, seconds[0]))


class TestCase(_TestCase, metaclass=_TestCaseMeta):
    pass

