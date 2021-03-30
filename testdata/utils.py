# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import types
import inspect
import sys

from .compat import *


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
            # this makes sure methods defined on this class get through this call
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

                        # https://stackoverflow.com/questions/2172189/why-i-cant-extend-bool-in-python
                        class_type = type(v) if self._is_type(v, bool) == 0 else object 

                        class MockAttr(class_type):
                            def __new__(cls, *args, **kwargs):
                                try:
                                    return super(MockAttr, cls).__new__(cls, *args, **kwargs)
                                except TypeError:
                                    return super(MockAttr, cls).__new__(cls)

                            def __call__(self, *args, **kwargs):
                                return v

                            def __bool__(self):
                                return bool(v)
                            __nonzero__ = __bool__

                        return MockAttr(v)

        return v

    def _raise_if_error(self, v):
        is_type = self._is_type(v, Exception)
        if is_type == 1:
            raise v

        elif is_type == 2:
            raise v()

#         do_raise = False
#         try:
#             do_raise = isinstance(v, Exception)
# 
#         except TypeError:
#             pass
# 
#         else:
#             if do_raise:
#                 raise v
# 
#         try:
#             do_raise = issubclass(v, Exception)
# 
#         except TypeError:
#             pass
# 
#         else:
#             if do_raise:
#                 raise v()

    def _is_type(self, v, class_types):
        ret = 0
        try:
            if isinstance(v, class_types):
                ret = 1

        except TypeError:
            pass

        if ret == 0:
            try:
                if issubclass(v, class_types):
                    ret = 2

            except TypeError:
                pass

        return ret







