# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from testdata.compat import *

from . import TestCase, testdata


class MockTest(TestCase):
    def test_mock_instance(self):
        """make sure .mock_instance() acts like .mock()"""
        instance = testdata.mock_instance("FooBar", foo="1", bar=2)
        self.assertEqual("1", instance.foo)
        self.assertEqual("1", instance.foo())
        self.assertTrue(isinstance(instance.bar, int))
        self.assertTrue(isinstance(instance.bar(), int))

    def test_mock_1(self):
        instance = testdata.mock(foo="1", bar=2, che=lambda *a, **k: 3)
        self.assertEqual("1", instance.foo)
        self.assertEqual("1", instance.foo())
        self.assertTrue(isinstance(instance.bar, int))
        self.assertTrue(isinstance(instance.bar(), int))
        self.assertEqual(3, instance.che())

    def test_mock_2(self):
        instance = testdata.mock({"foo.bar.che": 1})
        self.assertEqual(1, instance.foo.bar.che)

    def test_mock_dict(self):
        d = testdata.mock(foo="1", bar=2)
        self.assertEqual("1", d["foo"])
        self.assertEqual("1", d["che"]["baz"]["foo"])

    def test_mock_depth_attr(self):
        """make sure we can mock one object and have it look like many objects"""
        instance = testdata.mock(foo=1)
        self.assertEqual(1, instance.bar.che.foo)

    def test_mock_depth_method(self):
        """make sure we can mock one object and have it look like many objects"""
        instance = testdata.mock(foo=1)
        self.assertEqual(1, instance.bar().che().foo())

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

        self.assertTrue(isinstance(instance.foo, bool))
        self.assertTrue(isinstance(instance.foo(), bool))

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
        mpath = testdata.create_module()
        morig = mpath.module()

        m = testdata.patch_module(morig, {"FOO": 1, "BAR": 2})
        with self.assertRaises(AttributeError):
            morig.FOO
        self.assertEqual(1, m.FOO)

        m = testdata.patch_module(mpath, {"FOO": 1, "BAR": 2})
        with self.assertRaises(AttributeError):
            morig.FOO
        self.assertEqual(1, m.FOO)

    def test_patch_module_nested(self):
        mpath = testdata.create_module()
        morig = mpath.module()

        m = testdata.patch_module(morig, {"foo.bar.che": 1, "os.getcwd": "/foo/bar"})
        self.assertEqual(1, m.foo.bar.che)
        self.assertEqual("/foo/bar", m.os.getcwd())

    def test_patch_method_without_method(self):
        """Make sure patching a method with a non-method wraps the non-method in
        a method"""
        class Foo(object):
            def barmethod(self):
                return "barmethod"

            @classmethod
            def barclass(cls):
                return "barclass"

            def barstatic():
                return "barstatic"

        m = testdata.patch_instance(
            Foo(),
            barmethod="barmethod 3", 
            barclass="barclass 3", 
            barstatic="barstatic 3", 
        )
        self.assertEqual("barmethod 3", m.barmethod())
        self.assertEqual("barclass 3", m.barclass())
        self.assertEqual("barstatic 3", m.barstatic())

        m_class = testdata.patch_class(
            Foo,
            barmethod="barmethod 2", 
            barclass="barclass 2", 
            barstatic="barstatic 2", 
        )

        m = m_class()
        self.assertEqual("barmethod 2", m.barmethod())
        self.assertEqual("barclass 2", m.barclass())
        self.assertEqual("barstatic 2", m.barstatic())

