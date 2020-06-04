# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import time

from testdata.threading import Thread, Deque, Tail
from testdata import threading
from testdata.compat import *
from testdata.utils import ByteString, String
from testdata.client import Command

from . import TestCase, testdata


class DequeTest(TestCase):
    def test_lifecycle(self):
        d = Deque(2)
        self.assertEqual(0, len(d))

        d.append(1)
        self.assertEqual(1, len(d))

        d.append(2)
        self.assertEqual(2, len(d))

        d.append(3)
        self.assertEqual(2, len(d))

        self.assertEqual(2, d[0])
        self.assertEqual(3, d[1])


class Thread3Test(TestCase):
    def setUp(self):
        # !!! this test can trigger a keyboard interrupt error, but I normally don't
        # need to do that so only comment out if needed
        self.skip_test()
        pass

    def test_lifecycle_1(self):
        def run():
            time.sleep(0.25)
            raise ValueError("lifecycle 1")

        thread = Thread(target=run)
        thread.daemon = True
        thread.start()

        while not thread.exception:
            pass

        pout.v(thread.exception)
        #time.sleep(1)

    def test_lifecycle_2(self):
        def run():
            time.sleep(0.25)
            raise ValueError("lifecycle 2")

        thread = Thread(target=run)
        thread.daemon = True
        thread.start()

#         while not thread.exception:
#             pass
# 
#         pout.v(thread.exception)
        #time.sleep(1)


class ThreadTest(TestCase):
#     def tearDown(self):
#         # clear the queue to make sure one test doesn't inherit the error of another test
#         q = threading.exc_queue
#         while not q.empty():
#             q.get(False)
#             q.task_done()

    def test_success(self):
        q = queue.Queue()
        def run():
            q.put(2)

        thread = Thread(target=run)
        thread.start()
        thread.join()
        self.assertEqual(2, q.get(False)) 

    def test_raise_error_daemon_start(self):
        def run():
            raise ValueError("raise_error_daemon_start")

        thread = Thread(target=run)
        thread.daemon = True
        with self.assertRaises(KeyboardInterrupt):
            thread.start()
            while thread.is_alive():
                time.sleep(0.1)

        self.assertIsInstance(thread.exception, ValueError)

    def test_raise_error_start(self):
        def run():
            raise ValueError("raise_error_start")

        thread = Thread(target=run)
        with self.assertRaises(KeyboardInterrupt):
            thread.start()
            while thread.is_alive():
                time.sleep(0.1)

        self.assertIsInstance(thread.exception, ValueError)

    def test_raise_error_join(self):
        def run():
            time.sleep(0.5)
            raise ValueError("raise_error_join")

        thread = Thread(target=run)
        thread.start()
        with self.assertRaises(ValueError):
            thread.join()

    def test_raise_error_daemon_join(self):
        def run():
            time.sleep(0.5)
            raise ValueError("raise_error_daemon_join")

        thread = Thread(target=run)
        thread.daemon = True
        thread.start()
        with self.assertRaises(ValueError):
            thread.join()

    def test_join_2(self):
        def run():
            time.sleep(0.5)
            raise ValueError("join_2")

        thread = Thread(target=run)
        thread.daemon = True
        thread.start()

        try:
            thread.join()

        except ValueError as e:
            self.assertEqual("join_2", str(e))

    def test_no_error_raised(self):
        # https://github.com/Jaymon/testdata/issues/14
        class C2(object):
            def blah(self, *args): pass
        c2 = C2()

        def c2_send():
            c2.blah(foo_bar) # foo_bar doesn't exist so NameError should be raised

        with self.assertRaises(NameError):
            t2 = testdata.Thread(target=c2_send)
            t2.start()
            #pout.h()
            #time.sleep(0.5)
            t2.join()


class TailTest(TestCase):
    def test_tail(self):
        p = testdata.create_file()
        with testdata.capture() as c:
            testdata.tail(p)
            #t = Tail(p)
            #t.start()

            Command("echo 1 >> {}".format(p)).run()
            Command("echo 2 >> {}".format(p)).run()
            Command("echo end >> {}".format(p)).run()

            testdata.wait(lambda: "end" in c)

    def test_tail_2(self):
        self.skip_test("This was handy for manual testing")
        p = testdata.create_file()
        pout.v(p)
        # echo -e "end" >> "/path/printed/above"
        with testdata.capture() as c:
            t = Tail(p)
            t.start()

            testdata.wait(lambda: "end" in c)

    def test_tail_1(self):
        self.skip_test("I could not get this to work reliably")

        with testdata.capture() as c:
            p = testdata.create_file()
            with open(p, "w+") as fp:
                t = Tail(p)
                t.start()

                fp.write(b"Line 1. This line should be on the screen\n")
                fp.write(b"Line 2.\n")
                fp.write(b"Line 3.") 
                fp.write(b" This is another line")
                fp.write(b"\n")

            testdata.wait(lambda: "Line 3." in c)

