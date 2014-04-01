"""
test testdata

link -- http://docs.python.org/library/unittest.html

to run on the command line:
python -m unittest test_testdata[.ClassTest[.test_method]]
"""
import unittest
import re
import string
import os
import importlib
import datetime
import types
from collections import OrderedDict

import testdata

class TestdataTest(unittest.TestCase):

    def test_create_file_structure(self):
        ts = [
            (
                """
                /foo/
                    /bar/
                        /che/baz.py
                    /2
                    /3
                /4/5/6/here.py
                """,
                [
                    "foo",
                    "foo/bar",
                    "foo/bar/che",
                    "4/5/6"
                ],
                [
                    "foo/bar/che/baz.py",
                    "foo/2",
                    "foo/3",
                    "4/5/6/here.py"
                ]
            ),
            (
                os.linesep.join([
                    "foo/",
                    "  __init__.py",
                    "  bar/",
                    "    __init__.py",
                    "    che.py",
                    "  baz/",
                    "    __init__.py",
                    "    boom/",
                    "      __init__.py",
                    "      pez.py",
                ]),
                [
                    "foo",
                    "foo/bar",
                    "foo/baz",
                    "foo/baz/boom",
                ],
                [
                    "foo/__init__.py",
                    "foo/bar/__init__.py",
                    "foo/bar/che.py",
                    "foo/baz/__init__.py",
                    "foo/baz/boom/__init__.py",
                    "foo/baz/boom/pez.py",
                ]
            ),
            (
                """
                /foo/
                    /bar/che.py
                        /baz/
                    /boom/
                """,
                [
                    "foo",
                    "foo/bar",
                    "foo/bar/baz",
                    "foo/boom"
                ],
                [
                    "foo/bar/che.py",
                ]
            ),
        ]

        for structure_str, expected_dirs, expected_files in ts:
            basedir, created_dirs, created_files = testdata.create_file_structure(structure_str)

            for d in expected_dirs:
                fd = os.path.join(basedir, d)
                #pout.v(fd)
                self.assertTrue(os.path.isdir(fd))

            for d in expected_files:
                fd = os.path.join(basedir, d)
                #pout.v(fd)
                self.assertTrue(os.path.isfile(fd))

    def test_create_dir(self):
        ts = [
            "\\foo\\bar",
            "/foo1/bar1",
            "/foo2/bar2/",
            "foo3/bar3",
            "foo4/bar4/",
            "",
            None
        ]

        for t in ts:
            d = testdata.create_dir(t)
            self.assertTrue(os.path.isdir(d))

        with self.assertRaises(ValueError):
            testdata.create_dir("./foo/bar")

    def test_create_file(self):
        ts = [
            "\\foo\\bar\\test.txt",
            "/foo1/bar1/test.txt",
            "/test.txt",
            "foo3/test.txt",
            "foo4/bar4/che4/test.txt",
        ]
        s = u"happy"

        for t in ts:
            f = testdata.create_file(t, s)
            self.assertTrue(os.path.isfile(f))
            with file(f) as fr:
                sr = fr.read()
                self.assertEqual(s, sr)

        with self.assertRaises(ValueError):
            testdata.create_dir("./foo/bar/test.txt")

    def test_create_module(self):
        ts = [
            (
                "foo.bar",
                "Che",
                u"class Che(object): pass"
            )
        ]

        for t in ts:
            testdata.create_module(t[0], contents=t[2])
            module = importlib.import_module(t[0])
            class_name = getattr(module, t[1])
            instance = class_name()
            # if all these worked, then the test passed :)

    def test_create_modules(self):
        ts = [
            OrderedDict([
                ("foo2.bar", u"class Che(object): pass"),
                ("foo2.bar.baz", u"class Che(object): pass"),
            ])
        ]

        tmpdir = testdata.create_dir(u"")
        for t in ts:
            testdata.create_modules(t, tmpdir=tmpdir)
            for k in t.keys():
                module = importlib.import_module(k)
                class_name = getattr(module, "Che")
                instance = class_name()
                self.assertEqual(k, instance.__module__)

        for v in ['foo2/bar']:
            v = os.path.join(tmpdir, v)
            self.assertTrue(os.path.isdir(v))

        for v in ['foo2/__init__.py', 'foo2/bar/__init__.py', 'foo2/bar/baz.py']:
            v = os.path.join(tmpdir, v)
            self.assertTrue(os.path.isfile(v))

    def test_create_modules_2(self):
        prefix = "testdata_cm2"
        r = testdata.create_modules({
            prefix: os.linesep.join([
                "class Default(object):",
                "    def GET(*args, **kwargs): pass",
                ""
            ]),
            "{}.default".format(prefix): os.linesep.join([
                "class Default(object):",
                "    def GET(*args, **kwargs): pass",
                ""
            ]),
            "{}.foo".format(prefix): os.linesep.join([
                "class Default(object):",
                "    def GET(*args, **kwargs): pass",
                "",
                "class Bar(object):",
                "    def GET(*args, **kwargs): pass",
                "    def POST(*args, **kwargs): pass",
                ""
            ]),
            "{}.foo.baz".format(prefix): os.linesep.join([
                "class Default(object):",
                "    def GET(*args, **kwargs): pass",
                "",
                "class Che(object):",
                "    def GET(*args, **kwargs): pass",
                ""
            ]),
        })

        module = importlib.import_module(prefix)
        class_name = getattr(module, "Default")
        instance = class_name()


    def test_get_ascii_name(self):
        name = testdata.get_ascii_name()
        self.assertGreater(len(name), 0)
        name.decode('utf-8') # this should not fail because the string is ascii

    def test_get_unicode_name(self):
        name = testdata.get_unicode_name()
        self.assertGreater(len(name), 0)
        with self.assertRaises(UnicodeEncodeError):
            name.decode('utf-8')

    def test_get_email(self):
        email = testdata.get_email()
        self.assertGreater(len(email), 0)

        name = testdata.get_ascii_name()
        email = testdata.get_email(name)
        self.assertTrue(email.startswith(name.lower()))

    def test_get_name(self):
        name = testdata.get_name()
        self.assertEqual(1, len(re.findall(r'\s+', name)))

        name = testdata.get_name(as_str=False)
        self.assertEqual(2, len(name))

        name = testdata.get_name(name_count=0)
        self.assertNotEqual(u"", name)

    def test_get_words(self):
        v = testdata.get_words(word_count=2)
        self.assertEqual(1, len(re.findall(r'\s+', v)))

        v = testdata.get_words(word_count=2, as_str=False)
        self.assertEqual(2, len(v))

        v = testdata.get_words(as_str=False)
        self.assertGreater(len(v), 0)

        v = testdata.get_words()
        self.assertNotEqual(u"", v)
    
    def test_get_ascii_words(self):
        v = testdata.get_ascii_words()
        self.assertGreater(len(v), 0)
        v.decode('utf-8') # this should not fail because the string is ascii

    def test_get_unicode_words(self):
        v = testdata.get_unicode_words()
        self.assertGreater(len(v), 0)
        with self.assertRaises(UnicodeEncodeError):
            v.decode('utf-8')

    def test_get_birthday(self):
        v = testdata.get_birthday()
        self.assertTrue(isinstance(v, datetime.date))

        v = testdata.get_birthday(as_str=True)
        self.assertTrue(isinstance(v, types.StringType))

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
            s_byte.encode('utf-8')
            raise UnicodeError('well what do you know, get_str() returned all ascii')

        s = testdata.get_str(24, chars=string.hexdigits.lower())
        self.assertNotEqual(u"", s)
        self.assertEqual(24, len(s))

    def test_get_ascii(self):
        s = testdata.get_ascii()
        self.assertNotEqual(u"", s)

        s = testdata.get_ascii(3)
        self.assertEqual(3, len(s))

    def test_get_url(self):
        s = testdata.get_url()
        self.assertNotEqual(u"", s)
        self.assertRegexpMatches(s, 'https?\://\S*')

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

    def test_patch(self):
        def mock_boom(): return 2
        contents = os.linesep.join([
            "def boom():",
            "    return 1",
            "",
            "class FooPatch(object):",
            "    @classmethod",
            "    def bam(cls): return boom()",
            ""
        ])
        testdata.create_module("patch.foo", contents=contents)

        from patch.foo import FooPatch

        self.assertEqual(1, FooPatch.bam())

        FooPatch = testdata.patch(FooPatch, boom=mock_boom)
        self.assertEqual(2, FooPatch.bam())


        from patch import foo
        self.assertEqual(1, foo.FooPatch.bam())
        foo = testdata.patch(foo, boom=mock_boom)
        self.assertEqual(2, foo.FooPatch.bam())

        foo = testdata.patch('patch.foo', boom=mock_boom)
        self.assertEqual(2, foo.FooPatch.bam())

    def test_get_past_datetime(self):
        now = datetime.datetime.utcnow()
        for x in xrange(5):
            dt = testdata.get_past_datetime()
            self.assertGreater(now, dt)

        for x in xrange(5):
            dt = testdata.get_past_datetime(now)
            self.assertGreater(now, dt)
            now = dt

    def test_get_future_datetime(self):
        now = datetime.datetime.utcnow()
        for x in xrange(5):
            dt = testdata.get_future_datetime()
            self.assertGreater(dt, now)

        for x in xrange(5):
            dt = testdata.get_future_datetime(now)
            self.assertGreater(dt, now)
            now = dt

    def test_get_between_datetime(self):
        start = testdata.get_past_datetime()
        for x in xrange(5):
            dt = testdata.get_between_datetime(start)
            now = datetime.datetime.utcnow()
            self.assertGreater(now, dt)

        stop = datetime.datetime.utcnow()
        for x in xrange(5):
            dt = testdata.get_between_datetime(start, stop)
            self.assertGreater(dt, start)
            self.assertGreater(stop, dt)
            start = dt

        now = datetime.datetime.utcnow()
        with self.assertRaises(ValueError):
            dt = testdata.get_between_datetime(now, now)


