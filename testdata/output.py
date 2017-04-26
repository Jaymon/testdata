# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

import sys
import logging
from collections import defaultdict
from contextlib import contextmanager
from .compat import StringIO, is_py2
import inspect
import heapq
from heapq import heappush as hpush, heappop as hpop, merge as hmerge
import time

from . import environ


logger = logging.getLogger(__name__)


class Base(object):
    """Inheriting from this class makes an object appear more string like"""
    def read(self, *args, **kwargs):
        size = kwargs.get("size", args[1] if args else 0)
        ret = "".join(self)
        if size:
            ret = ret[0:size]
        return ret

    def __contains__(self, val):
        """support "VAL" in self"""
        s = self.read()
        return val in s

    def __len__(self):
        """support len(self)"""
        return len(self.read())

    def __getattr__(self, k):
        """Pass through any methods to the underlying string, this allows this
        object to use any string method

        https://docs.python.org/2/library/stdtypes.html#string-methods
        """
        return getattr(self.read(), k)

    def __bool__(self):
        """support bool(self)"""
        return bool(self.read())

    __nonzero__ = __bool__ # py2

    def __bytes__(self):
        """Return b"" string of self's contents"""
        return self.read().encode(sys.getdefaultencoding()) #"utf-8")

    def __unicode__(self):
        """Return "" string of self's contents"""
        return self.read()

    __str__ = __bytes__ if is_py2 else __unicode__


class Stream(Base):
    """This is what will be used in place of stdout and stderr, it saves each string
    that is written to an array with a timestamp, this is so if you want to combine
    the stdout and stderr streams they will be in the correct order

    https://docs.python.org/2/tutorial/inputoutput.html#methods-of-file-objects
    """
    def __init__(self, stream=None):
        """create an instance of this stream capture class

        :param stream: file object, the stream this instance is wrapping, if this
            is passed in then this will save the string and also pass the string
            to this stream
        """
        self.heap = []
        self.stream = stream

    def write(self, s):
        t = time.time()
        hpush(self.heap, (t, s))
        if self.stream:
            self.stream.write(s)

    def __iter__(self):
        for t, s in self.heap:
            yield s


class Capture(Base):
    """Capture stdout and stderr into internal buffers"""
    def __init__(self):
        self.stdout = None
        self.stderr = None
        # I could use the sys ones but docs suggest not to
        # https://docs.python.org/2/library/sys.html#sys.__stdout__
        self.sys_stdout = sys.stdout
        self.sys_stderr = sys.stderr

        self.modified = {
            "stdout": [],
            "stderr": [],
        }
        self.capturing = False

    def __iter__(self):
        bits=hmerge(self.stdout.heap, self.stderr.heap)
        for t, s in bits:
            yield s

    @contextmanager
    def __call__(self, passthrough=None):
        if passthrough is None:
            passthrough = environ.PASSTHROUGH
        self.start(passthrough)
        yield self
        self.stop()

    def capture_modules(self):
        mod_stdout = self.modified["stdout"]
        mod_stderr = self.modified["stderr"]

        for module_name, module in list(sys.modules.items()):
            try:
                members = inspect.getmembers(module)
                for member_name, member in members:
                    if member_name.startswith("__"): continue

                    if member is self.sys_stdout:
                        logger.info("Capturing stdout module member: {}.{}".format(
                            module_name,
                            member_name
                        ))
                        mod_stdout.append((module_name, module, member_name))
                        setattr(module, member_name, self.stdout)

                    elif member is self.sys_stderr:
                        logger.info("Capturing stderr module member: {}.{}".format(
                            module_name,
                            member_name
                        ))
                        mod_stderr.append((module_name, module, member_name))
                        setattr(module, member_name, self.stderr)

            except ImportError:
                pass

    def capture_logging(self):
        mod_stdout = self.modified["stdout"]
        mod_stderr = self.modified["stderr"]
        loggers = list(logging.Logger.manager.loggerDict.items())
        loggers.append(("root", logging.getLogger()))
        for logger_name, logger in loggers:
            for handler in getattr(logger, "handlers", []):
                members = inspect.getmembers(handler)
                for member_name, member in members:
                    if member is self.sys_stdout:
                        logger.info("Capturing stdout logger: {}".format(
                            logger_name,
                        ))
                        mod_stdout.append((logger_name, handler, member_name))
                        setattr(handler, member_name, self.stdout)

                    elif member is self.sys_stderr:
                        logger.info("Capturing stderr logger: {}".format(
                            logger_name,
                        ))
                        mod_stderr.append((logger_name, handler, member_name))
                        setattr(handler, member_name, self.stderr)

    def release(self):
        for stream_name, captures in self.modified.items():
            stream = getattr(self, "sys_{}".format(stream_name))
            for name, obj, member_name in captures:
                logger.info("Releasing {} stream: {}".format(
                    stream_name,
                    name,
                ))
                setattr(obj, member_name, stream)

    def start(self, passthrough=False):
        self.stdout = Stream(self.sys_stdout if passthrough else None)
        self.stderr = Stream(self.sys_stderr if passthrough else None)

        self.capture_modules()
        self.capture_logging()
        self.capturing = True

    def stop(self):
        self.capturing = False
        self.release()

