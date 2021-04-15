# -*- coding: utf-8 -*-
"""
test testdata

link -- http://docs.python.org/library/unittest.html

to run on the command line:
python -m unittest test_testdata[.ClassTest[.test_method]]
"""
from __future__ import unicode_literals, division, print_function, absolute_import
import re
import string
import os
import importlib
import datetime
import types
from collections import OrderedDict, Counter
import time
import sys
import logging

from testdata import environ
from testdata.compat import *
from testdata.output import Capture

from . import TestCase, testdata, SkipTest


class TestdataTest(TestCase):
    def test_get_range(self):
        for x in range(10):
            for count in testdata.get_range(50):
                pass
            self.assertLessEqual(count, 50)

    def test_get_list(self):
        xs = testdata.get_list(testdata.get_int)
        for count, x in enumerate(xs):
            self.assertEqual(int, type(x))
        self.assertLess(0, count)

    def test_get_dict(self):
        d = testdata.get_dict()
        self.assertTrue(isinstance(d, dict))

        d = testdata.get_dict(foo=testdata.get_int)
        self.assertEqual(1, len(d))
        self.assertTrue(isinstance(d["foo"], int))
        self.assertTrue(isinstance(d, dict))

        d = testdata.get_dict("foo", "bar")
        self.assertEqual(2, len(d))
        self.assertTrue(isinstance(d, dict))
        self.assertTrue("foo" in d)
        self.assertTrue("bar" in d)

    def test_choice(self):
        xs = [1, 2]
        for x in testdata.get_range():
            r = testdata.choice(xs, exclude=[1])
            self.assertEqual(2, r)

    def test_get_counter(self):
        c = testdata.get_counter()
        self.assertEqual(1, c())
        self.assertEqual(2, c())
        self.assertEqual(3, c())

        c = testdata.get_counter(0, 2)
        self.assertEqual(0, c())
        self.assertEqual(2, c())
        self.assertEqual(4, c())

    def test_get_phone(self):
        ph = testdata.get_phone()
        self.assertRegex(ph, r"\d{3}-\d{3}-\d{4}")

        ph = testdata.get_phone("+{country_code}-{area_code}-{exchange_code}-{line_number}")
        self.assertRegex(ph, r"\+\d-\d{3}-\d{3}-\d{4}")

        ph = testdata.get_phone(line_number="5555")
        self.assertTrue(ph.endswith("-5555"))

    def test_get_usa_address(self):
        a = testdata.get_usa_address()
        self.assertEqual(a[0], a.street)
        self.assertEqual(a[1], a.section)
        self.assertEqual(a[2], a.city)
        self.assertEqual(a[3], a.state)
        self.assertEqual(a[4], a.zipcode)
        self.assertEqual(a[5], a.line)
        self.assertEqual(a[6], a.lines)

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

    def test_get_hash(self):
        h = testdata.get_hash()
        self.assertEqual(32, len(h))

    def test_get_bool(self):
        results = Counter()
        for x in range(100):
            b = testdata.get_bool()
            results[b] += 1

        self.assertEqual(2, len(results))
        self.assertLess(0, results[True])
        self.assertLess(0, results[False])

    def test_get_md5(self):
        h1 = testdata.get_md5("foo")
        h2 = testdata.get_md5("foo")
        self.assertEqual(h1, h2)

        h3 = testdata.get_md5()
        h4 = testdata.get_md5()
        self.assertTrue(h3 != "")
        self.assertTrue(h4 != "")
        self.assertNotEqual(h3, h4)

        if is_py3:
            h5 = testdata.get_md5(b"bar")
            self.assertTrue(h5 != "")

    def test_get_uuid(self):
        for x in range(10):
            uuid = testdata.get_uuid()
            self.assertEqual(36, len(uuid))

    def test_yes(self):
        for x in range(10):
            self.assertTrue(testdata.yes() in set([0, 1]))

        for x in range(10):
            choice = testdata.yes(5)
            self.assertTrue(choice in set([1, 2, 3, 4, 5]))

        for x in range(10):
            self.assertTrue(testdata.yes(0.75) in set([0, 1]))

        for x in range(10):
            self.assertTrue(testdata.yes(75.0) in set([0, 1]))

    def test_get_names(self):
        fname = testdata.get_first_name()
        fname = testdata.get_first_name("male")
        fname = testdata.get_first_name("m")
        fname = testdata.get_first_name("female")
        fname = testdata.get_first_name("f")
        fname = testdata.get_first_name(True)
        fname = testdata.get_first_name(1)
        fname = testdata.get_first_name(2)
        fname = testdata.get_first_name(False)

        fname = testdata.get_first_name(is_unicode=True)
        self.assertUnicode(fname)
        fname = testdata.get_first_name(is_unicode=False)
        self.assertAscii(fname)

        lname = testdata.get_last_name()
        lname = testdata.get_last_name(is_unicode=True)
        self.assertUnicode(lname)
        lname = testdata.get_last_name(is_unicode=False)
        self.assertAscii(lname)

        name = testdata.get_name(is_unicode=True)
        self.assertUnicode(name)
        name = testdata.get_name(is_unicode=False)
        self.assertAscii(name)

        for x in range(100):
            fname = testdata.get_first_name()
            self.assertFalse(re.search(r"\s+", fname))

            fname = testdata.get_ascii_first_name()
            self.assertFalse(re.search(r"\s+", fname))

    def test_get_ascii_name(self):
        name = testdata.get_ascii_name()
        self.assertGreater(len(name), 0)
        if is_py2:
            name.decode('utf-8') # this should not fail because the string is ascii
        elif is_py3:
            bytes(name, encoding="ascii").decode('utf-8')

    def test_get_unicode_name(self):
        name = testdata.get_unicode_name()
        self.assertGreater(len(name), 0)
        with self.assertRaises(UnicodeEncodeError):
            if is_py2:
                name.decode('utf-8')
            elif is_py3:
                bytes(name, encoding="ascii").decode('utf-8')

    def test_get_name(self):
        name = testdata.get_name()
        self.assertEqual(1, len(re.findall(r'\s+', name)))

        name = testdata.get_name(as_str=False)
        self.assertEqual(2, len(name))

        name = testdata.get_name(name_count=0)
        self.assertNotEqual(u"", name)

        name = testdata.get_name(name_count=1)
        self.assertNotEqual(u"", name)

    def test_get_unique_email(self):
        email = testdata.get_unique_email()
        self.assertFalse(" " in email)

    def test_get_email(self):
        email = testdata.get_email()
        self.assertGreater(len(email), 0)
        self.assertTrue("'" not in email)
        self.assertTrue("-" not in email)

        email = testdata.get_email("foo")
        self.assertTrue(email.startswith("foo"))

        email = testdata.get_email("foo'bar")
        self.assertTrue(email.startswith("foobar"))

    def test_get_words(self):
        v = testdata.get_words(count=2)
        self.assertEqual(1, len(re.findall(r'\s+', v)))

        v = testdata.get_words(count=2, as_str=False)
        self.assertEqual(2, len(v))

        v = testdata.get_words(as_str=False)
        self.assertGreater(len(v), 0)

        v = testdata.get_words()
        self.assertNotEqual(u"", v)

    def test_get_ascii_words(self):
        v = testdata.get_ascii_words()
        self.assertGreater(len(v), 0)
        if is_py2:
            v.decode('utf-8') # this should not fail because the string is ascii
        elif is_py3:
            bytes(v, encoding="ascii").decode('utf-8')

    def test_get_unicode_words(self):
        v = testdata.get_unicode_words()
        self.assertGreater(len(v), 0)
        with self.assertRaises(UnicodeEncodeError):
            if is_py2:
                v.decode('utf-8')
            elif is_py3:
                bytes(v, encoding="ascii").decode('utf-8')

    def test_get_lines(self):
        ls = testdata.get_lines(10)
        self.assertTrue(isinstance(ls, basestring))

        ls = testdata.get_lines(11, as_str=False)
        self.assertTrue(isinstance(ls, list))

    def test_get_birthday(self):
        v = testdata.get_birthday()
        self.assertTrue(isinstance(v, datetime.date))

        v = testdata.get_birthday(as_str=True)
        self.assertTrue(isinstance(v, basestring))

    def test_get_coordinate(self):
        v1 = 123.3445435454535
        v2 = 124.23454535
        v = testdata.get_coordinate(v1, v2)
        self.assertGreaterEqual(v, v1)
        self.assertGreaterEqual(v2, v)

    def test_get_str(self):
        s = testdata.get_str()
        #pout.v(repr(s))

        s_byte = s.encode('utf-8')
        with self.assertRaises(UnicodeError):
            if is_py2:
                s_byte.encode('utf-8')
            elif is_py3:
                str(s_byte).encode('utf-8')

            raise UnicodeError('well what do you know, get_str() returned all ascii')

        s = testdata.get_str(24, chars=string.hexdigits.lower())
        self.assertNotEqual("", s)
        self.assertEqual(24, len(s))

    def test_get_ascii(self):
        s = testdata.get_ascii()
        self.assertNotEqual("", s)

        s = testdata.get_ascii(3)
        self.assertEqual(3, len(s))

    def test_get_url(self):
        s = testdata.get_url()
        self.assertNotEqual("", s)
        if is_py2:
            self.assertRegexpMatches(s, r'https?\://\S*')
        else:
            self.assertRegex(s, r'https?\://\S*')

    def test_get_digits(self):
        for x in range(testdata.get_posint(5)):
            for count in range(1, testdata.get_int(2, 10)):
                d = testdata.get_digits(count)
                self.assertEqual(count, len(d))

        with self.assertRaises(ValueError):
            testdata.get_digits(4, 50000)

        d = testdata.get_digits(5, 4000)
        self.assertEqual(5, len(d))
        self.assertEqual("04000", d)

    def test_get_int(self):
        i = testdata.get_int()
        self.assertGreater(i, 0)

        i = testdata.get_int(1, 5)
        self.assertGreaterEqual(i, 1)
        self.assertGreaterEqual(5, i)

    def test_get_posint(self):
        i = testdata.get_posint()
        self.assertGreater(i, 0)
        self.assertLessEqual(i, 2**31-1)

    def test_get_int32(self):
        i = testdata.get_int32()
        self.assertGreater(i, 0)

    def test_get_float(self):
        f = testdata.get_float()
        self.assertGreater(f, 0.0)

        f = testdata.get_float(1.0, 2.0)
        self.assertGreater(f, 1.0)
        self.assertGreater(2.0, f)

    def test_get_past_datetime(self):
        now = datetime.datetime.utcnow()
        for x in range(5):
            dt = testdata.get_past_datetime()
            self.assertGreater(now, dt)

        for x in range(5):
            dt = testdata.get_past_datetime(now)
            self.assertGreater(now, dt)
            now = dt

    def test_get_past_date(self):
        for x in range(3):
            dt = testdata.get_past_date()
            self.assertTrue(type(dt) is datetime.date)

    def test_get_future_datetime(self):
        now = datetime.datetime.utcnow()
        for x in range(5):
            dt = testdata.get_future_datetime()
            self.assertGreater(dt, now)

        for x in range(5):
            dt = testdata.get_future_datetime(now)
            self.assertGreater(dt, now)
            now = dt

    def test_get_future_date(self):
        for x in range(3):
            dt = testdata.get_future_date()
            self.assertTrue(type(dt) is datetime.date)

    def test_get_datetime(self):
        d = testdata.get_datetime(datetime.datetime.utcnow())
        self.assertGreater(datetime.datetime.utcnow(), d)

        d = testdata.get_datetime(datetime.datetime.utcnow().date())
        self.assertGreater(datetime.datetime.utcnow(), d)

        d = testdata.get_datetime(3600, backward=True)
        self.assertGreater(datetime.datetime.utcnow(), d)

        d = testdata.get_datetime(-3600, backward=True)
        self.assertGreater(datetime.datetime.utcnow(), d)

        d = testdata.get_datetime(-3600)
        self.assertGreater(datetime.datetime.utcnow(), d)

        d = testdata.get_datetime(3600)
        self.assertLess(datetime.datetime.utcnow(), d)

        d = testdata.get_datetime(datetime.timedelta(seconds=-3600), backward=True)
        self.assertGreater(datetime.datetime.utcnow(), d)

        d = testdata.get_datetime(datetime.timedelta(seconds=3600), backward=True)
        self.assertGreater(datetime.datetime.utcnow(), d)

        d = testdata.get_datetime(datetime.timedelta(seconds=-3600))
        self.assertGreater(datetime.datetime.utcnow(), d)

        d = testdata.get_datetime(datetime.timedelta(days=1, seconds=3600, microseconds=1234))
        self.assertLess(datetime.datetime.utcnow(), d)

    def test_get_between_datetime_1(self):
        start = testdata.get_past_datetime()
        for x in range(5):
            dt = testdata.get_between_datetime(start)
            now = datetime.datetime.utcnow()
            self.assertGreater(now, dt)

        time.sleep(0.1)
        stop = datetime.datetime.utcnow()
        for x in range(5):
            dt = testdata.get_between_datetime(start, stop)
            self.assertGreater(dt, start)
            self.assertGreater(stop, dt)
            start = dt

        now = datetime.datetime.utcnow()
        with self.assertRaises(ValueError):
            dt = testdata.get_between_datetime(now, now)

        start = testdata.get_datetime(-60)

        dt = testdata.get_between_datetime(start=datetime.timedelta(days=-60))
        self.assertLess(start, dt)

        dt = testdata.get_between_datetime(start=-60)
        self.assertLess(start, dt)

    def test_get_between_datetime_same_microseconds(self):
        """noticed a problem when using the same now"""
        now = datetime.datetime.utcnow()
        start_dt = testdata.get_past_datetime(now)
        stop_dt = testdata.get_between_datetime(start_dt, now)
        self.assertGreater(stop_dt, start_dt)

    def test_get_between_date(self):
        start = testdata.get_past_datetime()
        for x in range(3):
            dt = testdata.get_between_date(start)
            self.assertTrue(type(dt) is datetime.date)


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
            print('bar stderr', file=sys.stderr)
            print("baz stdout")
            print('che stderr', file=sys.stderr)

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


class TC1Test(testdata.TestCase):
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


class TC2Test(testdata.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skip_test()

    def test_this_test_should_never_run(self):
        raise RuntimeError()


class TC3Test(testdata.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skipTest()

    def test_this_test_should_never_run(self):
        raise RuntimeError()

