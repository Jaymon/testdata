# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import types
import inspect
import sys

from .compat import *


class ByteString(bytes):
    def __new__(cls, val, encoding="UTF-8"):
        if not encoding:
            # ??? use chardet to figure out what encoding val is?
            # https://stackoverflow.com/questions/196345/how-to-check-if-a-string-in-python-is-in-ascii/6988354#6988354
            encoding = sys.getdefaultencoding()

        if isinstance(val, unicode):
            val = val.encode(encoding)

        instance = super(ByteString, cls).__new__(cls, val)
        instance.encoding = encoding
        return instance

    def unicode(self):
        return self.decode(self.encoding)
    __unicode__ = unicode

    def __str__(self):
        return self if is_py2 else self.unicode()

    def __bytes__(self):
        return self


class String(unicode):
    def __new__(cls, val, encoding="UTF-8"):
        if not isinstance(val, (unicode, int)):
            val = ByteString(val, encoding).unicode()
        instance = super(String, cls).__new__(cls, val)
        instance.encoding = encoding
        return instance


class Mock(object):
    """Do our very best to mock functionality

    This class tries to make it easy to mock an object, and can be used to quickly
    get an object that can match a certain state, it isn't exhaustive and will fail
    things like isinstance checks, but it does it's very best to get you a mocked
    up object that you can use for testing.

    If the given attribute doesn't exist then this will return an instance of self
    so you can chain together objects of any depth with just the first object

    :Example:
        m = Mock(foo=1)
        m.foo() # 1
        m.foo # 1
        m.bar.che.foo # 1

        m = Mock(foo=ValueError("the error you want to raise"))
        m.foo(1, 2) # raises ValueError
    """
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def __getitem__(self, key):
        try:
            v = super(Mock, self).__getattribute__(key)

        except AttributeError:
            return self

        else:
            self._raise_if_error(v)
            #self.__dict__["_raise_if_error"](v)
            return v

    def __getattribute__(self, key):
        if hasattr(type(self), key):
            return super(Mock, self).__getattribute__(key)

        try:
            v = super(Mock, self).__getattribute__(key)

        except AttributeError:
            return self

        else:
            if v is not None:

                self._raise_if_error(v)
                #self.__dict__["_raise_if_error"](v)

                if not hasattr(v, "__call__"):

                    frames = inspect.stack()
                    frame = frames[1]
                    loc = "\n".join(frame[4])
                    if ".{}(".format(key) in loc or ".{}".format(key) not in loc:

                        class MockAttr(type(v)):
                            def __new__(cls, *args, **kwargs):
                                return super(MockAttr, cls).__new__(cls, *args, **kwargs)

                            def __call__(self, *args, **kwargs):
                                return v

                        return MockAttr(v)

        return v

    def _raise_if_error(self, v):
        do_raise = False
        try:
            do_raise = isinstance(v, Exception)

        except TypeError:
            pass

        else:
            if do_raise:
                raise v

        try:
            do_raise = issubclass(v, Exception)

        except TypeError:
            pass

        else:
            if do_raise:
                raise v()

