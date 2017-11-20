# -*- coding: utf-8 -*-
"""
test testdata

link -- http://docs.python.org/library/unittest.html

to run on the command line:
python -m unittest test_testdata[.ClassTest[.test_method]]
"""
from __future__ import unicode_literals, division, print_function, absolute_import
import unittest
import re
import string
import os
import importlib
import datetime
import types
from collections import OrderedDict, Counter
import time
import logging
import sys

import requests

import testdata
from testdata.path import Filepath, Dirpath
from testdata.compat import *
from testdata.threading import Thread
from testdata import threading
from testdata.output import Capture
from testdata.server import AnyServer, CookieServer, CallbackServer


#logging.basicConfig(format="[%(levelname).1s] %(message)s", level=logging.DEBUG, stream=sys.stdout)
testdata.basic_logging()
logger = logging.getLogger(__name__)


class ServerTest(unittest.TestCase):
    def test_callback(self):
        def do_GET(handler):
            return None

        def do_POST(handler):
            return handler.body

        server = CallbackServer({
            "GET": do_GET,
            "POST": do_POST,
        })
        with server:
            res = requests.get(server.url("/foo/bar/get?foo=1"))
            self.assertEqual(204, res.status_code)

            res = requests.post(server.url("/foo/bar/post"), {"foo": 1})
            self.assertEqual(200, res.status_code)

            res = requests.request("BOGUS", server.url("/foo/bar/bogus"))
            self.assertEqual(501, res.status_code)

    def test_cookies(self):
        cookies = {
            "foo": testdata.get_ascii(),
            "bar": testdata.get_ascii(),
            "che": 1,
        }

        server = testdata.create_cookieserver(cookies.items())

        with server:
            res = requests.get(server)
            self.assertEqual(cookies["foo"], res.cookies["foo"])
            self.assertEqual(cookies["bar"], res.cookies["bar"])
            self.assertEqual(str(cookies["che"]), res.cookies["che"])
            self.assertEqual(len(cookies), res.json()["sent_cookies"])

            cookies = res.cookies
            b = requests.Session()
            b.cookies = cookies
            res = b.get(server)
            self.assertEqual(len(cookies), res.json()["read_cookies"])

    def test_any(self):
        server = AnyServer()
        with server:
            res = requests.get(server.url("/foo/bar/che"))
            self.assertTrue(204, res.status_code)

            res = requests.get(server.url("/foo"))
            self.assertTrue(204, res.status_code)

            res = requests.get(server)
            self.assertTrue(204, res.status_code)

    def test_alternate_args(self):

        server = testdata.create_fileserver("foo")
        with server:
            res = requests.get(server)
            self.assertEqual("foo", res.content.decode())

        server = testdata.create_fileserver(["foo"])
        with server:
            res = requests.get(server)
            self.assertEqual("foo", res.content.decode())

    def test_serve(self):
        server = testdata.create_fileserver({
            "foo.txt": ["foo"],
            "bar.txt": ["bar"],
        })

        server.start()
        res = requests.get(server.url("foo.txt"))
        self.assertEqual("foo", res.content.decode())
        server.stop()

        with server:
            res = requests.get(server.url("bar.txt"))
            self.assertEqual("bar", res.content.decode())

        # !!! For some reason I couldn't create a new instance with the same port
        # and I'm not sure enough I care to fix it and nothing in this worked:
        # https://stackoverflow.com/questions/6380057/python-binding-socket-address-already-in-use
        with testdata.create_fileserver({"che.txt": ["che"]}, port=(server.port + 1)) as s:
        #with testdata.create_fileserver({"che.txt": ["che"]}) as s:
            res = requests.get(s.url("che.txt"))
            self.assertEqual("che", res.content.decode())


