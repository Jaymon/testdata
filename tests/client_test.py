# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import time

from testdata.compat import *
from testdata.service import Systemd
from testdata.utils import ByteString, String
from testdata.server import CallbackServer
from testdata.client import HTTP, Command

from . import TestCase, testdata, SkipTest


class CommandTest(TestCase):
    def test_murder(self):
        start = time.time()
        c = Command("sleep 15")
        c.run_async()
        c.murder(15)
        stop = time.time()
        self.assertTrue((stop - start) < 10)

    def test_create_cmd(self):
        c = Command("sleep 1")

        cmd = c.create_cmd("echo foo", "")
        self.assertEqual("echo foo", cmd)

        c.sudo = True
        cmd = c.create_cmd(["echo", "foo"], "")
        self.assertEqual("sudo", cmd[0])


class ClientTest(TestCase):
    def test_run_environ(self):
        env = dict(os.environ)
        contents = "some value"
        env["TEST_RUN_ENVIRON"] = contents
        r = testdata.run("echo $TEST_RUN_ENVIRON", environ=env)
        self.assertEqual(contents, r)

    def test_async(self):
        start = time.time()

        c = Command("sleep 1.0")
        c.run_async()

        mid = time.time()

        r = c.join()
        stop = time.time()

        self.assertTrue((stop - start) > 0.5)
        self.assertTrue((mid - start) < 0.5)
        self.assertEqual(0, r.returncode)

        s = testdata.get_ascii()
        c = Command("echo {}".format(s))
        c.run_async()
        r = c.join()
        self.assertEqual(s, r.strip())

    def test_quit(self):
        start = time.time()
        c = Command("sleep 5.0")
        c.run_async()
        time.sleep(0.1)
        c.quit()
        c.join()
        stop = time.time()
        self.assertTrue((stop - start) < 4.0)

    def test_kill(self):
        start = time.time()
        c = Command("sleep 5.0")
        c.run_async()
        time.sleep(0.1)
        c.kill()
        c.join()
        stop = time.time()
        self.assertTrue((stop - start) < 4.0)

    def test_terminate(self):
        start = time.time()
        c = Command("sleep 5.0")
        c.run_async()
        time.sleep(0.1)
        c.terminate()
        c.join()
        stop = time.time()
        self.assertTrue((stop - start) < 4.0)

    def test_unicode_output(self):
        mod1 = testdata.create_module("foo.bar.__main__", [
            "import testdata",
            "print(testdata.get_unicode_words().encode('utf8'))",
        ])

        r = testdata.run(mod1)

    def test_return_code(self):
        path1 = testdata.create_file("foo.py", ["print('foo')", "exit(1)"])
        r = testdata.run(path1, code=1)
        self.assertTrue("foo" in r)

        with self.assertRaises(RuntimeError):
            r = testdata.run(path1)

    def test_return_code_2(self):
        c = Command("echo 1")
        r = c.run()
        self.assertEqual(0, r.returncode)

        c = Command("false")
        r = c.run(code=1)
        self.assertEqual(1, r.returncode)

    def test_int_environ(self):
        """https://github.com/Jaymon/testdata/issues/37"""
        c = Command("echo 1")
        c.environ["FOOINT"] = 0
        r1 = c.run() # if it doesn't error out then it was a success

    def test_run_basic(self):
        r1 = testdata.run("echo 1")
        r2 = testdata.run(["echo", "1"])
        self.assertEqual(r1, r2)

    def test_run_file(self):
        path1 = testdata.create_file("foo.py", "print(1)")
        path2 = testdata.get_file(path1.fileroot, tmpdir=path1.basedir)

        r1 = testdata.run(path1)
        r2 = testdata.run(path2)
        r3 = path1.run()
        r4 = path2.run()
        self.assertTrue(r1 == r2 == r3 == r4)

    def test_run_module(self):
        mod1 = testdata.create_module("foo.bar.__main__", "print(1)")
        #pout.v(mod1.parent, mod1.relpath, mod1)
        r1 = testdata.run(mod1)
        r2 = mod1.run()
        self.assertEqual(r1, r2)

    def test_alternative_method(self):
        def do_PUT(handler):
            return "PUT"

        server = CallbackServer({
            "PUT": do_PUT,
        })
        with server:
            c = HTTP(server)
            res = c.put(server)
            self.assertEqual(200, res.code)
            self.assertEqual("PUT", res.body)



