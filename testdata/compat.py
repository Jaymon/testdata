# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from datatypes.compat import *
from datatypes.compat import _thread
from datatypes.string import String, ByteString


if is_py2:
    from Cookie import SimpleCookie
    import imp

else:
    from http.cookies import SimpleCookie

