# -*- coding: utf-8 -*-

import sys

# shamelessly ripped from https://github.com/kennethreitz/requests/blob/master/requests/compat.py
# Syntax sugar.
_ver = sys.version_info
is_py2 = (_ver[0] == 2)
is_py3 = (_ver[0] == 3)

if is_py2:
    basestring = basestring
    range = xrange # range is now always an iterator

elif is_py3:
    basestring = (str, bytes)

