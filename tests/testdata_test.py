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
from testdata.path import (
    Dirpath,
    Filepath,
    Modulepath,
    ContentBytes,
    ContentString,
    ContentFilepath
)
from testdata.compat import *
from testdata.output import Capture
from testdata.server import AnyServer, CookieServer, CallbackServer
from testdata.client import HTTP, Command
from testdata.utils import ByteString, String

from . import TestCase, testdata, SkipTest


testdata.basic_logging()


class ServerTest(TestCase):
    def test_close(self):
        content = testdata.get_unicode_words()
        server = testdata.create_fileserver({
            "foo.txt": content
        })

        with server:
            pass

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
            res = testdata.fetch(server.url("/foo/bar/get?foo=1"))
            self.assertEqual(204, res.status_code)

            res = testdata.fetch(server.url("/foo/bar/post"), {"foo": 1})
            self.assertEqual(200, res.status_code)

            res = testdata.fetch(server.url("/foo/bar/bogus"), method="BOGUS")
            self.assertEqual(501, res.status_code)

    def test_cookies(self):
        cookies = {
            "foo": testdata.get_ascii(),
            "bar": testdata.get_ascii(),
            "che": 1,
        }

        server = testdata.create_cookieserver(cookies)

        with server:
            res = testdata.fetch(server)
            self.assertEqual(cookies["foo"], res.cookies["foo"])
            self.assertEqual(cookies["bar"], res.cookies["bar"])
            self.assertEqual(str(cookies["che"]), res.cookies["che"])
            self.assertEqual(len(cookies), res.json()["sent_count"])

            res = testdata.fetch(server, cookies=res.cookies)
            self.assertEqual(len(cookies), res.json()["read_count"])

            # test with different case
            res = testdata.fetch(server, headers={"cookie": "foo=1234"})
            self.assertEqual("1234", res.json()["unread_cookies"]["foo"]["value"])

    def test_any(self):
        server = AnyServer()
        with server:
            res = testdata.fetch(server.url("/foo/bar/che"))
            self.assertTrue(204, res.status_code)

            res = testdata.fetch(server.url("/foo"))
            self.assertTrue(204, res.status_code)

            res = testdata.fetch(server)
            self.assertTrue(204, res.status_code)

    def test_alternate_args(self):

        server = testdata.create_fileserver("foo")
        with server:
            res = testdata.fetch(server)
            self.assertEqual("foo", res.content)

        server = testdata.create_fileserver(["foo"])
        with server:
            res = testdata.fetch(server)
            self.assertEqual("foo", res.content)

    def test_serve_1(self):
        server = testdata.create_fileserver({
            "foo.txt": ["foo"],
            "bar.txt": ["bar"],
        })

        server.start()
        res = testdata.fetch(server.url("foo.txt"))
        self.assertEqual("foo", res.content)
        server.stop()

        with server:
            res = testdata.fetch(server.url("bar.txt"))
            self.assertEqual("bar", res.content)

        # !!! For some reason I couldn't create a new instance with the same port
        # and I'm not sure I care enough to fix it and nothing in this worked:
        # https://stackoverflow.com/questions/6380057/python-binding-socket-address-already-in-use
        with testdata.create_fileserver({"che.txt": ["che"]}, port=(server.port + 1)) as s:
        #with testdata.create_fileserver({"che.txt": ["che"]}) as s:
            res = testdata.fetch(s.url("che.txt"))
            self.assertEqual("che", res.content)

    def test_server_encoding(self):
        content = testdata.get_unicode_words()
        server = testdata.create_fileserver({
            "foo.txt": content,
        })

        with server:
            res = testdata.fetch(server.url("foo.txt"))
            self.assertEqual(environ.ENCODING.upper(), res.encoding.upper())
            self.assertEqual(content, res.body)

        server = testdata.create_fileserver({
            "foo.txt": content,
        }, encoding="UTF-16")

        with server:
            res = testdata.fetch(server.url("foo.txt"))
            self.assertNotEqual("UTF-8", res.encoding.upper())
            self.assertEqual(content, res.body)


