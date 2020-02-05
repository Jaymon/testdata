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
import collections
import logging

from .compat import *
from .utils import String


# https://docs.python.org/3/library/unittest.html#unittest.skip
skip_if = skipIf # Skip the decorated test if condition is true.
skip_unless = skipUnless # Skip the decorated test unless condition is true.
expected_failure = expectedFailure # Mark the test as an expected failure.
expect_failure = expectedFailure


if is_py2:
    # this is largely a copy/paste job of the 3.7 code:
    # https://github.com/python/cpython/blob/3.7/Lib/unittest/case.py
    # I wouldn't have divided this up into all these classes but I wanted to
    # keep complete api compatibility between py2 and 3

    class _BaseTestCaseContext(object):
        def __init__(self, test_case):
            self.test_case = test_case

        def _raiseFailure(self, standardMsg):
            msg = self.test_case._formatMessage(self.msg, standardMsg)
            raise self.test_case.failureException(msg)


    _LoggingWatcher = collections.namedtuple("_LoggingWatcher", ["records", "output"])


    class _CapturingHandler(logging.Handler):
        def __init__(self):
            super(_CapturingHandler, self).__init__()
            self.watcher = _LoggingWatcher([], [])

        def flush(self):
            pass

        def emit(self, record):
            self.watcher.records.append(record)
            msg = self.format(record)
            self.watcher.output.append(msg)


    class _AssertLogsContext(_BaseTestCaseContext):
        LOGGING_FORMAT = "%(levelname)s:%(name)s:%(message)s"

        def __init__(self, test_case, logger_name, level):
            super(_AssertLogsContext, self).__init__(test_case)


            self.logger_name = logger_name
            if level:
                if isinstance(level, basestring):
                    if is_py2:
                        self.level = logging._checkLevel(String(level).upper())
                    else:
                        self.level = logging._nameToLevel[String(level).upper()]

                else:
                    self.level = level
            else:
                self.level = logging.INFO

            self.msg = None

        def __enter__(self):
            if isinstance(self.logger_name, logging.Logger):
                logger = self.logger = self.logger_name
            else:
                logger = self.logger = logging.getLogger(self.logger_name)

            formatter = logging.Formatter(self.LOGGING_FORMAT)
            handler = _CapturingHandler()
            handler.setFormatter(formatter)
            self.watcher = handler.watcher
            self.old_handlers = logger.handlers[:]
            self.old_level = logger.level
            self.old_propagate = logger.propagate
            logger.handlers = [handler]
            logger.setLevel(self.level)
            logger.propagate = False
            return handler.watcher

        def __exit__(self, exc_type, exc_value, tb):
            self.logger.handlers = self.old_handlers
            self.logger.propagate = self.old_propagate
            self.logger.setLevel(self.old_level)
            if exc_type is not None:
                # let unexpected exceptions pass through
                return False

            if len(self.watcher.records) == 0:
                self._raiseFailure(
                    "no logs of level {} or higher triggered on {}"
                    .format(logging.getLevelName(self.level), self.logger.name))

else:
    # just to keep api cross version (p2 and 3) compatibility if you did need to
    # type check
    from unittest.case import (
        _BaseTestCaseContext,
        _LoggingWatcher,
        _CapturingHandler,
        _AssertLogsContext,
    )


class TestCase(BaseTestCase):
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
    skipUnless = skipUnless

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

    def assertUntilTrue(callback, cb_args=None, cb_kwargs=None, timeout=30.0, interval=0.1): 
        # TODO -- move all the __init__.py functions into a func package, so they
        # can be imported into this and this can just call wait
        pass

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
    def assertWithin(self, seconds):
        """checks if the code executes within seconds

        :Example:
            with self.assertWithin(1):
                foo() # if returns within 1 second we're good, otherwise AssertError
        :param seconds: float, how many seconds before considered a failure
        """
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
            return self.assertRegexpMatches(s, r)

        def assertNotRegex(self, s, r):
            """brings py3 assert to py2

            https://docs.python.org/3/library/unittest.html#unittest.TestCase.assertNotRegex
            """
            return self.assertNotRegexpMatches(s, r)

        def assertRaisesRegex(self, exception, regex, *args, **kwds):
            """brings py3 assert to py2

            https://docs.python.org/3/library/unittest.html#unittest.TestCase.assertRaisesRegex
            """
            return self.assertRaisesRegexp(exception, regex, *args, **kwds)

        def assertLogs(self, logger=None, level=None):
            """This just makes sure something gets logged, and raises an exception
            if it doesn't, I thought about making this work with output.Capture but
            this uses a strange log formatter and stuff and is really just designed
            to test that a log at a minimum level was raised so I opted to move the
            3.7 code (with some changes) into here so the api will be completely identical"""
            return _AssertLogsContext(self, logger, level)

        def assertWarns(self, warning, cb, *args, **kwargs):
            # https://github.com/python/cpython/blob/3.7/Lib/unittest/case.py#L221
            raise NotImplementedError()

        def assertWarnsRegex(self, warning, regex, cb, *args, **kwargs):
            # https://github.com/python/cpython/blob/3.7/Lib/unittest/case.py#L221
            raise NotImplementedError()
