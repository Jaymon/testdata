# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os

from testdata.compat import *
from testdata import environ

from . import TestCase, testdata


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
    def test_patch_1(self):

        @classmethod
        def mock_bam(*args, **kwargs): return 22

        def mock_boom(): return 2
        contents = [
            "def boom():",
            "    return 1",
            "",
            "class FooPatch(object):",
            "    @classmethod",
            "    def bam(cls): return boom()",
            ""
        ]
        m = testdata.create_module(contents)
        foo = m.module()

        self.assertEqual(1, foo.FooPatch.bam())

        FP = testdata.patch(foo.FooPatch, bam=mock_bam)
        self.assertEqual(22, FP.bam())

        self.assertEqual(1, foo.FooPatch.bam())
        foo = testdata.patch(foo, boom=mock_boom)
        self.assertEqual(2, foo.FooPatch.bam())

        foo = testdata.patch(m, boom=mock_boom)
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
        contents = [
            "class PatchFactory(object):",
            "    def clone(self): return type(self)()",
            "    def bar(self): return 55",
            ""
        ]
        m = testdata.create_module(contents)
        pathclassmod = m.module()

        def mock_bar(self):
            return 33

        MonkeyFactory = testdata.patch_class(
            pathclassmod.PatchFactory,
            bar=mock_bar
        )

        f = pathclassmod.PatchFactory()
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

    def test_patch_class_classmethod(self):
        class Che(object):
            pass

        class Foo(Che):
            @staticmethod
            def barstatic(): return "static"

            def barinstance(self): return "instance"

            @classmethod
            def barclass(cls):
                return "class"

        MonkeyFoo = testdata.patch_class(
            Foo,
            barclass=lambda *_, **__: 1,
            barstatic=lambda *_, **__: 2,
            barinstance=lambda *_, **__: 3,
        )

        self.assertEqual(1, MonkeyFoo.barclass())
        self.assertEqual(2, MonkeyFoo.barstatic())
        self.assertEqual(3, MonkeyFoo().barinstance())

        f = Foo()
        self.assertTrue(isinstance(f, Foo))

        f2 = MonkeyFoo()
        self.assertTrue(isinstance(f2, Foo))

    def test_patch_module(self):
        m = testdata.patch_module(environ, {"FOO": 1, "BAR": 2})
        with self.assertRaises(AttributeError):
            environ.FOO
        self.assertEqual(1, m.FOO)

        m = testdata.patch_module(environ.__name__, {"FOO": 1, "BAR": 2})
        with self.assertRaises(AttributeError):
            environ.FOO
        self.assertEqual(1, m.FOO)