class PathTest(TestCase):
    def test_csv_writes(self):
        """Turns out, the csv writer didn't write anything in py3"""
        counter = testdata.get_counter()
        csvfile = testdata.create_csv({
            "foo": counter,
            "bar": testdata.get_words,
        })

        for row in csvfile.lines():
            for k in ["foo", "bar"]:
                self.assertTrue(k in row)
                self.assertTrue(row[k])

    def test_create_csv_noheader(self):
        p = testdata.create_csv({
            "foo": testdata.get_name,
            "bar": testdata.get_int,
            "che": testdata.get_words,
        }, count=2, header=False)

        row_count = 0
        for r in p:
            for k in ["foo", "bar", "che"]:
                self.assertTrue(k in r)
                self.assertTrue(r[k])
            row_count += 1
        self.assertEqual(2, row_count)

        p.append([{"foo": 1, "bar": 2, "che": 3}])
        row_count = 0
        for r in p:
            for k in ["foo", "bar", "che"]:
                self.assertTrue(k in r)
                self.assertTrue(r[k])
            row_count += 1
        self.assertEqual(3, row_count)

    def test_create_csv_header(self):
        p = testdata.create_csv({
            "foo": testdata.get_name,
            "bar": testdata.get_int,
            "che": testdata.get_words,
        }, count=2)

        row_count = 0
        for r in p:
            for k in ["foo", "bar", "che"]:
                self.assertTrue(k in r)
                self.assertTrue(r[k])
            row_count += 1
        self.assertEqual(2, row_count)

        p.append([{"foo": 1, "bar": 2, "che": 3}])
        row_count = 0
        for r in p:
            for k in ["foo", "bar", "che"]:
                self.assertTrue(k in r)
                self.assertTrue(r[k])
            row_count += 1
        self.assertEqual(3, row_count)

    def test_head_tail(self):
        count = 10
        p = testdata.create_file(contents=testdata.get_lines(21))
        hlines = p.head(count)
        self.assertEqual(count, len(hlines))

        tlines = p.tail(count)
        self.assertEqual(count, len(tlines))
        self.assertNotEqual("\n".join(hlines), "\n".join(tlines))

    def test_checksum(self):
        contents = "foo bar che"
        path1 = testdata.create_file(contents=contents)
        h1 = path1.checksum()
        self.assertNotEqual("", h1)

        path2 = testdata.create_file(contents=contents)
        h2 = path2.checksum()
        self.assertNotEqual("", h2)

        self.assertEqual(h1, h2)

    def test_existing_file_creation(self):
        path = testdata.create_dir()
        d2 = testdata.create_dir(path)
        self.assertEqual(path, d2)

        relpath = "/foo1/bar1/test.txt"
        s = "happy"
        f = testdata.create_file(relpath, s)

    def test_copy_to(self):
        """https://github.com/Jaymon/testdata/issues/30"""
        source_d = testdata.create_files({
            "foo.txt": testdata.get_words(),
            "bar/che.txt": testdata.get_words(),
        })
        dest_d = testdata.create_dir()

        source_d.copy_to(dest_d)
        self.assertTrue("foo.txt" in dest_d)
        self.assertTrue("bar/che.txt" in dest_d)

        source_f = testdata.create_file("foo.txt", testdata.get_words())
        dest_f = testdata.get_file()
        self.assertFalse(dest_f.exists())
        source_f.copy_to(dest_f)
        self.assertEqual(source_f.contents(), dest_f.contents())

    def test_copy_into(self):
        # directory into directory
        source_d = testdata.create_files({
            "foo.txt": testdata.get_words(),
            "bar/che.txt": testdata.get_words(),
        })
        d = testdata.create_dir()
        d.copy_into(source_d)
        self.assertTrue("foo.txt" in d)
        self.assertTrue("bar/che.txt" in d)

        source_f = testdata.create_file("foo.txt", testdata.get_words())

        # file into directory
        d = testdata.create_dir()
        d.copy_into(source_f)
        self.assertTrue(source_f.basename in d)
        dest_f = d.get_file(source_f.basename)
        self.assertEqual(source_f.contents(), dest_f.contents())

        # file into file
        dest_f = testdata.create_file("foo.txt", testdata.get_words())
        self.assertNotEqual(source_f.contents(), dest_f.contents())
        dest_f.copy_into(source_f)
        self.assertEqual(source_f.contents(), dest_f.contents())
        self.assertTrue(source_f.contents() in dest_f.contents())

    def test_dirpath_clear(self):
        d = testdata.create_dir()
        foo_f = d.create_file("foo.txt", "foo")
        bar_f = d.create_file("bar/bar.txt", "bar")
        che_d = d.create_dir("che")

        self.assertTrue(foo_f.exists())
        self.assertTrue(bar_f.exists())
        self.assertTrue(che_d.exists())

        d.clear()
        self.assertFalse(foo_f.exists())
        self.assertFalse(bar_f.exists())
        self.assertFalse(che_d.exists())
        self.assertEqual(0, len(list(d.files())))

    def test_contents_decode_error(self):
        base_d = testdata.create_dir()
        os.chdir(base_d)
        f = base_d.create_file("bytes.txt", testdata.get_words())

        c = testdata.get_contents(f)
        self.assertTrue(isinstance(c, ContentBytes))

        c = testdata.get_contents(f, encoding="UTF-8")
        self.assertTrue(isinstance(c, ContentString))

    def test_contents(self):
        base_d = testdata.create_dir()
        cwd = os.getcwd()
        os.chdir(base_d)

        # check scanning failure
        with self.assertRaises(IOError):
            c = ContentString("foo", encoding="UTF-8")

        # check scanning success
        foo_f = base_d.create_file("testdata/foo.txt", testdata.get_words())
        c = ContentString("foo", encoding="UTF-8")
        self.assertEqual(foo_f.contents(), c)

        # check passed in directory
        c = ContentString("foo", base_d.child("testdata"), encoding="UTF-8")
        self.assertEqual(foo_f.contents(), c)

        # check direct match
        c = ContentString("foo.txt", encoding="UTF-8")
        self.assertEqual(foo_f.contents(), c)

        # check wrapper
        c = testdata.get_content_body("foo", encoding="UTF-8")
        self.assertEqual(foo_f.contents(), c)

        f = testdata.get_content_file("foo")
        self.assertEqual(f.path, c.path)
        self.assertEqual(f, c.path)

        os.chdir(cwd)

    def test_file(self):
        f = testdata.create_file("foo.txt", "this is the text")
        self.assertEqual("foo", f.fileroot)
        self.assertEqual("txt", f.ext)
        self.assertEqual("foo.txt", f.name)
        self.assertEqual(f.directory, f.parent)

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
        if is_py2:
            self.assertRegexpMatches(f.permissions, r"0[0-7]{3}")
        else:
            self.assertRegex(f.permissions, r"0[0-7]{3}")

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

        f = d.child("foobar.txt")
        self.assertTrue(isinstance(f2, Filepath))

        d2 = d.child("barfoo.txt/")
        self.assertTrue(isinstance(d2, Dirpath))

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

    def test_modules_1(self):
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

    def test_modules_prefix(self):
        mpath = testdata.create_modules({
            "foo": [
                "class Foo(object): pass",
                "class Bar(object): pass",
                "",
            ],
            "bar": [
                "class Che(object): pass",
                "class Bar(object): pass",
                "",
            ],
            "che": [
                "class Baz(object): pass",
                "",
            ],
        }, prefix="modpref")

        mp = mpath.modpath("modpref")
        mps = list(mp.modpaths())
        self.assertTrue(3, len(mps))
        for modpath in ["modpref.foo", "modpref.bar", "modpref.che"]:
            self.assertTrue(modpath in mps)