class PathTest(unittest.TestCase):
    def test_directory(self):
        d = testdata.create_dir()
        self.assertEqual(d, d.directory)

        f = testdata.create_file("dir.txt", "", d)
        self.assertEqual(d, f.directory)

        p = testdata.create_package("r.e", "", d)
        self.assertEqual(os.path.join(d, "r", "e"), p.directory)

        m = testdata.create_module("d.i", "", d)
        self.assertEqual(os.path.join(d, "d"), m.directory)

    def test_permissions(self):
        f = testdata.create_file("permissions.txt")
        self.assertRegexpMatches(f.permissions, "0[0-7]{3}")

        f.chmod("0755")
        self.assertEqual("0755", f.permissions)

        f.chmod(644)
        self.assertEqual("0644", f.permissions)

        f.chmod("655")
        self.assertEqual("0655", f.permissions)

        f.chmod(655)
        self.assertEqual("0655", f.permissions)

        f.chmod(500)
        self.assertEqual("0500", f.permissions)

    def test_child(self):
        d = testdata.create_dir()
        d2 = d.child("foo", "bar")
        self.assertTrue(isinstance(d2, Dirpath))

        f = d.create_file("foo/bar.txt")
        f2 = d.child("foo/bar.txt")
        self.assertTrue(isinstance(f2, Filepath))

    def test_division(self):
        d = testdata.create_dir()
        d2 = d.child("foo/bar")
        d3 = d / "foo/bar"
        self.assertEqual(d2, d3)

    def test_module(self):
        m = testdata.create_module("bar.foo_test", [
            "from unittest import TestCase",
            "class FooTest(TestCase):",
            "    def test_foo(self):",
            "        pass",
            #"        print 'in foo test'",
            "",
        ])
        self.assertEqual(m.module.__file__, m.path)
        self.assertEqual("bar/foo_test.py", m.relpath)

    def test_modules(self):
        mpath = testdata.create_modules({
            "test_modules.foo": [
                "class Foo(object): pass",
                "class Bar(object): pass",
                "",
            ],
            "test_modules.bar": [
                "class Che(object): pass",
                "class Bar(object): pass",
                "",
            ],
            "test_modules.che": [
                "class Baz(object): pass",
                "",
            ],
        })

        mp = mpath.modpath("test_modules")
        mps = list(mp.modpaths())
        self.assertTrue(3, len(mps))
        for modpath in ["test_modules.foo", "test_modules.bar", "test_modules.che"]:
            self.assertTrue(modpath in mps)

        klasses = list(mp.classes)
        self.assertEqual(5, len(klasses))


