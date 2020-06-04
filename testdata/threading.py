# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import threading
import sys
import logging
from collections import deque
import copy
import time
import os

from .compat import queue, _thread, reraise, is_py2


logger = logging.getLogger(__name__)


# these are the errors the queue raises
Queue = queue.Queue
Empty = queue.Empty

#exc_queue = Queue()


# import ctypes
# import atexit
# 
# def foobar():
#     raise ValueError("foobar")
#     #sys.exit(1)
# 
# atexit.register(foobar)

class Deque(list):
    """A Deque object that allows a window into a threaded queue but looks like
    a list

    unlike a traditional queue.Queue that will block when it reaches maxlen this
    will pop an element from the front of the Queue when an element is appended
    to the end of the Queue

    https://docs.python.org/3/tutorial/datastructures.html#more-on-lists
    """
    def __init__(self, maxlen=0):
        self.maxlen = maxlen
        # https://docs.python.org/3/library/collections.html#collections.deque
        self.deque = deque(maxlen=maxlen if maxlen else None)
        # https://docs.python.org/3/library/queue.html#queue.Queue
        self.queue = queue.Queue(maxsize=maxlen if maxlen else 0)
        super(Deque, self).__init__()

    def _consume(self):
        """transfer the outstanding items in the internal queue to the internal deque"""
        while True:
            try:
                x = self.queue.get_nowait()

            except Empty:
                break

            else:
                self.deque.append(x)

    def append(self, x):
        """append an item to the end of the queue

        :param x: object, the item to append
        """
        try:
            self.queue.put_nowait(x)
        except queue.Full:
            _x = self.queue.get_nowait()
            self.append(x)
            #self.deque.append(xd)

    def extend(self, iterable):
        """append all the items of iterable to the end of the queue

        :param iterable: objects, the items to append
        """
        for x in iterable:
            self.append(x)

    def __iter__(self):
        """iterate through the all consumed items as of the call of this method 
        (ie, do not iterate through new queue items)

        :returns: generator
        """
        self._consume()
        for x in self.deque:
            yield x

    def __len__(self):
        """return the total size (deque and queue items)

        :returns: int, the length
        """
        size = len(self.deque) + self.queue.qsize()
        return min(self.maxlen, size) if self.maxlen else size

    def __reversed__(self):
        """support reversed(instance)"""
        self._consume()
        for x in reversed(self.deque):
            yield x

    def count(self, x):
        """how many x are found in

        :param x: object, the item to count
        """
        self._consume()
        return self.deque.count(x) # py >= 3.2

    def index(self, x, start=None, end=None):
        """get the first instance of x found"""
        self._consume()
        return self.deque(x, start, end) # py >= 3.5

    def copy(self):
        self._consume()
        ret = type(self)
        ret.deque = copy.copy(self.deque)
        return ret

    def __getitem__(self, k):
        """override default instance[k] behavior

        :param k] int, the index of the internal deque instance
        :returns: the value found at k
        """
        self._consume()
        return self.deque[k]
        #return super(Deque, self).__getitem__(k)

    def __setitem__(self, *args, **kwargs):
        raise NotImplementedError()
    __delitem__ = __setitem__
    insert = __setitem__
    remove = __setitem__
    pop = __setitem__
    clear = __setitem__
    reverse = __setitem__
    sort = __setitem__
    __add__ = __setitem__
    __mul__ = __setitem__
    __imul__ = __setitem__



class Thread(threading.Thread):
    """
    Drop in replacement for the standard Thread that raises any error

    by default, the threading library suppresses exceptions, this makes using a thread
    for testing kind of annoying since AssertionErrors don't get picked up correctly, but
    this thread will throw the error if .join() is used, and raise a KeyboardInterrupt if
    .join() isn't used (stopping on the error is better than nothing)

    If you want to see what exception was raised you can get that through the .exception
    property

    https://github.com/python/cpython/blob/3.7/Lib/threading.py#L744

    https://stackoverflow.com/questions/2829329/catch-a-threads-exception-in-the-caller-thread-in-python
    https://stackoverflow.com/questions/323972/is-there-any-way-to-kill-a-thread-in-python
    https://stackoverflow.com/questions/2564137/python-how-to-terminate-a-thread-when-main-program-ends

    search:
        python3 raise error on MainThread from child thread
        how does python finish and clean up a thread that stops
    """
    def __init__(self, *args, **kwargs):
        super(Thread, self).__init__(*args, **kwargs)
        self.exc_queue = Queue()

