# -*- coding: utf-8 -*-
import logging
import re

from datatypes.url import Host, Url
from datatypes.server import (
    ServerThread,
    PathServer,
    CallbackServer,
)
from datatypes.utils import infer_type

from .compat import *
from .config import environ
from .base import TestData


logger = logging.getLogger(__name__)


###############################################################################
# Supporting classes and methods
###############################################################################

class Server(ServerThread):
    """This is the Webserver master class, it masquerades as a string whose
    value is the url scheme://hostname:port but adds helper methods to manage
    the webserver

    :Example:
        s = Server(PathServer("<SOME-PATH>"))
        with s:
            # make an http request to <SERVER-HOST>/foo/bar.txt
            requests.get(s.child("foo", "bar.txt"))
    """
    @classmethod
    def get_server_address(self, hostname, port):
        # DEPRECATED?
        if not hostname: hostname = environ.HOSTNAME
        if port is None: port = environ.HOSTPORT
        return Host(hostname, port)

    def url(self, *parts, **kwargs):
        """Use this method to get a full url for the file you want

        :example:
            s = WebServer("/some/path")
            print(s.url("foo.txt")) # http://localhost:PORT/foo.txt

        :param *parts: list, the path parts you will add to the scheme://netloc
        :returns: the full url scheme://netloc/parts
        """
        # DEPRECATED? this class extends Url so you can use all Url's helper
        # methods
        return self.child(*parts, **kwargs)


class CookieServer(CallbackServer):
    """This will write and read cookies to make sure a client is passing cookies
    correctly to the server

    :Example:
        c = CookieServer({
            "foo-cookie-name": "foo cookie value",
            "bar-cookie-name": "bar cookie value",
        })

    https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie
    """
    def make_morsels(self, handler):
        ret = []
        for name, val in handler.server.cookies:
            c = SimpleCookie()
            if isinstance(val, Mapping):
                # TODO: this isn't right :(
                c[name] = val

            else:
                c[str(name)] = str(val)

            ret.extend(c.values())
        return ret

    def get_morsel_dict(self, morsel):
        """converts the morsel class into a dict"""
        ret = {}
        ret = dict(morsel)
        ret["value"] = morsel.value
        ret["name"] = morsel.key
        return ret

    def ANY(self, handler):
        ret = None
        req_cookies = handler.headers.get("cookie", "")
        if req_cookies:
            ret = {}
            read_cookies = {}
            unread_cookies = {}

            server_morsels = set(
                m.OutputString() for m in self.make_morsels(handler)
            )
            total_server_morsels = len(server_morsels)
            req_c = SimpleCookie("\r\n".join(req_cookies.split(", ")))

            for req_morsel in req_c.values():
                req_s = req_morsel.OutputString()
                morsel_d = self.get_morsel_dict(req_morsel)
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
            # Turns out Chrome won't set a cookie on a 204, this might be a
            # thing in the spec, but just to be safe we will send information
            # down
            handler.send_response(200)
            count = 0
            sent_cookies = {}
            for morsel in self.make_morsels(handler):
                handler.send_header("Set-Cookie", morsel.OutputString())
                sent_cookies[morsel.key] = self.get_morsel_dict(morsel)
                count += 1
            handler.end_headers()
            ret = {"sent_count": count, "sent_cookies": sent_cookies}

        return ret

    def __init__(self, cookies, server_address=None, **kwargs):
        # we store cookies as (name, val) tuples because you could have cookies
        # with the same name but different paths and things like that so we want
        # to support that, but since most people don't need that dicts are fine
        # to pass in also with name: val
        if isinstance(cookies, Mapping):
            self.cookies = cookies.items()

        else:
            self.cookies = cookies

        super().__init__(server_address=server_address, **kwargs)


