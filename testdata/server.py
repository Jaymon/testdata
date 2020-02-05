# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import json
import logging
from wsgiref.simple_server import WSGIServer as WSGIHTTPServer, WSGIRequestHandler
import runpy

from .compat import *
from .threading import Thread
from . import environ


logger = logging.getLogger(__name__)


class PathHandler(SimpleHTTPRequestHandler):
    """Overrides built-in handler to allow setting of the base path instead of
    always using os.getcwd()

    https://github.com/python/cpython/blob/2.7/Lib/BaseHTTPServer.py#L114


    the parent classes:
        https://github.com/python/cpython/blob/2.7/Lib/SimpleHTTPServer.py
        https://github.com/python/cpython/blob/2.7/Lib/BaseHTTPServer.py
        https://github.com/python/cpython/blob/2.7/Lib/SocketServer.py
    """
    def translate_path(self, path):
        path = SimpleHTTPRequestHandler.translate_path(self, path)
        relpath = os.path.relpath(path, os.getcwd())
        fullpath = os.path.join(self.server.base_path, relpath)
        return fullpath

    def send_header(self, keyword, value):
        if keyword.lower() == "content-type":
            value += "; charset={}".format(self.server.encoding)

        SimpleHTTPRequestHandler.send_header(self, keyword, value)


class AnyHandler(PathHandler):
    def send_head(self):
        self.send_response(204)
        self.end_headers()


class CallbackHandler(AnyHandler):
    @property
    def uri(self):
        uri = self.path
        if "?" in uri:
            uri = uri[:uri.find("?")]
        return uri

    @property
    def query(self):
        _query = getattr(self, "_query", None)
        if _query is None:
            _query = ""
            if "?" in self.path:
                _query = self.path[self.path.find("?")+1:]
                _query = self.parse_querystr(_query)
            self._query = _query
        return _query

    @property
    def body(self):
        _body = getattr(self, "_body", None)
        if _body is None:
            content_len = int(self.headers.get('content-length', 0))
            _body = self.rfile.read(content_len)

            if _body:
                ct = self.headers.get("content-type", "")
                if ct:
                    ct = ct.lower()
                    if ct.rfind("json") >= 0:
                        _body = json.loads(body)

                    else:
                        _body = self.parse_querystr(_body)

            self._body = _body
        return _body

    def parse_querystr(self, s):
        d = {}
        for k, kv in urlparse.parse_qs(s, True, strict_parsing=True).items():
            if len(kv) > 1:
                d[k] = kv
            else:
                d[k] = kv[0]
        return d

    def do_HEAD(self):
        return self.do()

    def do_GET(self):
        return self.do()

    def do(self):
        ret = None
        self.headers_sent = False

        # log request headers
        for h, v in self.headers.items():
            self.log_message("req - %s: %s", h, v)

        try:
            callbacks = getattr(self.server, "callbacks", {})
            if callbacks:
                try:
                    ret = callbacks[self.command](self)
                except KeyError:
                    if not self.headers_sent:
                        self.send_error(501, "Unsupported method {}".format(self.command))
                    return

            else:
                ret = self.server.callback(self)

        except Exception as e:
            logger.exception(e)
            if not self.headers_sent:
                self.send_error(500, "{} - {}".format(e.__class__.__name__, e))

        else:
            if ret is None or ret == "" or ret == 0:
                if not self.headers_sent:
                    self.send_response(204)
                    self.end_headers()

            else:
                if not self.headers_sent:
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                b = json.dumps(ret)
                if is_py2:
                    self.wfile.write(b)
                else:
                    self.wfile.write(bytes(b, self.server.encoding))

    def __getattr__(self, k):
        if k.startswith("do_"):
            return self.do
        else:
            raise AttributeError(k)

    def end_headers(self):
        self.headers_sent = True
        return AnyHandler.end_headers(self)

    def send_header(self, keyword, value):
        self.log_message("res - %s: %s", keyword, value)
        return AnyHandler.send_header(self, keyword, value)


class Server(String):
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

    def __new__(cls, hostname, port, handler_cls, server_cls, encoding=""):
        if not hostname: hostname = environ.HOSTNAME
        if port is None: port = environ.HOSTPORT
        if not encoding: encoding = environ.ENCODING

        server = server_cls((hostname, port), handler_cls)
        server.encoding = encoding
        netloc = "http://{}:{}".format(hostname, server.server_port)
        instance = super(Server, cls).__new__(cls, netloc)
        instance.encoding = encoding
        instance.server = server
        instance.hostname = hostname
        instance.port = server.server_port
        return instance

    def __del__(self):
        self.server.server_close()

    def __enter__(self):
        """Allows webserver to be used with "with" keyword"""
        self.start()
        return self

    def __exit__(self, esc_type, esc_val, traceback):
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

        #from threading import Thread
        th = Thread(target=target)
        th.daemon = True
        th.start()
        self.thread = th

    def stop(self):
        """stop the webserver"""
        if self.started:
            self.server.shutdown()
            self.thread = None


class AnyServer(Server):
    def __new__(cls, hostname="", port=None, handler_cls=AnyHandler,
                server_cls=HTTPServer, *args, **kwargs):
        return super(AnyServer, cls).__new__(
            cls,
            hostname,
            port,
            handler_cls,
            server_cls,
            *args,
            **kwargs
        )


