import sys
import io
from contextlib import contextmanager
import inspect
from heapq import heappush as hpush, merge as hmerge
import time
from collections import UserString

from datatypes import logging

from .config import environ
from .compat import *
from .base import TestData


logger = logging.getLogger(__name__)


class Base(UserString):
    """Inheriting from this class makes an object appear more string like"""
    @property
    def data(self):
        return self.read()

    def __init__(self):
        super().__init__("")

    def read(self, *args, **kwargs):
        size = kwargs.get("size", args[1] if args else 0)
        ret = "".join(self)
        if size:
            ret = ret[0:size]
        return ret

    def __iter__(self):
        raise NotImplementedError(
            "Base classes should implement this to support read()"
        )


class Stream(Base):
    """This is what will be used in place of stdout and stderr, it saves each
    string that is written to an array with a timestamp, this is so if you want
    to combine the stdout and stderr streams they will be in the correct order

    https://docs.python.org/2/tutorial/inputoutput.html#methods-of-file-objects
    """
    def __init__(self, stream: io.IOBase, passthrough: bool = True):
        """create an instance of this stream capture class

        :param stream: file object, the stream this instance is wrapping, if this
            is passed in then this will save the string and also pass the string
            to this stream
        """
        self.heap = []
        self.heaptimes = set()
        self.stream = stream
        self.capturing = False
        self.passthrough = passthrough

    def write(self, s):
        if self.capturing:
            # sometimes `time.time_ns` returns the same value on subsequent
            # calls
            # https://stackoverflow.com/questions/1938048/
            # https://stackoverflow.com/a/38256446
            t = time.time_ns()
            while t in self.heaptimes:
                t += 1
            self.heaptimes.add(t)
            hpush(self.heap, (t, s))

        if self.passthrough:
            self.stream.write(s)

    def __iter__(self):
        for t, s in self.heap:
            yield s

    def __getattr__(self, k):
        """first try and proxy unknown keys to the string, if that fails
        then try and proxy to the wrapped stream instance"""
        try:
            return super().__getattr__(k)

        except AttributeError:
            return getattr(self.stream, k)


class Capture(Base):
    """Capture stdout and stderr into internal buffers

    .. note:: This only captures stdout and stderr streams, even in loggers
    """
    def __init__(self, stdout=True, stderr=True, loggers=True):
        """create a capture instance

        :param stdout: capture stdout streams
        :param stderr: capture stderr streams
        :param loggers: capture stdout and stderr streams of loggers
        """
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

        self.capture_stdout = stdout
        self.capture_stderr = stderr
        self.capture_loggers = loggers

    def __iter__(self):
        bits=hmerge(self.stdout.heap, self.stderr.heap)
        for t, s in bits:
            yield s

    @contextmanager
    def __call__(self, passthrough=None):
        try:
            if passthrough is None:
                passthrough = environ.PASSTHROUGH
            self.start(passthrough)
            yield self

        finally:
            self.stop()

    def capture_sys(self):
        """just switch out sys.stdout and sys.stderr which is exactly what python
        proper does:

            https://github.com/python/cpython/blob/3.6/Lib/test/support/__init__.py#L1458
            https://github.com/python/cpython/blob/2.7/Lib/test/support/__init__.py#L1211
        """
        mod_stdout = self.modified["stdout"]
        mod_stderr = self.modified["stderr"]

        if self.capture_stdout:
            logger.debug("Capturing sys: stdout")
            mod_stdout.append(("sys", sys, "stdout"))
            setattr(sys, "stdout", self.stdout)

        if self.capture_stderr:
            logger.debug("Capturing sys: stderr")
            mod_stderr.append(("sys", sys, "stderr"))
            setattr(sys, "stderr", self.stderr)

    def capture_logging(self):
        if not self.capture_loggers:
            return
        if not self.capture_stdout and not self.capture_stderr:
            return

        mod_stdout = self.modified["stdout"]
        mod_stderr = self.modified["stderr"]

        for l, handler in logging.get_handlers():
            if isinstance(handler, logging.StreamHandler):
                if handler.stream is self.sys_stdout:
                    if self.capture_stdout:
                        logger.debug(f"Capturing stdout logger: {l.name}")
                        mod_stdout.append((l.name, handler, "stream"))
                        setattr(handler, "stream", self.stdout)

                elif handler.stream is self.sys_stderr:
                    if self.capture_stderr:
                        logger.debug(f"Capturing stderr logger: {l.name}")
                        mod_stderr.append((l.name, handler, "stream"))
                        setattr(handler, "stream", self.stderr)

                else:
                    members = inspect.getmembers(handler.stream)
                    for member_name, member in members:
                        if self.capture_stdout and member is self.sys_stdout:
                            mname = f"{l.name}.stream.{member_name}"
                            logger.debug(f"Capturing stdout logger: {mname}")
                            mod_stdout.append(
                                (mname, handler.stream, member_name)
                            )
                            setattr(handler.stream, member_name, self.stdout)

                        elif self.capture_stderr and member is self.sys_stderr:
                            mname = f"{l.name}.stream.{member_name}"
                            logger.debug(f"Capturing stderr logger: {mname}")
                            mod_stderr.append(
                                (mname, handler.stream, member_name)
                            )
                            setattr(handler.stream, member_name, self.stderr)

    def start(self, passthrough=False):
        self.stdout = Stream(self.sys_stdout, passthrough)
        self.stderr = Stream(self.sys_stderr, passthrough)

        self.capture_sys()
        self.capture_logging()

        self.stdout.capturing = True
        self.stderr.capturing = True

    def stop(self):
        self.stdout.capturing = False
        self.stderr.capturing = False

        for stream_name, captures in self.modified.items():
            stream = getattr(self, "sys_{}".format(stream_name))
            for logger_name, obj, member_name in captures:
                logger.debug(f"Releasing {stream_name} stream: {logger_name}")
                setattr(obj, member_name, stream)


###############################################################################
# testdata functions
###############################################################################
class OutputData(TestData):
    def basic_logging(self, **kwargs):
        """Lots of times, in tests, I have to add a basic logger, it's basically
        the same code over and over again, this will just make that a little
        easier to do

        :example:
            import testdata
            testdata.basic_logging() # near top of file

        :param **kwargs: key/val, these will be passed into logger.basicConfig
            method
        """
        logging.quick_config(**kwargs)

    def capture(
        self,
        stdout: bool = True,
        stderr: bool = True,
        loggers: bool = True,
        **kwargs,
    ) -> Capture:
        """Capture stdout and stderr so you can inspect it

        this is handy for tests when you are trying to figure out if logging or
        whatnot is doing the correct thing

        I'd always wanted something similar to php's output buffering
        `ob_start()` method
        http://www.php.net/manual/en/function.ob-start.php

        This is not a log capturing method for tests, this really is more like
        php's `ob_start` where it captures stdout and stderr output, and this
        is what this method is for, if you need to capture logs then you
        should use unittest's `assertLogs`

        :example:
            with testdata.capture() as c:
                print("foo")
            if "foo" in c:
                print("foo was captured")

        :param stdout: capture stdout streams
        :param stderr: capture stderr streams
        :param loggers: capture stdout and stderr streams of loggers
        :returns: output.Capture instance
        """
        c = Capture(stdout=stdout, stderr=stderr, loggers=loggers)
        return c(**kwargs)