#     def __del__(self):
#         # !!! this only is useful in python 3+ and only because it prints that
#         # the exception was ignored
#         thread_e_info = self.exc_info
#         if thread_e_info:
#             thread_e, thread_exc_info = thread_e_info
#             reraise(*thread_exc_info)

    @property
    def exc_info(self):
        exc_queue = self.exc_queue
        thread_e_info = getattr(self, "thread_e_info", None)
        if not exc_queue.empty():
            thread_e_info = None

        if not thread_e_info:
            try:
                thread_e_info = exc_queue.get(False)
                exc_queue.task_done()

            except Empty:
                pass

            else:
                self.thread_e_info = thread_e_info

        return thread_e_info

    @property
    def exception(self):
        """this will hold the exception if KeyboardInterrupt is raised and .join()
        isn't used"""
        thread_e_info = self.exc_info
        return thread_e_info[0] if thread_e_info else None

    def run(self, *args, **kwargs):
        try:
            super(Thread, self).run(*args, **kwargs)

        except Exception as e:
            # http://stackoverflow.com/a/1854263/5006
            #global exc_queue
            exc_queue = self.exc_queue
            exc_info = sys.exc_info()
            exc_queue.put((e, exc_info))
            logger.exception(e)
            _thread.interrupt_main()

#             t = threading.main_thread()
#             def fail():
#                 reraise(exc_info)
#             t._target = fail
#             t.run()
#             pout.i(t)

#             exc = ctypes.py_object(SystemExit)
#             res = ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(self.ident), exc)
#             pout.v(res)



    def join(self, *args, **kwargs):
        try:
            super(Thread, self).join(*args, **kwargs)

        except KeyboardInterrupt as e:
            pass

        finally:
            if not is_py2:
                # this is here to address this issue:
                # https://github.com/Jaymon/testdata/issues/53
                lock = getattr(self, "_tstate_lock", None)
                if lock:
                    lock.release()

            thread_e_info = self.exc_info
            if thread_e_info:
                thread_e, thread_exc_info = thread_e_info
                reraise(*thread_exc_info)


            #global exc_queue
#             exc_queue = self.exc_queue
#             thread_e_info = None
#             try:
#                 thread_e_info = exc_queue.get(False)
#                 exc_queue.task_done()
# 
#             except Empty:
#                 pass
# 
#             finally:
#                 if thread_e_info:
#                     thread_e, thread_exc_info = thread_e_info
#                     reraise(*thread_exc_info)


class Tail(object):
    """Follow/tail a file and print the new contents of that file to a stream

    This uses threads and has a similar interface to start it

    :Example:
        t = Tail("/path/to/file")
        t.start()
    """

    thread_class = Thread

    def __init__(self, path, stream=None, encoding="UTF-8", **kwargs):
        """
        :param path: string, the path of the file you want to tail/follow
        :param stream: io.IOBase, a file object with a write method
        :param encoding: string, the encoding of lines
        :param **kwargs:
            prefix -- by default prefix is the path basename, but you can set
                something custom here
        """
        self.path = path
        if stream:
            self.stream = stream
        else:
            self.stream = sys.stderr
        self.encoding = encoding
        self.prefix = kwargs.get("prefix", "{}: ".format(os.path.basename(path)))
        if not self.prefix:
            self.prefix = ""

    def start(self):
        t = self.thread_class(target=self.target)
        t.daemon = True
        t.start()

    def target(self):
        # we use regular open here because codecs.open was giving me caching problems
        with open(self.path, mode="rb") as fp:
            fp.seek(0, 2) # we are tailing the file so we don't care about anything before now
            while True:
                line = fp.readline()
                if line:
                    line = line.decode(self.encoding)
                    self.flush(line)
                else:
                    time.sleep(0.1)

    def flush(self, line):
        """flush the line to the stream"""
        self.stream.write("{}{}".format(self.prefix, line))

