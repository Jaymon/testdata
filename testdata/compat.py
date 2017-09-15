# -*- coding: utf-8 -*-

import sys

# shamelessly ripped from https://github.com/kennethreitz/requests/blob/master/requests/compat.py
# Syntax sugar.
_ver = sys.version_info
is_py2 = (_ver[0] == 2)
is_py3 = (_ver[0] == 3)

if is_py2:
    basestring = basestring
    unicode = unicode
    range = xrange # range is now always an iterator

    import Queue as queue
    import thread as _thread
    try:
        from cStringIO import StringIO
    except ImportError:
        from StringIO import StringIO

    # shamelously ripped from six https://bitbucket.org/gutworth/six
    exec("""def reraise(tp, value, tb=None):
        try:
            raise tp, value, tb
        finally:
            tb = None
    """)

    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from BaseHTTPServer import HTTPServer as BaseHTTPServer

elif is_py3:
    basestring = (str, bytes)
    unicode = str

    import queue
    import _thread
    from io import StringIO
    from http.server import HTTPServer as BaseHTTPServer, SimpleHTTPRequestHandler

    # ripped from six https://bitbucket.org/gutworth/six
    def reraise(tp, value, tb=None):
        try:
            if value is None:
                value = tp()
            if value.__traceback__ is not tb:
                raise value.with_traceback(tb)
            raise value
        finally:
            value = None
            tb = None


