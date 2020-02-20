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
    from BaseHTTPServer import HTTPServer
    from Cookie import SimpleCookie
    import urlparse
    from urllib import urlencode
    from urllib2 import Request, urlopen, URLError, HTTPError
    from collections import Mapping, Sequence
    import imp


elif is_py3:
    basestring = (str, bytes)
    unicode = str
    long = int

    import queue
    import _thread
    from io import StringIO
    from http.server import HTTPServer, SimpleHTTPRequestHandler
    #from http import cookies
    from http.cookies import SimpleCookie
    from urllib import parse as urlparse
    from urllib.request import Request, urlopen
    from urllib.error import URLError, HTTPError
    from urllib.parse import urlencode
    from collections.abc import Mapping, Sequence
    import importlib

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


String = unicode if is_py2 else str
Bytes = str if is_py2 else unicode

