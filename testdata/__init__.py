# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import random
import os
import logging
import time
from time import sleep

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


__version__ = '6.3.1'


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
    def wait(self, callback, cb_args=None, cb_kwargs=None, timeout=30.0, interval=0.1): 
        """
        keep running callback(*cb_args, **cb_kwargs) until it returns True or
        timeout is reached

        :param callback: callable, the function to call, should return
            True/False
        :param cb_args: list, any callback arguments
        :param cb_kwargs: dict, any callback keyword arguments
        :param timeout: float, how long you should wait before failing with
            RuntimeError
        :param interval: float, sleep for this interval inbetween callback calls
        """
        if cb_args is None:
            cb_args = []

        else:
            if not isinstance(cb_args, list):
                cb_args = [cb_args]

        if not cb_kwargs:
            cb_kwargs = {}

        start = time.time()
        while not callback(*cb_args, **cb_kwargs):
            time.sleep(interval)
            if timeout:
                stop = time.time()
                if (stop - start) >= timeout:
                    raise RuntimeError(
                        "wait() timed out after {} seconds".format(timeout)
                    )

