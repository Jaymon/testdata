# -*- coding: utf-8 -*-
import logging
import time

from testdata.compat import *

from . import TestCase, testdata


class TestCaseTest(TestCase):
    def test_self_testdata(self):
        td = type(self).td

        s = type(self).get_string()
        self.assertTrue(s)

        s = self.get_string()
        self.assertTrue(s)

        w = self.get_words(10)
        self.assertEqual(10, len(w.split(" ")))

        modpath = self.create_module([
            "def get_foo(*args, **kwargs):",
            "    return (args, kwargs)"
        ])

        type(self).td = modpath.module()
        with self.assertRaises(AttributeError):
            self.get_words()
        r = self.get_foo(1, 2)
        self.assertEqual((1, 2), r[0])
        self.assertEqual(self.td.__name__, modpath)

        type(self).td = td

        w = type(self).get_words()
        self.assertTrue(w)

        type(self).td = modpath.module()
        with self.assertRaises(AttributeError):
            self.get_words()
        r = self.get_foo(1, 3)
        self.assertEqual((1, 3), r[0])

        type(self).td = None


class TC1Test(TestCase):
    def test_assert_logs(self):

        name = "test_assert_logs"
        logger = logging.getLogger(name)

        with self.assertLogs(name):
            logger.info("boom1")

        with self.assertRaises(AssertionError):
            with self.assertLogs(name, logging.INFO):
                logger.debug("boom2")

        with self.assertLogs(name, logging.INFO) as cm:
            logger.error("boom3")

        with self.assertRaises(AssertionError):
            with self.assertLogs(name, logging.INFO):
                pass

    def test_assert_within(self):
        with self.assertRaises(AssertionError):
            with self.assertWithin(0.25):
                time.sleep(0.3)

    def test_assert_regex(self):
        self.assertRegex("foo", r"^foo$")
        self.assertNotRegex("bar", r"^foo$")

    @testdata.expectedFailure
    def test_failure_1(self):
        raise RuntimeError()

    @testdata.expected_failure
    def test_failure_2(self):
        raise RuntimeError()

    @testdata.expect_failure
    def test_failure_3(self):
        raise RuntimeError()

    @testdata.skipUnless(False, "this is the required reason")
    def test_skip_1(self):
        self.assertTrue(True)

    def test_skip_2(self):
        self.skip()

    def test_skip_3(self):
        self.skipTest()

    def test_skip_unless(self):
        self.skipUnless(False)

    def test_skip_if(self):
        self.skipIf(False)


class TC2Test(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skip_test()

    def test_this_test_should_never_run(self):
        raise RuntimeError()


class TC3Test(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skipTest()

    def test_this_test_should_never_run(self):
        raise RuntimeError()


