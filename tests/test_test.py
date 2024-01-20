# -*- coding: utf-8 -*-
import logging
import time

from testdata.compat import *
from testdata.base import TestData

from . import TestCase, testdata


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


class TCDataAttributeSet(TestCase):
    class DataClass(TestData):
        def get_foobar(self):
            return self.foobar

    @classmethod
    def setUpClass(cls):
        try:
            cls.data.foobar

        except AttributeError:
            pass

        cls.data.foobar = 1

        assert cls.foobar == 1
        assert cls.data.foobar == 1

    @classmethod
    def tearDownClass(cls):
        cls.data.foobar = None

        assert cls.foobar is None
        assert cls.data.foobar is None

    def test_attribute_set(self):
        self.assertEqual(1, self.get_foobar())

