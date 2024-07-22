# -*- coding: utf-8 -*-

from datatypes import ReflectCallable

from testdata.__main__ import (
    ApplicationParser
)

from . import TestCase


class ApplicationParserTest(TestCase):
    def test_parse(self):
        p = ApplicationParser()
        parsed = p.parse_args(["get_int"])
        for name in ["min_size", "max_size"]:
            self.assertTrue(name in parsed)

        parsed = p.parse_args(["get_int", "500", "600"])
        self.assertEqual("500", parsed.min_size)
        self.assertEqual("600", parsed.max_size)

        parsed = p.parse_args(["get_int", "--max_size", "700"])
        self.assertEqual(1, parsed.min_size)
        self.assertEqual("700", parsed.max_size)