class TestdataTest(unittest.TestCase):
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

    def test_create_file_structure(self):
        raise unittest.SkipTest("no longer supported")
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

    def test_get_file(self):
        f = testdata.get_file()
        self.assertFalse(f.exists())

        f.write(testdata.get_words())
        self.assertTrue(f.exists())

        f = testdata.get_file("foobar.txt")
        self.assertTrue(f.endswith("foobar.txt"))

        words = testdata.get_words()
        with f.open("w+") as fp:
            fp.write(words)

        self.assertEqual(words, f.contents())


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
            with open(f) as fr:
                sr = fr.read()
                self.assertEqual(s, sr)

        with self.assertRaises(ValueError):
            testdata.create_dir("./foo/bar/test.txt")

    def test_create_files(self):
        ts = {
            "foo/1.txt": testdata.get_words(),
            "foo/2.txt": testdata.get_words(),
            "/bar/3.txt": testdata.get_words(),
            "/bar/che/4.txt": testdata.get_words(),
        }

        path = testdata.create_files(ts)
        self.assertEqual(list(path.files()), list(path))

        count = 0
        for f in path:
            for rp, v in ts.items():
                if rp in f:
                    count += 1
                    self.assertEqual(v, f.contents())

        self.assertLess(0, count)

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

    def test_create_modules_3(self):
        prefix = "testdata_cm3"
        r = testdata.create_modules({
            "{}.foo.bar".format(prefix): [
                "class Bar(object): pass",
            ],
            "{}.foo.bar.che.baz".format(prefix): [
                "class Baz(object): pass",
                ""
            ],
        })

        self.assertEqual(5, len(list(r.modules())))

        m = r.module("{}.foo.bar.che.baz".format(prefix))
        c = m.Baz() # if this doesn't raise error, it worked

        mp = r.modpath("{}.foo".format(prefix))
        self.assertTrue(mp.is_package())

    def test_create_package(self):
        prefix = "foo"
        contents = os.linesep.join([
            "class Bar(object): pass",
        ])
        mp = testdata.create_package(prefix, contents=contents)
        self.assertTrue(mp.is_package())
        return



        basedir = testdata.create_dir()
        prefix = "foo"
        testdata.create_dir(prefix, tmpdir=basedir)
        contents = os.linesep.join([
            "class Bar(object): pass",
        ])
        mp = testdata.create_module(prefix, contents=contents, tmpdir=basedir)
        self.assertTrue(mp.is_package())

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

    def test_get_email(self):
        email = testdata.get_email()
        self.assertGreater(len(email), 0)
        self.assertTrue("'" not in email)
        self.assertTrue("-" not in email)

        email = testdata.get_email("foo")
        self.assertTrue(email.startswith("foo"))

        email = testdata.get_email("foo'bar")
        self.assertTrue(email.startswith("foobar"))

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

    def test_get_past_datetime(self):
        now = datetime.datetime.utcnow()
        for x in range(5):
            dt = testdata.get_past_datetime()
            self.assertGreater(now, dt)

        for x in range(5):
            dt = testdata.get_past_datetime(now)
            self.assertGreater(now, dt)
            now = dt

    def test_get_future_datetime(self):
        now = datetime.datetime.utcnow()
        for x in range(5):
            dt = testdata.get_future_datetime()
            self.assertGreater(dt, now)

        for x in range(5):
            dt = testdata.get_future_datetime(now)
            self.assertGreater(dt, now)
            now = dt

    def test_get_between_datetime(self):
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

    def test_get_between_datetime_same_microseconds(self):
        """noticed a problem when using the same now"""
        now = datetime.datetime.utcnow()
        start_dt = testdata.get_past_datetime(now)
        stop_dt = testdata.get_between_datetime(start_dt, now)
        self.assertGreater(stop_dt, start_dt)

    def test_patch(self):

        @classmethod
        def mock_bam(*args, **kwargs): return 22

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

        FP = testdata.patch(FooPatch, bam=mock_bam)
        self.assertEqual(22, FP.bam())

        from patch import foo
        self.assertEqual(1, foo.FooPatch.bam())
        foo = testdata.patch(foo, boom=mock_boom)
        self.assertEqual(2, foo.FooPatch.bam())

        foo = testdata.patch('patch.foo', boom=mock_boom)
        self.assertEqual(2, foo.FooPatch.bam())

    def test_patch_instance(self):
        class Foo(object):
            che = 6
            def bar(self):
                return 5

        def mock_bar(self):
            return 2

        f = Foo()
        self.assertEqual(5, f.bar())
        self.assertEqual(6, f.che)

        fm = testdata.patch_instance(
            f,
            bar=mock_bar,
            che=7
        )
        self.assertEqual(2, fm.bar())
        self.assertEqual(7, fm.che)
        self.assertEqual(2, f.bar())
        self.assertEqual(7, f.che)

        f = Foo()
        self.assertEqual(5, f.bar())
        self.assertEqual(6, f.che)
        fm = testdata.patch(f, bar=mock_bar, che=7)
        self.assertEqual(2, fm.bar())
        self.assertEqual(7, fm.che)

    def test_patch_instance_property(self):
        class Foo(object):
            @property
            def bar(self): return 1

        f = Foo()
        fm = testdata.patch_instance(
            f,
            bar=2
        )

        self.assertEqual(2, fm.bar)
        self.assertEqual(2, f.bar)

        f2 = Foo()
        self.assertEqual(1, f2.bar)

    def test_patch_class_self(self):
        """a class that creates itself should create a copy of the patched class"""
        contents = os.linesep.join([
            "class PatchFactory(object):",
            "    def clone(self): return type(self)()",
            "    def bar(self): return 55",
            ""
        ])
        testdata.create_module("pathclassmod", contents=contents)

        from pathclassmod import PatchFactory

        def mock_bar(self):
            return 33

        MonkeyFactory = testdata.patch_class(
            PatchFactory,
            bar=mock_bar
        )

        f = PatchFactory()
        fm = MonkeyFactory()

        self.assertEqual(55, f.bar())
        self.assertEqual(55, f.clone().bar())

        self.assertEqual(33, fm.bar())
        self.assertEqual(33, fm.clone().bar())

    def test_patch_class(self):
        class Foo(object):
            che = []
            def bar(self):
                return 5

        def mock_bar(self):
            return 3

        MonkeyFoo = testdata.patch_class(
            Foo,
            bar=mock_bar
        )

        f = Foo()
        fm = MonkeyFoo()
        self.assertEqual(5, f.bar())
        self.assertEqual(3, fm.bar())

        MonkeyFoo.che.extend([1, 2, 3])
        self.assertEqual(3, len(MonkeyFoo.che))
        self.assertEqual(3, len(fm.che))
        self.assertFalse(Foo.che)
        self.assertFalse(f.che)

    def test_patch_class_property(self):
        class Foo(object):
            @property
            def bar(self):
                return 5
            @property
            def che(self):
                return 55
            def bam(self):
                return id(self)

        MonkeyFoo = testdata.patch_class(
            Foo,
            bar=3
        )

        f = Foo()
        fm = MonkeyFoo()
        self.assertEqual(5, f.bar)
        self.assertEqual(3, fm.bar)
        self.assertEqual(55, fm.che)
        self.assertNotEqual(f.bam(), fm.bam())
        self.assertEqual(id(f), f.bam())
        self.assertEqual(id(fm), fm.bam())