class TestDataServer(CallbackServer):
    """Create a testdata server that basically turns all TestData children
    methods into a json api

    The server will answer requests in the form of:

        <HOST>/<METHOD-NAME>/<ARGS>?<KWARGS>

    :Example:
        s = TestDataServer(("localhost", 4321)
        with s:
            testdata.fetch("http://localhost:4321/get_int/1/100")
    """
    @classmethod
    def run_method(cls, cb, *args, **kwargs):
        if callable(cb):
            cbr = cb(*args, **kwargs)

        else:
            cbr = cb

        if cbr is None:
            ret = None

        if isinstance(cbr, (basestring, float, int, bool)):
            ret = cbr

        elif isinstance(cbr, Mapping):
            ret = cbr

        elif isinstance(cbr, Sequence):
            ret = []
            for o in cbr:
                try:
                    ret.append(cls.get_object_json(o))

                except ValueError:
                    ret.append(o)

        elif isinstance(cbr, object):
            ret = cls.get_object_json(cbr)

        else:
            ret = cbr

        return ret

    @classmethod
    def get_object_json(cls, o):
        """If the testdata method that was ran returns an object then this will
        try and figure out how to turn that object into json

        DEPRECATED -- 2025-06-27, use TestData.get_jsonable_value instead

        :param o: object, the generic object whose json value couldn't be
            inferred
        :returns: dict
        """
        # https://stackoverflow.com/a/51055044
        if hasattr(o, "jsonable"):
            ret = o.jsonable()

        elif hasattr(o, "to_json"):
            ret = o.to_json()

        elif hasattr(o, "toJSON"):
            ret = o.toJSON()

        elif hasattr(o, "tojson"):
            ret = o.tojson()

        elif hasattr(o, "json"):
            ret = o.json()

        elif hasattr(o, "__json__"):
            ret = o.__json__()

        else:
            ret = String(o)

        return ret

    def get_method_call(self, handler):
        """From the path, query, and body figure out the method name and the
        arguments that will be passed to it

        :param handler: CallbackHandler, the handler that is handling the
            request
        :returns: tuple[str, list, dict]
        """
        kwargs = handler.query
        if body := handler.body:
            kwargs.update(body)
        kwargs = infer_type(kwargs)

        parts = Url(handler.path).parts
        if parts:
            method_name = parts[0]
            args = infer_type(parts[1:])

        else:
            handler.code = 404
            raise ValueError(
                "Path missing method name, should be /<METHOD-NAME>"
            )

        return method_name, args, kwargs

    def run_handler_method(self, handler):
        """Internal method to figure out and run the testdata method that was
        requested

        :param handler: CallbackHandler, the handler that is handling the
            request
        :returns: Any, it will return whatever the ran method returned
        """
        try:
            method_name, args, kwargs = self.get_method_call(handler)
            cb = TestData.__findattr__(method_name)

        except TypeError as e:
            handler.code = 404
            raise

        else:
            try:
                return self.run_method(cb, *args, **kwargs)

            except TypeError as e:
                handler.code = 405
                raise

    def GET(self, handler):
        """Answer GET requests"""
        return self.run_handler_method(handler)

    def POST(self, handler):
        """Answer POST requests"""
        return self.run_handler_method(handler)

    def __init__(self, server_address=None, **kwargs):
        super().__init__(server_address=server_address, **kwargs)


###############################################################################
# testdata functions
###############################################################################
class ServerData(TestData):
    def create_fileserver(
        self,
        file_dict,
        tmpdir="",
        hostname="",
        port=0,
        encoding=""
    ):
        """create a fileserver that can be used to test remote file retrieval

        :Example:
            c = testdata.create_fileserver({
                "foo.txt": "foo text body",
                "bar/che.txt": "che text body",
            })

        :param file_dict: dict|list|str, same as create_files
        :param tmpdir: str, same as create_files
        :param hostname: str, usually leave this alone and it will use localhost
        :param port: int, the port you want to use
        """
        if not isinstance(file_dict, Mapping):
            file_dict = {
                "index.html": file_dict
            }

        path = self.create_files(file_dict, tmpdir=tmpdir, encoding=encoding)
        return Server(
            PathServer(
                path,
                server_address=(hostname, port),
                encoding=encoding
            )
        )
    create_file_server = create_fileserver
    create_pathserver = create_fileserver
    create_path_server = create_fileserver
    get_fileserver = create_fileserver

    def create_cookieserver(self, cookies, hostname="", port=0):
        """create a fileserver that can be used to test remote file retrieval

        :Example:
            c = testdata.create_cookieserver({
                "foo-cookie-name": "foo cookie value",
                "bar-cookie-name": "bar cookie value",
            })

        :param cookies: a dict of name: val or a list ot tuples(name, val)
        :param hostname: str, usually leave this alone and it will use localhost
        :param port: int, the port you want to use
        """
        return Server(CookieServer(cookies, server_address=(hostname, port)))
    create_cookie_server = create_cookieserver
    get_cookieserver = create_cookieserver

    def create_callbackserver(self, cb_dict, hostname="", port=0):
        """Create a callback server

        :Example:
            def do_PUT(handler):
                return "PUT"

            c = testdata.create_callbackserver({
                "PUT": do_PUT,
            })

        https://github.com/Jaymon/testdata/issues/79

        :param cb_dict: dict, key is the http method and value is the callback,
            the callback should have a signature of (handler)
        :param hostname: str, usually leave this alone and it will use localhost
        :param port: int, the port you want to use
        """
        return Server(CallbackServer(cb_dict, server_address=(hostname, port)))
    create_callback_server = create_callbackserver
    create_cb_server = create_callbackserver
    create_cbserver = create_callbackserver
    get_callbackserver = create_callbackserver

    def serve(self, hostname="", port=0, server_class=TestDataServer):
        """A wrapper around the TestDataServer class's .server_forever method

        :param hostname: str, usually leave this alone and it will use localhost
        :param port: int, the port you want to use
        """
        s = None
        try:
            s = server_class(server_address=(hostname, port))

            #hostloc = ":".join(map(str, s.server_address))

            logger.info("Server is listening on {}".format(
                Host(*s.server_address).client()
            ))
            #logger.info("Listening on {}".format(hostloc))

            s.serve_forever()

        except KeyboardInterrupt:
                pass

        finally:
            if s:
                s.server_close()

