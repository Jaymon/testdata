# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import random
import os
import logging
import time
from time import sleep
from contextlib import contextmanager

from .compat import *
from .test import (
    TestCase,
    skip,
    SkipTest,
    skipIf,
    skipUnless,
    expectedFailure,
    skip_if,
    skip_unless,
    expected_failure,
    expect_failure,
)
from .threading import *
from .client import *
from .output import *
from .path import *
from .service import *
from .mocking import *
from .server import *
from .types.string import *
from .types.number import *
from .types.sequence import *
from .types.mapping import *
from .types.datetime import *
from .user import *
from .base import TestData


__version__ = '6.2.0'


# get rid of "No handler found" warnings (cribbed from requests)
# DEPRECATED 7-15-2022, doesn't seem to be needed in python3
logging.getLogger(__name__).addHandler(logging.NullHandler())


def __getattr__(name):
    """Allow module level magic attribute access

    Any method defined in a TestData subclass will be available on the module
    through this function

    python 3.7+
        * https://peps.python.org/pep-0562/
        * https://stackoverflow.com/a/48916205/5006
    """
    return TestData.__findattr__(name)


###############################################################################
# testdata functions
###############################################################################
class TestdataData(TestData):
    @contextmanager
    def environment(self, thing=None, **kwargs):
        """Context manager to change the os.environ to something else for the life of
        the with statement

        :Example:
            with testdata.environ("FOO"="bar"):
                print(os.environ["FOO"]) # bar

            print(os.environ["FOO"]) # keyError

        :param **kwargs: key is the environment variable name and value is the value
        """
        normalize_value = lambda v: v
        if thing is None:
            thing = os.environ
            normalize_value = lambda v: String(v)

        def has_key(thing, k):
            if isinstance(thing, Mapping):
                ret = k in thing
            else:
                ret = hasattr(thing, k)
            return ret

        def set_key(thing, k, v):
            if isinstance(thing, Mapping):
                thing[k] = v
            else:
                setattr(thing, k, v)

        def get_key(thing, k):
            if isinstance(thing, Mapping):
                ret = thing[k]
            else:
                ret = getattr(thing, k)
            return ret

        def del_key(thing, k):
            if isinstance(thing, Mapping):
                thing.pop(k)
            else:
                delattr(thing, k)

        originals = {}
        try:
            for k, v in kwargs.items():
                if has_key(thing, k):
                    originals[k] = get_key(thing, k)

                set_key(thing, k, normalize_value(v))

            yield originals

        finally:
            for k, v in kwargs.items():
                if k in originals:
                    set_key(thing, k, originals[k])
                else:
                    del_key(thing, k)
    modify = environment
    change = environment
    configure = environment
    environ = environment

    def wait(self, callback, cb_args=None, cb_kwargs=None, timeout=30.0, interval=0.1): 
        """
        keep running callback(*cb_args, **cb_kwargs) until it returns True or timeout is
        reached

        :param callback: callable, the function to call, should return True/False
        :param cb_args: list, any callback arguments
        :param cb_kwargs: dict, any callback keyword arguments
        :param timeout: float, how long you should wait before failing with RuntimeError
        :param interval: float, sleep for this interval inbetween callback calls
        """
        if cb_args is None:
            cb_args = []
        else:
            if not isinstance(cb_args, list):
                cb_args = [cb_args]
        if not cb_kwargs: cb_kwargs = {}
        start = time.time()
        while not callback(*cb_args, **cb_kwargs):
            time.sleep(interval)
            if timeout:
                stop = time.time()
                if (stop - start) >= timeout:
                    raise RuntimeError("wait() timed out after {} seconds".format(timeout))

