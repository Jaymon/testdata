# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import importlib
from collections import OrderedDict

from testdata.path import (
    Dirpath,
    Filepath,
    Modulepath,
    ContentBytes,
    ContentString,
    ContentFilepath
)
from testdata.compat import *
from testdata.utils import ByteString, String

from . import TestCase, testdata, SkipTest


class CSVTest(TestCase):
    def test_csv_no_callback(self):
        """Turns out, the csv writer didn't write anything in py3"""
        csvfile = testdata.create_csv({
            "foo": testdata.get_int(),
            "bar": testdata.get_words(),
        })
        self.assertEqual(1, len(csvfile))

    def test_csv_writes(self):
        """Turns out, the csv writer didn't write anything in py3"""
        counter = testdata.get_counter()
        csvfile = testdata.create_csv({
            "foo": counter,
            "bar": testdata.get_words,
        })

        for row in csvfile:
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

        p.add({"foo": 1, "bar": 2, "che": 3})
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

        p.add({"foo": 1, "bar": 2, "che": 3})
        row_count = 0
        for r in p:
            for k in ["foo", "bar", "che"]:
                self.assertTrue(k in r)
                self.assertTrue(r[k])
            row_count += 1
        self.assertEqual(3, row_count)


class ContentTest(TestCase):
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



class FilepathTest(TestCase):
    def test_existing_file_creation(self):
        path = testdata.create_dir()
        d2 = testdata.create_dir(path)
        self.assertEqual(path, d2)

        relpath = "/foo1/bar1/test.txt"
        s = "happy"
        f = testdata.create_file(relpath, s)

    def test_tmpdir(self):
        f = testdata.create_file("first file", ext="txt")
        f2 = testdata.create_file("first file", tmpdir=f.directory, ext="txt")
        self.assertEqual(f.directory, f2.directory)
        self.assertNotEqual(f, f2)


class ModulepathTest(TestCase):
    def test_tmpdir(self):
        m = testdata.create_module([
            "class Foo(object): pass",
        ])
        m2 = testdata.create_module([
            "class Foo(object): pass",
        ], tmpdir=m.basedir)
        m3 = testdata.create_module([
            "class Foo(object): pass",
        ])
        self.assertEqual(m.directory, m2.directory)
        self.assertNotEqual(m.directory, m3.directory)
        self.assertNotEqual(m, m2)
        self.assertNotEqual(m, m3)

    def test_create_module_2(self):
        m = testdata.create_module([
            "from unittest import TestCase",
            "class FooTest(TestCase):",
            "    def test_foo(self):",
            "        pass",
        ], "foo.bar.che")
        self.assertEqual("foo.bar.che", m)
        self.assertFalse(m.is_package())

        m = testdata.create_module([
            "from unittest import TestCase",
            "class FooTest(TestCase):",
            "    def test_foo(self):",
            "        pass",
        ])
        self.assertFalse(m.is_package())
        self.assertEqual(m.module.__file__, m.path)
        self.assertTrue(m.relpath.endswith(".py"))

    def test_directory(self):
        d = testdata.create_dir()

        f = testdata.create_file(tmpdir=d)
        self.assertEqual(d, f.directory)

        p = testdata.create_package(modpath="r.e", tmpdir=d)
        self.assertEqual(os.path.join(d, "r", "e"), p.directory)

        m = testdata.create_module(modpath="d.i", tmpdir=d)
        self.assertEqual(os.path.join(d, "d"), m.directory)

    def test_create_modules_1(self):
        modpath = "test_modules"
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
        }, modpath=modpath)

        mp = mpath.modpath(modpath)
        pout.v(mp)
        mps = list(mp.modpaths())
        pout.v(mps)
        return
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

    def test_get_module_name_1(self):
        mp = testdata.get_module_name(bits=5, name="foo")
        self.assertTrue(mp.endswith(".foo"))

        mp = testdata.get_module_name(bits=5, prefix="bar", name="foo")
        self.assertTrue(mp.endswith(".barfoo"))

    def test_get_module_name_2(self):
        for x in range(100):
            mn = testdata.get_module_name(bits=testdata.random.randint(1, 3))
            for bit in mn.split("."):
                self.assertNotRegex(bit, r"^[0-9]")
                self.assertTrue(mn.islower())

        mn = testdata.get_module_name(prefix="get_module_name")
        self.assertTrue(mn.startswith("get_module_name"))


class TestdataTest(TestCase):
    def test_get_filename(self):
        n = testdata.get_filename(ext="py", name="foo")
        self.assertEqual("foo.py", n)

        n = testdata.get_filename(ext="py", name="foo.py")
        self.assertEqual("foo.py", n)

        n = testdata.get_filename(ext="py", prefix="bar", name="foo.py")
        self.assertEqual("barfoo.py", n)

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

        d = testdata.create_dir()
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

