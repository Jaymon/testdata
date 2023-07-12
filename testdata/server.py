# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import logging

from datatypes.url import Host
from datatypes.server import (
    ServerThread,
    PathServer,
    CallbackServer,
)

from .compat import *
from .config import environ
from .base import TestData


logger = logging.getLogger(__name__)


###############################################################################
# Supporting classes and methods
###############################################################################

class Server(ServerThread):
    """This is the Webserver master class, it masquerades as a string whose value
    is the url scheme://hostname:port but adds helper methods to manage the webserver

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
        # DEPRECATED? this class extends Url so you can use all Url's helper methods
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

    def get_morsel_dict(self, morsel):
        """converts the morsel class into a dict"""
        ret = {}
        ret = dict(morsel)
        ret["value"] = morsel.value
        ret["name"] = morsel.key
        return ret

    def callback(self, handler):
        ret = None
        req_cookies = handler.headers.get("cookie", "")
        if req_cookies:
            ret = {}
            read_cookies = {}
            unread_cookies = {}

            server_morsels = set(m.OutputString() for m in self.make_morsels(handler))
            total_server_morsels = len(server_morsels)
            if is_py2:
                req_c = SimpleCookie(b"\r\n".join(req_cookies.split(b", ")))
            else:
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
            # Turns out Chrome won't set a cookie on a 204, this might be a thing
            # in the spec, but just to be safe we will send information down
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

    def __init__(self, cookies, *args, **kwargs):
        # we store cookies as (name, val) tuples because you could have cookies
        # with the same name but different paths and things like that so we want
        # to support that, but since most people don't need that dicts are fine
        # to pass in also with name: val
        if isinstance(cookies, Mapping):
            self.cookies = cookies.items()
        else:
            self.cookies = cookies

        super().__init__({"default": self.callback}, *args, **kwargs)


###############################################################################
# testdata functions
###############################################################################
class ServerData(TestData):
    def create_fileserver(self, file_dict, tmpdir="", hostname="", port=0, encoding=""):
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
        return Server(PathServer(path, server_address=(hostname, port), encoding=encoding))
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

        :param cb_dict: dict, key is the http method and value is the callback, the
            callback should have a signature of (handler)
        :param hostname: str, usually leave this alone and it will use localhost
        :param port: int, the port you want to use
        """
        return Server(CallbackServer(cb_dict, server_address=(hostname, port)))
    create_callback_server = create_callbackserver
    create_cb_server = create_callbackserver
    create_cbserver = create_callbackserver
    get_callbackserver = create_callbackserver

