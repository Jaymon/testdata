# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from testdata.config import environ
from testdata.compat import *
from testdata.base import TestData

from . import TestCase


class TestDataTest(TestCase):
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