class CallbackServer(AnyServer):
    def __new__(cls, callbacks, hostname="", port=None, handler_cls=CallbackHandler,
                server_cls=HTTPServer, *args, **kwargs):
        instance = super(CallbackServer, cls).__new__(
            cls,
            hostname,
            port,
            handler_cls,
            server_cls,
            *args,
            **kwargs
        )

        if isinstance(callbacks, Mapping):
            instance.server.callbacks = callbacks
        else:
            instance.server.callback = callbacks

        return instance


class CookieServer(CallbackServer):
    """This will write and read cookies to make sure a client is passing cookies
    correctly to the server

    https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie
    """
    @classmethod
    def make_morsels(cls, handler):
        ret = []
        for name, val in handler.server.cookies:
            c = SimpleCookie()
            if is_py2:
                if isinstance(val, Mapping):
                    # TODO: this isn't right :(
                    c[bytes(name)] = val
                else:
                    # NOTE -- cookies can't really have unicode values
                    if isinstance(val, basestring):
                        val = val.encode("utf-8")
                    else:
                        val = bytes(val)
                    c[name.encode("utf-8")] = val

            else:
                if isinstance(val, Mapping):
                    # TODO: this isn't right :(
                    c[name] = val
                else:
                    c[str(name)] = str(val)

            ret.extend(c.values())
        return ret

    @classmethod
    def get_morsel_dict(cls, morsel):
        """converts the morsel class into a dict"""
        ret = {}
        ret = dict(morsel)
        ret["value"] = morsel.value
        ret["name"] = morsel.key
        return ret

    @classmethod
    def callback(cls, handler):
        ret = None
        req_cookies = handler.headers.get("cookie", "")
        if req_cookies:
            ret = {}
            read_cookies = {}
            unread_cookies = {}

            server_morsels = set(m.OutputString() for m in cls.make_morsels(handler))
            total_server_morsels = len(server_morsels)
            if is_py2:
                req_c = SimpleCookie(b"\r\n".join(req_cookies.split(b", ")))
            else:
                req_c = SimpleCookie("\r\n".join(req_cookies.split(", ")))
            for req_morsel in req_c.values():
                req_s = req_morsel.OutputString()
                morsel_d = cls.get_morsel_dict(req_morsel)
                if req_s in server_morsels:
                    read_cookies[req_morsel.key] = morsel_d
                else:
                    unread_cookies[req_morsel.key] = morsel_d

                server_morsels.discard(req_s)

            # How many passed up cookies from client were found?
            ret["read_count"] = total_server_morsels - len(server_morsels)
            ret["read_cookies"] = read_cookies
            ret["unread_cookies"] = unread_cookies

        else:
            # Turns out Chrome won't set a cookie on a 204, this might be a thing
            # in the spec, but just to be safe we will send information down
            handler.send_response(200)
            count = 0
            sent_cookies = {}
            for morsel in cls.make_morsels(handler):
                handler.send_header("Set-Cookie", morsel.OutputString())
                sent_cookies[morsel.key] = cls.get_morsel_dict(morsel)
                count += 1
            handler.end_headers()
            ret = {"sent_count": count, "sent_cookies": sent_cookies}

        return ret

    def __new__(cls, cookies, hostname="", port=None, handler_cls=CallbackHandler,
                server_cls=HTTPServer, *args, **kwargs):
        instance = super(CookieServer, cls).__new__(
            cls,
            cls.callback,
            hostname,
            port,
            handler_cls,
            server_cls,
            *args,
            **kwargs
        )

        # we store cookies as (name, val) tuples because you could have cookies
        # with the same name but different paths and things like that so we want
        # to support that, but since most people don't need that dicts are fine
        # to pass in also with name: val
        if isinstance(cookies, Mapping):
            instance.server.cookies = cookies.items()
        else:
            instance.server.cookies = cookies
        return instance


class PathServer(Server):
    @property
    def path(self):
        """returns the base path the server is serving from"""
        return self.server.base_path
    directory = path
    base_path = path

    def __new__(cls, base_path, hostname="", port=None, handler_cls=PathHandler,
                server_cls=HTTPServer, *args, **kwargs):
        instance = super(PathServer, cls).__new__(
            cls,
            hostname,
            port,
            handler_cls,
            server_cls,
            *args,
            **kwargs
        )
        instance.server.base_path = base_path
        return instance


class WSGIServer(Server):
    """Starts a wsgi server using a wsgifile, the wsgifile is a python file that
    has an application property"""
    def __new__(cls, wsgifile, hostname="", port=None, handler_cls=WSGIRequestHandler,
                server_cls=WSGIHTTPServer, *args, **kwargs):
        instance = super(WSGIServer, cls).__new__(
            cls,
            hostname=hostname,
            port=port,
            handler_cls=handler_cls,
            server_cls=server_cls,
            *args,
            **kwargs
        )

        config = runpy.run_path(wsgifile)
        instance.server.set_app(config["application"])
        instance.config = config
        instance.wsgifile = wsgifile
        return instance