class MockTest(TestCase):
#     def test_mock_instance(self):
#         instance = testdata.mock_instance(foo=1, bar=lambda *a, **kw: 5)
#         pout.v(instance.foo)
#         pout.v(instance.bar())

    def test_mock_instance(self):
        instance = testdata.mock(foo="1", bar=2, che=lambda *a, **k: 3)
        self.assertEqual("1", instance.foo)
        self.assertEqual("1", instance.foo())
        self.assertTrue(isinstance(instance.bar, int))
        self.assertTrue(isinstance(instance.bar(), int))

    def test_mock_dict(self):
        d = testdata.mock(foo="1", bar=2)
        self.assertEqual("1", d["foo"])
        self.assertEqual("1", d["che"]["baz"]["foo"])

    def test_mock_depth(self):
        """make sure we can mock one object and have it look like many objects"""
        instance = testdata.mock(foo=1)
        self.assertEqual(1, instance.bar.che.foo)

    def test_mock_error(self):
        instance = testdata.mock(foo=AttributeError, bar=RuntimeError("bar is bad"))

        with self.assertRaises(AttributeError):
            instance.foo()

        with self.assertRaises(AttributeError):
            instance.foo

        with self.assertRaisesRegex(RuntimeError, r"bar\s+is\s+bad"):
            instance.bar

        with self.assertRaisesRegex(RuntimeError, r"bar\s+is\s+bad"):
            instance.bar()

    def test_mock_bool(self):
        instance = testdata.mock(foo=True)
        self.assertTrue(instance.foo)
        self.assertTrue(instance.foo())

    def test__is_type(self):
        m = testdata.mock()

        self.assertTrue(m._is_type(True, bool))
        self.assertTrue(m._is_type(False, bool))
        self.assertTrue(m._is_type(bool, bool))
        self.assertFalse(m._is_type(str, bool))

    def test_tuple(self):
        m = testdata.mock(foo=("one", "two"))
        self.assertEqual("one", m.foo[0])
        self.assertEqual("two", m.bar.foo[1])
        self.assertEqual("one", m.foo()[0])
        self.assertEqual("two", m.bar.foo()[1])


