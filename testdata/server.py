# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
from .compat import *

from .threading import Thread
from . import environ


class HTTPHandler(SimpleHTTPRequestHandler):
    """Overrides built-in handler to allow setting of the base path instead of
    always using os.getcwd()

    https://github.com/python/cpython/blob/2.7/Lib/BaseHTTPServer.py#L114
    """
    def translate_path(self, path):
        path = SimpleHTTPRequestHandler.translate_path(self, path)
        relpath = os.path.relpath(path, os.getcwd())
        fullpath = os.path.join(self.server.base_path, relpath)
        return fullpath


class HTTPServer(BaseHTTPServer):
    """This is only needed so that the base_path can be set and then retrieved
    in the handler

    http://2ality.com/2014/06/simple-http-server.html
    https://github.com/python/cpython/blob/2.7/Lib/SimpleHTTPServer.py
    https://github.com/python/cpython/blob/2.7/Lib/SocketServer.py
    """
    def __init__(self, base_path, server_address, RequestHandlerClass=HTTPHandler):
        self.base_path = base_path
        BaseHTTPServer.__init__(self, server_address, RequestHandlerClass)


class Webserver(str):
    """This is the Webserver master class, it masquerades as a string whose value
    is the url scheme://hostname:port but adds helper methods to manage the webserver
    """
    @property
    def started(self):
        """Returns True if the webserver has been started"""
        try:
            ret = True if self.thread else False
        except AttributeError:
            ret = False
        return ret

    @property
    def directory(self):
        """alias for self.path"""
        return self.path

    @property
    def path(self):
        """returns the base path the server is serving from"""
        return self.server.path

    def __new__(cls, base_path, hostname="", port=0):
        if not hostname: hostname = environ.HOSTNAME
        if not port: port = environ.HOSTPORT
        netloc = "http://{}:{}".format(hostname, port)
        server = HTTPServer(base_path, (hostname, port))
        instance = super(Webserver, cls).__new__(cls, netloc)
        instance.server = server
        instance.hostname = hostname
        instance.port = port
        return instance

    def __enter__(self):
        """Allows webserver to be used with "with" keyword"""
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        """Allows webserver to be used with "with" keyword"""
        self.stop()

    def url(self, *parts):
        """Use this method to get a full url for the file you want

        :example:
            s = WebServer("/some/path")
            print(s.url("foo.txt")) # http://localhost:PORT/foo.txt

        :param *parts: list, the path parts you will add to the scheme://netloc
        :returns: the full url scheme://netloc/parts
        """
        vs = [self]
        vs.extend(map(lambda p: p.strip("/"), parts))
        return "/".join(vs)

    def start(self):
        """Start the webserver"""
        if self.started: return
        server = self.server

        def target():
            try:
                server.serve_forever()
            except Exception as e:
                raise

        th = Thread(target=target)
        th.daemon = True
        th.start()
        self.thread = th

    def stop(self):
        """stop the webserver"""
        if self.started:
            self.server.shutdown()
            self.thread = None


