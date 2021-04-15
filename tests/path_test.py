# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import importlib
from collections import OrderedDict
import inspect

from testdata.path import (
    TempModulepath,
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
    def test_find(self):
        basedir = testdata.create_files({
            "foo.txt": "foo",
            "bar.txt": "bar",
            "che/bam.txt": "bam",
        })

        f = testdata.find_data_file("foo", basedir)
        self.assertEqual(basedir, f.directory)

        f = testdata.find_data_file("bam.txt", basedir)
        self.assertTrue(f.startswith(basedir))
        self.assertTrue(f.endswith("bam.txt"))
        self.assertTrue("che" in f)

    def test_contents_decode_error(self):
        base_d = testdata.create_files({
            "bytes.txt": testdata.get_words(),
        })
        with testdata.chdir(base_d):
            c = testdata.find_data("bytes")
            self.assertTrue(isinstance(c, bytes))

            c = testdata.find_data("bytes", encoding="UTF-8")
            self.assertTrue(isinstance(c, unicode))

    def test_contents_1(self):
        base_d = testdata.create_dir()
        with testdata.chdir(base_d):

            # check scanning failure
            with self.assertRaises(IOError):
                c = testdata.find_data("foo", encoding="UTF-8")

            # check scanning success
            foo_f = base_d.add_file("testdata/foo.txt", testdata.get_words())
            c = testdata.find_data("foo", encoding="UTF-8")
            self.assertEqual(foo_f.read_text(), c)

            # check direct match
            c = testdata.find_data("foo.txt", encoding="UTF-8")
            self.assertEqual(foo_f.read_text(), c)

            # check wrapper
            c = testdata.find_data("foo", encoding="UTF-8")
            f = testdata.find_data_file("foo")
            self.assertEqual(c, f.read_text())

        # check passed in directory
        c = testdata.find_data("foo", base_d.child("testdata"), encoding="UTF-8")
        self.assertTrue(c)


class FilepathTest(TestCase):
    def test_tmpdir(self):
        f = testdata.create_file("first file", ext="txt")
        f2 = testdata.create_file("first file", tmpdir=f.directory, ext="txt")
        self.assertEqual(f.directory, f2.directory)
        self.assertNotEqual(f, f2)

    def test_get_file(self):
        f = testdata.get_file()
        self.assertFalse(f.exists())

        f.write(testdata.get_words())
        self.assertTrue(f.exists())

        f = testdata.get_file("foobar.txt")
        self.assertTrue(f.endswith("foobar.txt"))

        words = testdata.get_words()
        f.write_text(words)
        self.assertEqual(words, f.read_text())

    def test_create_file(self):
        ts = [
            "./foo/bar/test.txt",
            "\\foo\\bar\\test.txt",
            "/foo1/bar1/test.txt",
            "/test.txt",
            "foo3/test.txt",
            "foo4/bar4/che4/test.txt",
        ]
        s = "happy"

        for t in ts:
            f = testdata.create_file(s, t)
            self.assertTrue(os.path.isfile(f))
            self.assertEqual(s, f.read_text())

    def test_get_filename(self):
        n = testdata.get_filename(ext="py", name="foo")
        self.assertEqual("foo.py", n)

        n = testdata.get_filename(ext="py", name="foo.py")
        self.assertEqual("foo.py", n)

        n = testdata.get_filename(ext="py", prefix="bar", name="foo.py")
        self.assertEqual("barfoo.py", n)

    def test_create_files(self):
        filename = testdata.get_filename(ext="txt")
        contents = testdata.get_words()
        file_dict = {
            filename: [contents]
        }
        basedir = testdata.create_files(file_dict)

        count = 0
        for path in basedir.rglob(filename):
            self.assertEqual(contents, path.read_text())
            count += 1
        self.assertEqual(1, count)


class DirpathTest(TestCase):
    def test_get_dir(self):
        d = testdata.get_dir()
        self.assertFalse(d.exists())

    def test_add_1(self):
        """The testdata *path classes can take lists and things as a data body, this
        makes sure that works as expected"""
        contents = testdata.get_words()
        d = testdata.create_dir()
        ts = {
            "foo.txt": [contents],
        }
        ds = d.add(ts)
        path = ds[0]
        self.assertTrue(os.path.isfile(path), "{} does not exist".format(path))
        self.assertEqual(contents, path.read_text())

    def test_create_dir(self):
        ts = [
            "\\foo\\bar",
            "/foo1/bar1",
            "/foo2/bar2/",
            "foo3/bar3",
            "foo4/bar4/",
            "./foo/bar",
            "",
            None
        ]

        for t in ts:
            d = testdata.create_dir(t)
            self.assertTrue(os.path.isdir(d))

        d = testdata.create_dir()
        self.assertTrue(os.path.isdir(d))


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

    def test_create_module_1(self):
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
        self.assertEqual(m.module().__file__, m.path)
        self.assertTrue(m.relpath.endswith(".py"))

    def test_create_module_2(self):
        ts = [
            (
                "foo.bar",
                "Che",
                u"class Che(object): pass"
            )
        ]

        for t in ts:
            m = testdata.create_module(data=t[2], modpath=t[0])
            module = m.module()
            #module = importlib.import_module(t[0])
            class_name = getattr(module, t[1])
            instance = class_name()
            # if all these worked, then the test passed :)

    def test_create_module_package(self):
        m = testdata.create_module("class Foo(object): pass", is_package=False)
        d = m.directory
        self.assertTrue(m.path.endswith("{}.py".format(m)))
        self.assertFalse(m.is_package())

        m2 = testdata.create_module(
            "class Foo(object): pass",
            m,
            tmpdir=m.directory,
            is_package=True
        )
        d2 = m.directory
        self.assertFalse(m2.path.endswith("{}.py".format(m)))
        self.assertTrue(m2.path.endswith("__init__.py"))
        self.assertTrue(m2.is_package())

        self.assertEqual(d, d2)

    def test_create_module_existing(self):
        for is_package in [False, True]:
            m = testdata.create_module("class Foo(object): pass", is_package=is_package)
            self.assertTrue(len(m.read_text()))

            m2 = TempModulepath(m, dir=m.directory)
            self.assertEqual(m.directory, m2.directory)
            self.assertEqual(m, m2)
            self.assertEqual(m.read_text(), m2.read_text())
            self.assertLess(0, len(m2.read_text()))

    def test_directory(self):
        d = testdata.create_dir()

        f = testdata.create_file(tmpdir=d)
        self.assertEqual(d, f.directory)

        p = testdata.create_package(modpath="r.e", tmpdir=d)
        self.assertEqual(os.path.join(d, "r"), p.directory)

        m = testdata.create_module(modpath="d.i", tmpdir=d)
        self.assertEqual(os.path.join(d, "d"), m.directory)

    def test_create_modules_modpath(self):
        modpath = "modpref"
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
        mps = list(mp.modpaths())
        self.assertTrue(3, len(mps))
        for modpath in ["modpref.foo", "modpref.bar", "modpref.che"]:
            self.assertTrue(modpath in mps)

    def test_create_modules_1(self):
        modpath = "test_modules"
        mpath = testdata.create_modules({
            "foo": [
                "class Foo(object): pass",
                "class Bar(object): pass",
            ],
            "bar": [
                "class Che(object): pass",
                "class Bar(object): pass",
            ],
            "che": [
                "class Baz(object): pass",
            ],
        }, modpath=modpath)

        m = mpath.module(modpath)
        # https://stackoverflow.com/a/1547567/5006
        self.assertTrue(inspect.ismodule(m))

        mps = list(mpath.modpaths())
        self.assertEqual(4, len(mps))

        mp = mpath.modpath(modpath)
        self.assertTrue(mp.path.endswith("__init__.py"))
        self.assertEqual(modpath, mp)
        self.assertEqual(m, mp.module())

        mps = list(mp.modpaths())
        self.assertTrue(3, len(mps))
        for modpath in ["test_modules.foo", "test_modules.bar", "test_modules.che"]:
            self.assertTrue(modpath in mps)

        klasses = list(mp.classes())
        self.assertEqual(5, len(klasses))

    def test_create_modules_2(self):
        ts = [
            OrderedDict([
                ("foo2.bar", u"class Che(object): pass"),
                ("foo2.bar.baz", u"class Che(object): pass"),
            ])
        ]

        tmpdir = testdata.create_dir()
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

    def test_create_modules_3(self):
        prefix = "testdata_cm2"
        r = testdata.create_modules({
            prefix: {
                "": [
                    "class Default(object):",
                    "    def GET(*args, **kwargs): pass",
                ],
                "default": [
                    "class Default(object):",
                    "    def GET(*args, **kwargs): pass",
                ],
                "foo": [
                    "class Default(object):",
                    "    def GET(*args, **kwargs): pass",
                    "",
                    "class Bar(object):",
                    "    def GET(*args, **kwargs): pass",
                    "    def POST(*args, **kwargs): pass",
                ],
                "foo.baz": [
                    "class Default(object):",
                    "    def GET(*args, **kwargs): pass",
                    "",
                    "class Che(object):",
                    "    def GET(*args, **kwargs): pass",
                ],
            }
        })

        module = importlib.import_module(prefix)
        class_name = getattr(module, "Default")
        instance = class_name()

    def test_create_modules_4(self):
        prefix = "testdata_cm3"
        r = testdata.create_modules({
            "foo.bar": [
                "class Bar(object): pass",
            ],
            "foo.bar.che.baz": [
                "class Baz(object): pass",
                ""
            ],
        }, prefix)

        self.assertEqual(5, len(list(r.modules())))

        m = r.module("{}.foo.bar.che.baz".format(prefix))
        c = m.Baz() # if this doesn't raise error, it worked

        mp = r.modpath("{}.foo".format(prefix))
        self.assertTrue(mp.is_package())

    def test_create_modules_5(self):
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
        }, tmpdir=basedir, modpath=prefix)

        p = os.path.join(basedir, prefix)
        self.assertTrue(os.path.isdir(p))

        p2 = os.path.join(p, prefix)
        self.assertFalse(os.path.isdir(p2))

    def test_create_package(self):
        prefix = "foo"
        data = [
            "class Bar(object): pass",
        ]
        mp = testdata.create_package(data, prefix)
        self.assertTrue(mp.is_package())

    def test_get_module_name_1(self):
        mp = testdata.get_module_name(count=5, name="foo")
        self.assertTrue(mp.endswith(".foo"))

        mp = testdata.get_module_name(count=5, prefix="bar", name="foo")
        self.assertTrue(mp.endswith(".barfoo"))

    def test_get_module_name_2(self):
        for x in range(100):
            mn = testdata.get_module_name(count=testdata.random.randint(1, 3))
            for bit in mn.split("."):
                self.assertNotRegex(bit, r"^[0-9]")
                self.assertTrue(mn.islower())

        mn = testdata.get_module_name(prefix="get_module_name")
        self.assertTrue(mn.startswith("get_module_name"))


class ImageTest(TestCase):
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


class InterpreterTest(TestCase):
    def test_get_interpreter(self):
        r = testdata.get_interpreter()
        self.assertTrue(r.exists())
        self.assertNotEqual("", r.major)
        self.assertNotEqual("", r.minor)
        self.assertNotEqual("", r.patch)
        self.assertNotEqual("", r.version)

