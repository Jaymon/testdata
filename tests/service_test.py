# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from testdata.compat import *
import testdata
from testdata.test import TestCase, SkipTest
from testdata.service import Systemd
from testdata.utils import ByteString, String


testdata.basic_logging()


class SystemdTest(TestCase):
    def test_format(self):
        s = Systemd("foo")
        c, kw = s.format_cmd("start")

        self.assertEqual("sudo systemctl start foo", " ".join(c))

    def test_status(self):
        s = Systemd("foo")
        active = [
            'foo.service - "foo"',
            'Loaded: loaded (/etc/systemd/system/foo.service; enabled; vendor preset: enabled)',
            'Active: active (running) since Wed YYYY-MM-DD HH:MM:SS UTC; N days ago',
            'Main PID: NNNNN (name)',
            'Status: "foo is ready"',
            '    Tasks: 3 (limit: 2362)',
            'CGroup: /system.slice/foo.service',
        ]
        s = testdata.patch(s, status=lambda *_, **__: "\n".join(active))
        self.assertTrue(s.is_running())

        s = Systemd("foo")
        inactive = [
            'foo.service - "foo"',
            'Loaded: loaded (/etc/systemd/system/foo.service; enabled; vendor preset: enabled)',
            'Active: inactive (dead)',
        ]
        s = testdata.patch(s, status=lambda *_, **__: "\n".join(inactive))
        self.assertFalse(s.is_running())

    def test_exists(self):

        s = Systemd("foo")
        s.path # just make sure there aren't any syntax errors