class Thread2Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        def run():
            time.sleep(0.5)
            raise ValueError("setUpClass")
        thread = Thread(target=run)
        thread.daemon = True
        thread.start()

    def test_raise_error_daemon_start(self):
        def run1():
            time.sleep(1)

        with self.assertRaises(ValueError):
            t1 = Thread(target=run1)
            t1.daemon = True
            t1.start()
            t1.join()


class ThreadTest(unittest.TestCase):
    def tearDown(self):
        # clear the queue to make sure one test doesn't inherit the error of another test
        q = threading.exc_queue
        while not q.empty():
            q.get(False)
            q.task_done()

    def test_success(self):
        q = queue.Queue()
        def run():
            q.put(2)

        thread = Thread(target=run)
        thread.start()
        thread.join()
        self.assertEqual(2, q.get(False)) 

    def test_raise_error_daemon_start(self):
        def run():
            raise ValueError("raise_error_daemon_start")

        thread = Thread(target=run)
        thread.daemon = True
        with self.assertRaises(KeyboardInterrupt):
            thread.start()
            while thread.is_alive():
                time.sleep(0.1)

        self.assertIsInstance(thread.exception, ValueError)

    def test_raise_error_start(self):
        def run():
            raise ValueError("raise_error_start")

        thread = Thread(target=run)
        with self.assertRaises(KeyboardInterrupt):
            thread.start()
            while thread.is_alive():
                time.sleep(0.1)

        self.assertIsInstance(thread.exception, ValueError)

    def test_raise_error_join(self):
        def run():
            time.sleep(0.5)
            raise ValueError("raise_error_join")

        thread = Thread(target=run)
        thread.start()
        with self.assertRaises(ValueError):
            thread.join()

    def test_raise_error_daemon_join(self):
        def run():
            time.sleep(0.5)
            raise ValueError("raise_error_daemon_join")

        thread = Thread(target=run)
        thread.daemon = True
        thread.start()
        with self.assertRaises(ValueError):
            thread.join()

    def test_join_2(self):
        def run():
            time.sleep(0.5)
            raise ValueError("join_2")

        thread = Thread(target=run)
        thread.daemon = True
        thread.start()

        try:
            thread.join()

        except ValueError as e:
            self.assertEqual("join_2", str(e))

    def test_no_error_raised(self):
        # https://github.com/Jaymon/testdata/issues/14
        class C2(object):
            def blah(self, *args): pass
        c2 = C2()

        def c2_send():
            c2.blah(foo_bar)

        with self.assertRaises(NameError):
            t2 = testdata.Thread(target=c2_send)
            t2.start()
            t2.join()


class CaptureTest(unittest.TestCase):
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
        capture = Capture()
        with capture():
            print("foo stdout")
            print('bar stderr', file=sys.stderr)
            print("baz stdout")
            print('che stderr', file=sys.stderr)

        self.assertTrue("foo stdout\nbar stderr\nbaz stdout\nche stderr" in capture)

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