class PatchTest(TestCase):
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

    def test_patch_module(self):
        m = testdata.patch_module(environ, {"FOO": 1, "BAR": 2})
        with self.assertRaises(AttributeError):
            environ.FOO
        self.assertEqual(1, m.FOO)


        m = testdata.patch_module(environ.__name__, {"FOO": 1, "BAR": 2})
        with self.assertRaises(AttributeError):
            environ.FOO
        self.assertEqual(1, m.FOO)


class TestdataTest(TestCase):
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

    def test_get_filename(self):
        n = testdata.get_filename(ext="py", name="foo")
        self.assertEqual("foo.py", n)

        n = testdata.get_filename(ext="py", name="foo.py")
        self.assertEqual("foo.py", n)

        n = testdata.get_filename(ext="py", prefix="bar", name="foo.py")
        self.assertEqual("barfoo.py", n)

    def test_get_module_name(self):
        mp = testdata.get_module_name(bits=5, name="foo")
        self.assertTrue(mp.endswith(".foo"))

        mp = testdata.get_module_name(bits=5, prefix="bar", name="foo")
        self.assertTrue(mp.endswith(".barfoo"))

    def test_get_interpreter(self):
        r = testdata.get_interpreter()
        self.assertTrue(r.exists())
        self.assertNotEqual("", r.major)
        self.assertNotEqual("", r.minor)
        self.assertNotEqual("", r.patch)
        self.assertNotEqual("", r.version)

    def test_get_module_name(self):
        for x in range(100):
            mn = testdata.get_module_name(bits=testdata.random.randint(1, 3))
            for bit in mn.split("."):
                self.assertNotRegex(bit, r"^[0-9]")
                self.assertTrue(mn.islower())

        mn = testdata.get_module_name(prefix="get_module_name")
        self.assertTrue(mn.startswith("get_module_name"))

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

    def test_create_file_structure(self):
        raise SkipTest("no longer supported")
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

    def test_create_dirs(self):
        ts = [
            "\\foo\\bar",
            "/foo1/bar1",
            "/foo2/bar2/",
            "foo3/bar3",
            "foo4/bar4/",
            "",
            None
        ]
        d = testdata.create_dirs(ts)

        for t in ts:
            td = d.child(t)
            self.assertTrue(os.path.isdir(d))

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
        s = "happy"

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
                if rp in f.path:
                    count += 1
                    self.assertEqual(v, f.contents())

        self.assertLess(0, count)

    def test_create_image(self):
        d = testdata.create_directory()
        jpg = testdata.create_jpg(tmpdir=d)
        self.assertTrue(jpg.endswith(".jpg"))

        png = testdata.create_png(tmpdir=d)
        self.assertTrue(png.endswith(".png"))

        gif = testdata.create_gif(tmpdir=d)
        self.assertTrue(gif.endswith(".gif"))

        agif = testdata.create_animated_gif(tmpdir=d)
        self.assertTrue(agif.endswith(".gif"))

        ico = testdata.create_ico(tmpdir=d)
        self.assertTrue(ico.endswith(".ico"))

        jpg = testdata.create_jpg("foo", tmpdir=d)
        self.assertTrue(jpg.endswith("foo.jpg"))

        jpg = testdata.create_jpg("bar.jpg", tmpdir=d)
        self.assertTrue(jpg.endswith("bar.jpg"))

    def test_create_png(self):
        import pout
        png_bw = testdata.create_png(width=1000, height=500)
        png_red = testdata.create_png(tmpdir=png_bw.directory, width=1000, height=500, color=[255,0,0])
        self.assertTrue(png_red.exists())
        self.assertTrue(png_bw.exists())

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

    def test_create_modules_4(self):
        """I discovered a bug while fixing some stuff in pyt where create_modules
        seems to create a structure like prefix/prefix/modname.py instead of 
        prefix/modname.py
        """
        basedir = testdata.create_dir()
        prefix = "testdata_cm4"
        r = testdata.create_modules({
            "foo": [
                "class Foo(object): pass",
            ],
            "bar": [
                "class Bar(object): pass",
            ],
        }, basedir, prefix=prefix)

        p = os.path.join(basedir, prefix)
        self.assertTrue(os.path.isdir(p))

        p2 = os.path.join(p, prefix)
        self.assertFalse(os.path.isdir(p2))

    def test_create_package(self):
        prefix = "foo"
        contents = os.linesep.join([
            "class Bar(object): pass",
        ])
        mp = testdata.create_package(prefix, contents=contents)
        self.assertTrue(mp.is_package())

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


class ServiceTest(testdata.TestCase):
    def test_start_service(self):
        # TODO -- figure out how to test this method
        raise self.skip_test()

    def test_stop_service(self):
        # TODO -- figure out how to test this method
        raise self.skip_test()


class UtilsTest(testdata.TestCase):
    def test_conversion(self):
        s = testdata.get_unicode()
        bs = ByteString(s)
        bs2 = ByteString(bs)

        self.assertEqual(bs, bs2)
        self.assertEqual(s, bs.unicode())
        self.assertEqual(s, bs2.unicode())
        self.assertEqual(s, unicode(bs2))
        # self.assertNotEqual(s, bytes(bs2)) # this prints a UnicodeWarning

    def test_string_int(self):
        i = testdata.get_int(0, 1000)
        s = String(i)
        self.assertEqual(str(i), String(i))

