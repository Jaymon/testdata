# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import logging

from testdata import environ
from testdata.compat import *
from testdata.server import AnyServer, CookieServer, CallbackServer
from testdata.client import HTTP, Command

from . import TestCase, testdata


class FileserverTest(TestCase):
    def test_close(self):
        content = testdata.get_unicode_words()
        server = testdata.create_fileserver({
            "foo.txt": content
        })

        with server:
            pass

    def test_alternate_args(self):
        content = testdata.get_words()

        server = testdata.create_fileserver(content)
        with server:
            res = testdata.fetch(server)
            self.assertEqual(content, res.content)

        server = testdata.create_fileserver([content])
        with server:
            res = testdata.fetch(server)
            self.assertEqual(content, res.content)

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
        name = testdata.get_filename(ext="txt")
        content = testdata.get_unicode_words()

        server = testdata.create_fileserver({
            name: content,
        })
        with server:
            res = testdata.fetch(server.url(name))
            self.assertEqual(environ.ENCODING.upper(), res.encoding.upper())
            self.assertEqual(content, res.body)

        server = testdata.create_fileserver({
            name: content,
        }, encoding="UTF-16")
        with server:
            res = testdata.fetch(server.url(name))
            self.assertNotEqual("UTF-8", res.encoding.upper())
            self.assertEqual(content, res.body)


class CookieServerTest(TestCase):
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


class CallbackServerTest(TestCase):
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


class AnyServerTest(TestCase):
    def test_any(self):
        server = AnyServer()
        with server:
            res = testdata.fetch(server.url("/foo/bar/che"))
            self.assertTrue(204, res.status_code)

            res = testdata.fetch(server.url("/foo"))
            self.assertTrue(204, res.status_code)

            res = testdata.fetch(server)
            self.assertTrue(204, res.status_code)

