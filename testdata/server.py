# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
#from contextlib import contextmanager
from .compat import *

from .threading import Thread
from . import environ


class WebHandler(SimpleHTTPRequestHandler):

    def __init__(self, request, client_address, server):
        self.base_path = server.base_path
        SimpleHTTPRequestHandler.__init__(self, request, client_address, server)

    def translate_path(self, path):
        #path = super(WebHandler, self).translate_path(self, path) # >3.0
        path = SimpleHTTPRequestHandler.translate_path(self, path)
        relpath = os.path.relpath(path, os.getcwd())
        fullpath = os.path.join(self.base_path, relpath)
        return fullpath


class HTTPServer(BaseHTTPServer):
    def __init__(self, base_path, server_address, RequestHandlerClass):
        self.base_path = base_path
        BaseHTTPServer.__init__(self, server_address, RequestHandlerClass)

#         BaseHTTPServer.__init__(self, server_address, RequestHandlerClass, bind_and_activate=False)
#         self.allow_reuse_address = True
#         self.server_bind()
#         self.server_activate()

#     def server_bind(self):
#         import socket
#         self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#         self.socket.bind(self.server_address)

class Webserver(str):
    @property
    def started(self):
        try:
            ret = True if self.thread else False
        except AttributeError:
            ret = False
        return ret

    @property
    def directory(self):
        return self.path

    @property
    def path(self):
        return self.server.path

    def __new__(cls, base_path, hostname="", port=0):
        if not hostname: hostname = environ.HOSTNAME
        if not port: port = environ.HOSTPORT
        netloc = "http://{}:{}".format(hostname, port)
        server = HTTPServer(base_path, (hostname, port), WebHandler)
        instance = super(Webserver, cls).__new__(cls, netloc)
        instance.server = server
        instance.hostname = hostname
        instance.port = port
        return instance

#     def __init__(self, base_path, hostname="", port=0):
#         #base_path = testdata.create_files(files)
# 
#         if not hostname: hostname = environ.HOSTNAME
#         if not port: port = environ.HOSTPORT
#         self.hostname = "http://{}:{}".format(host, port)
# 
#         httpd = HTTPServer(base_path, ("", port), WebHandler)
#         self.httpd = httpd

#     @classmethod
#     @contextmanager
#     def create(cls, *args, **kwargs):
#         instance = cls(*args, **kwargs)
#         try:
#             yield instance()
# 
#         finally:
#             instance.stop()

#     @contextmanager
#     def __call__(self):
#         try:
#             self.start()
#             yield self
# 
#         finally:
#             self.stop()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        self.stop()

    def url(self, *parts):
        vs = [self]
        vs.extend(map(lambda p: p.strip("/"), parts))
        return "/".join(vs)

    def start(self):
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
        if self.started:
            self.server.shutdown()
            self.thread = None


