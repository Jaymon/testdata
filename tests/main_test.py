# -*- coding: utf-8 -*-
import argparse

from testdata.__main__ import (
    ApplicationParser,
    FunctionParser,
)

from . import TestCase


class ApplicationParserTest(TestCase):
    def test_parse(self):
        p = ApplicationParser()

        parsed = p.parse_args(["get_int", "--max_size", "700"])
        self.assertEqual("700", parsed.max_size)
        self.assertEqual(1, parsed.min_size)
        return

        parsed = p.parse_args(["get_int"])
        for name in ["min_size", "max_size"]:
            self.assertTrue(name in parsed)

        parsed = p.parse_args(["get_int", "500", "600"])
        self.assertEqual("500", parsed.min_size)
        self.assertEqual("600", parsed.max_size)


class FunctionParserTest(TestCase):
    def test_default_positional_optional(self):
        def foo(bar=1):
            pass

        p = FunctionParser(foo, exit_on_error=False)
        parsed = p.parse_args(["foo", "--bar", "2"])
        self.assertEqual("2", parsed.bar)

        parsed = p.parse_args(["foo", "3"])
        self.assertEqual("3", parsed.bar)

        with self.assertRaises((argparse.ArgumentError, SystemExit)):
            p.parse_args(["foo", "--bar", "3", "4"])

