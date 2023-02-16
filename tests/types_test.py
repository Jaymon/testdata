# -*- coding: utf-8 -*-
import re
import string
from collections import Counter
import datetime
import time

from testdata.compat import *

from . import TestCase, testdata


class StringTest(TestCase):
    def test_get_hash(self):
        h = testdata.get_hash()
        self.assertEqual(32, len(h))

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

    def test_get_words_1(self):
        v = testdata.get_words(count=2)
        self.assertEqual(1, len(re.findall(r'\s+', v)))

        v = testdata.get_words(count=2, as_str=False)
        self.assertEqual(2, len(v))

        v = testdata.get_words(as_str=False)
        self.assertGreater(len(v), 0)

        v = testdata.get_words()
        self.assertNotEqual(u"", v)

    def test_get_words_lots(self):
        """
        https://github.com/Jaymon/testdata/issues/78
        """
        words = testdata.get_words(count=1000, as_str=False)
        self.assertEqual(1000, len(words))

    def test_get_words_bounds(self):
        for x in range(10):
            min_size = testdata.randint(0, 20)
            max_size = testdata.randint(20, 40)
            s = testdata.get_words(min_size=min_size, max_size=max_size)
            self.assertTrue(min_size <= len(s) <= max_size)

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

    def test_get_str_1(self):
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

    def test_get_str_bounds(self):
        for x in range(10):
            min_size = testdata.randint(0, 20)
            max_size = testdata.randint(20, 40)
            s = testdata.get_str(min_size=min_size, max_size=max_size)
            self.assertTrue(min_size <= len(s) <= max_size)

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


class NumberTest(TestCase):
    def test_get_range(self):
        for x in range(10):
            for count in testdata.get_range(50):
                pass
            self.assertLessEqual(count, 50)

    def test_get_counter(self):
        c = testdata.get_counter()
        self.assertEqual(1, c())
        self.assertEqual(2, c())
        self.assertEqual(3, c())

        c = testdata.get_counter(0, 2)
        self.assertEqual(0, c())
        self.assertEqual(2, c())
        self.assertEqual(4, c())

    def test_get_coordinate(self):
        v1 = 123.3445435454535
        v2 = 124.23454535
        v = testdata.get_coordinate(v1, v2)
        self.assertGreaterEqual(v, v1)
        self.assertGreaterEqual(v2, v)

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

    def test_get_bool(self):
        results = Counter()
        for x in range(100):
            b = testdata.get_bool()
            results[b] += 1

        self.assertEqual(2, len(results))
        self.assertLess(0, results[True])
        self.assertLess(0, results[False])

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


class SequenceTest(TestCase):
    def test_get_list(self):
        xs = testdata.get_list(testdata.get_int)
        for count, x in enumerate(xs):
            self.assertEqual(int, type(x))
        self.assertLess(0, count)

    def test_choice_1(self):
        xs = [1, 2]
        for x in testdata.get_range():
            r = testdata.choice(xs, exclude=[1])
            self.assertEqual(2, r)

    def test_choice_2(self):
        """dict_values instances in py3 weren't identified as sequences"""
        d = {
            "foo": 1,
            "bar": 2
        }
        r = testdata.choice(d.values())
        self.assertTrue(r in set(d.values()))


class MappingTest(TestCase):
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


class DatetimeTest(TestCase):
    def test_get_birthday(self):
        v = testdata.get_birthday()
        self.assertTrue(isinstance(v, datetime.date))

        v = testdata.get_birthday(as_str=True)
        self.assertTrue(isinstance(v, basestring))

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

