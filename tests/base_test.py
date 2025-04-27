# -*- coding: utf-8 -*-

from testdata.config import environ
from testdata.compat import *
from testdata.base import TestData

from . import TestCase, IsolatedAsyncioTestCase


class TestDataTest(IsolatedAsyncioTestCase):
    def test___getattr__(self):
        class GetAttrData(TestData):
            def _get_foo(self, *args, **kwargs):
                return "foo"

            def __getattr__(self, name):
                if name == "get_foo":
                    return self._get_foo

                else:
                    return super().__getattr__(name)

        class OtherData(TestData):
            def get_bar(self, *args, **kwargs):
                return self.get_foo()

        d = OtherData()
        foo = d.get_bar()
        self.assertEqual("foo", foo)

    async def test_call_method(self):
        """Make sure `TestData.call_method()` is working as expected

        https://github.com/Jaymon/testdata/issues/98
        """
        r = await TestData.call_method("get_int", bad_arg=1)
        self.assertTrue(isinstance(r, int))

        with self.assertRaises(AttributeError):
            await TestData.call_method("no_attr_name_exists")

        with self.assertRaises(TypeError):
            await TestData.call_method("create_callbackserver")


class TestDatasTest(TestCase):
    def test_insert_modules_path(self):
        modpath = self.create_module(
            [
                "from testdata import TestData",
                "",
                "class MockData(TestData):",
                "    def get_mock_foo(self):",
                "        return 1",
            ],
            modpath=self.get_module_name(count=2, name="extras.testdata")
        )

        with self.environ(cwd=modpath.basedir):
            self.data._data_instances.inserted_modules = False
            self.data._data_instances.module_prefixes = set()
            self.assertEqual(1, self.get_mock_foo())

        self.data.delete_class(modpath.get_module().MockData)

    def test_insert_modules_prefix(self):
        modpath = self.create_module(
            [
                "from testdata import TestData",
                "",
                "class MockData(TestData):",
                "    def get_mock_foo(self):",
                "        return 2",
            ],
            modpath=self.get_module_name(count=2, name="extras.testdata")
        )

        with self.environ(TESTDATA_PREFIX=modpath):
            self.data._data_instances.inserted_modules = False
            self.assertEqual(2, self.get_mock_foo())

        self.data.delete_class(modpath.get_module().MockData)

