# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import subprocess
import sys
from collections import deque
import base64
import socket
import re
import json
import email.message
import signal
import time
import logging

from .compat import *
from . import environ
from .utils import String
from .threading import Thread, Deque


logger = logging.getLogger(__name__)


class Command(object):
    """makes running a command from a non CLI environment easy peasy

    This is handy when you need to test some CLI functionality of your python
    modules.

    c = Command("echo")
    r = c.run("hello")
    print(r) # hello
    """

    quiet = False
    """this is the default quiet setting for running a script, it can be overriden in run()"""

    bufsize = 1000
    """how many lines to buffer of output, set to 0 to suppress all output"""

    thread_class = Thread
    """the threading class to use if run_async() is called instead of run()"""

    @property
    def returncode(self):
        return self.process.returncode

    @property
    def cmd(self):
        return self.process.cmd

    @property
    def buf(self):
        return self.process.deque

    @property
    def environ(self):
        environ = getattr(self, "_environ", None)
        if not environ:
            environ = dict(os.environ)

        pythonpath = self.cwd
        if "PYTHONPATH" in environ:
            environ["PYTHONPATH"] += os.pathsep + pythonpath
        else:
            environ["PYTHONPATH"] = pythonpath

        if os.getcwd() not in environ["PYTHONPATH"]:
            environ["PYTHONPATH"] += os.pathsep + os.getcwd()

        # make sure each value is a string
        for k in environ.keys():
            if not isinstance(environ[k], basestring):
                environ[k] = String(environ[k])

        self._environ = environ
        return environ

    @environ.setter
    def environ(self, v):
        self._environ = v

    @environ.deleter
    def environ(self):
        del self._environ

    def __init__(self, command, cwd="", environ=None, **kwargs):
        self.cwd = os.path.realpath(cwd) if cwd else os.getcwd()
        self.command = command
        if environ:
            self.environ.update(environ)

        self.logger_prefix = kwargs.pop("logger_prefix", None)
        logger = logging.getLogger("{}.Client".format(__name__))
        if len(logger.handlers) == 0:
            logger.setLevel(logging.INFO)
            log_handler = logging.StreamHandler(stream=sys.stdout)
            log_handler.setFormatter(logging.Formatter('%(message)s'))
            logger.addHandler(log_handler)
            logger.propagate = False
        self.logger = logger

        self.sudo = kwargs.pop("sudo", False)

    def flush(self, line):
        """flush the line to stdout"""
        if self.logger_prefix is None:
            self.logger_prefix = "{:0>5}: ".format(self.process.pid)

        #self.logger.info("{:0>5}: {}".format(self.process.pid, line.rstrip()))
        self.logger.info("{}{}".format(self.logger_prefix, line.rstrip()))
        #sys.stdout.write(line)
        #sys.stdout.flush()

    def is_running(self):
        return self.process.poll() is None

    def create_cmd(self, command, arg_str):
        if command:
            if isinstance(command, basestring):
                cmd = command
                if arg_str:
                    if isinstance(arg_str, basestring):
                        cmd += " " + arg_str
                    else:
                        cmd += " ".join(arg_str)

            else:
                cmd = list(command)
                if arg_str:
                    if isinstance(arg_str, basestring):
                        cmd.append(arg_str)
                    else:
                        cmd.extend(arg_str)

        else:
            cmd = arg_str

        if self.sudo:
            if isinstance(cmd, basestring):
                if not cmd.startswith("sudo"):
                    cmd = "sudo " + cmd

            else:
                if not cmd[0] == "sudo":
                    cmd.insert(0, "sudo")

        return cmd

    def create_process(self, arg_str, **kwargs):
        """
        https://docs.python.org/3/library/subprocess.html
        """
        process = None
        cmd = self.create_cmd(self.command, arg_str)

        options = {}
        options["quiet"] = quiet = kwargs.pop("quiet", self.quiet)
        options["expected_returncode"] = 0
        for k in ["code", "ret_code", "returncode", "expected_ret_code", "expected_returncode"]:
            if k in kwargs:
                options["expected_returncode"] = kwargs.pop(k)
                break

        # any kwargs with all capital letters should be considered environment
        # variables
        environ = self.environ
        for k in list(kwargs.keys()):
            if k.isupper():
                environ[k] = kwargs.pop(k)

        # we will allow overriding of these values
        kwargs.setdefault("stderr", subprocess.STDOUT)

        # we will not allow these to be overridden via kwargs
        kwargs["shell"] = isinstance(cmd, basestring)
        kwargs["stdout"] = subprocess.PIPE
        kwargs["cwd"] = self.cwd
        kwargs["env"] = environ

        try:
            process = subprocess.Popen(
                cmd,
                **kwargs
            )

        except subprocess.CalledProcessError as e:
            process.returncode = e.returncode

        finally:
            if process:
                process.options = options
                process.cmd = cmd
                process.deque = Deque(maxlen=self.bufsize)

        self.process = process
        return process

    def __iter__(self):
        process = self.process
        try:
            # another round of links
            # http://stackoverflow.com/a/17413045/5006 (what I used)
            # http://stackoverflow.com/questions/2715847/
            for line in iter(process.stdout.readline, b""):
                line = line.decode("utf-8")
                process.deque.append(line.rstrip())
                if not process.options.get("quiet", False):
                    self.flush(line)
                yield line

        finally:
            if process:
                process.stdout.close()

    def quit(self, timeout=1):
        """same as .terminate but uses signals"""
        return self.finish("send_signal", timeout=timeout, args=(signal.SIGTERM,))
        #self.process.send_signal(signal.SIGTERM)
        #return self.wait(timeout)

    def kill(self, timeout=1):
        """kill -9 the script running asyncronously"""
        return self.finish("kill", timeout=timeout)
        #self.process.kill()
        #return self.wait(timeout)

    def terminate(self, timeout=1):
        """terminate the script running asyncronously"""
        return self.finish("terminate", timeout=timeout)
        #self.process.terminate()
        #return self.wait(timeout)

    def murder(self, timeout=1):
        cmd = self.create_cmd(["pkill", "-f", self.cmd], "")
        logger.debug("Murdering {}".format(self.cmd))
        if is_py2:
            subprocess.call(cmd)
        else:
            subprocess.run(cmd, check=False)
        return self.wait(timeout)

    def finish(self, method, timeout=1, maxcount=5, args=None, kwargs=None):
        ret = ""

        args = args or ()
        kwargs = kwargs or {}

        while self.is_running():
            getattr(self.process, method)(*args, **kwargs)
            ret = self.wait(timeout=timeout)
            if ret.returncode is None:
                count += 1
                if count >= maxcount:
                    ret = self.murder()

        return ret

    def wait(self, timeout=None):
        ret = ""
        if is_py2:
            if timeout:
                start = time.time()
                stop = start
                while self.is_running() and stop - start < timeout:
                    time.sleep(0.1)
                    stop = time.time()

            else:
                self.process.wait()

            ret = String("\n".join(self.buf))

        else:
            try:
                self.process.wait(timeout=timeout)

            except subprocess.TimeoutExpired:
                pass

            else:
                ret = String("\n".join(self.buf))


        ret.returncode = self.returncode
        return ret
    join = wait

    def run_async(self, arg_str="", **kwargs):
        self.process = self.create_process(arg_str, **kwargs)

        def target():
            for line in self:
                pass

        t = self.thread_class(target=target)
        t.daemon = True
        t.start()
        self.async_thread = t

    def run(self, arg_str="", **kwargs):
        """runs the passed in arguments

        :param arg_str: string, the argument flags that will be passed to the command
        :param **kwargs: These will be passed to subprocess or consumed
        :returns: string, the string of the output and will have .returncode attribute
        """
        process = self.create_process(arg_str, **kwargs)

        for line in self: # consume all the output from the program
            pass

        process.wait()

        expected_ret_code = process.options.get("expected_returncode", 0)
        if process.returncode != expected_ret_code:
            raise RuntimeError("{} returned {}, expected {}".format(
                self.process.cmd,
                process.returncode,
                expected_ret_code
            ))

        # we wrap the output in a String so we can set returncode
        ret = String("\n".join(self.buf))
        ret.returncode = process.returncode
        return ret


class ModuleCommand(Command):
    """This sets the client up so you can just pass the module name and have everything
    just work

    :Example:
        #You can setup this command 2 ways

        # 1 - pass in the module name
        c = ModuleCommand("module_name")

        # 2 - have the parent set it
        class MyCommand(ModuleCommand):
            name = "module_name"
        c = MyCommand()
    """
    cmd_prefix = "{} -m".format(sys.executable)
    """this is what will be used to invoke captain from the command line when run()
    is called"""

    name = ""
    """This is the module name you want to run"""

    def __init__(self, name="", cwd="", environ=None):
        if name:
            self.name = name

        if not self.name:
            raise ValueError("No name specified")

        super(ModuleCommand, self).__init__(None, cwd=cwd, environ=environ)

    def create_cmd(self, command, arg_str):
        if isinstance(command, basestring):
            ret = "{} {} {}".format(self.cmd_prefix, self.name, command)

        else:
            ret = re.split(r"\s+", self.cmd_prefix)
            ret.append(self.name)
            if command:
                ret.extend(command)

        return super(ModuleCommand, self).create_cmd(ret, arg_str)


class FileCommand(ModuleCommand):
    """This will add the .py to a script so you don't have to

    an example might be best to understand how the command gets put together

    Let's say you wanted to run this path:

        /foo/bar/program.py

    You could configure this class like this:

        class ProgamCommand(FileCommand):
            script_prefix = "/foo/bar"
            name = "program"

    Then when you need to run program.py, you only need to do:

        p = ProgramCommand()
        p.run() # runs "python /foo/bar/program.py"

    But you also could run it:

        p = FileCommand("/foo/bar/program.py")

    or:
        class ProgamCommand(FileCommand):
            script_prefix = "/foo/bar"

        p = ProgramCommand("program")
    """
    cmd_prefix = sys.executable
    """If you have a space in the executable path that might be really bad"""

    script_prefix = ""
    """this will be prepended to the passed in script on initialization"""

    script_postfix = ".py"
    """this will be appended to the passed in script on initialization"""

    def __init__(self, fileroot="", cwd="", environ=None):
        if fileroot:
            self.name = fileroot

        if not self.name:
            raise ValueError("no name found")

        path = self.name
        if self.script_prefix and not fileroot.startswith(self.script_prefix):
            path = os.path.join(self.script_prefix.rstrip("/"), fileroot)

        if self.script_postfix and not path.endswith(self.script_postfix):
            path += self.script_postfix

        super(FileCommand, self).__init__(path, cwd=cwd, environ=environ)


class HTTPResponse(object):
    """This is the response object that is returned from an HTTP request, it tries
    its best to look like a requests response object so you can switch this out
    when you need a more full-featured solution
    """
    @property
    def encoding(self):
        encoding = environ.ENCODING
        if "content-type" in self.headers:
            em = email.message.Message()
            em.add_header("content-type", self.headers["content-type"])
            encoding = em.get_content_charset()
            # https://stackoverflow.com/questions/29761905/default-encoding-of-http-post-request-with-json-body
            if not encoding:
                if self.http.is_json(self.headers):
                    encoding = "UTF-8"
                else:
                    if self.headers["content-type"].startswith("text/"):
                        encoding = "ISO-8859-1"

        return encoding

    @property
    def cookies(self):
        # https://stackoverflow.com/questions/25387340/is-comma-a-valid-character-in-cookie-value
        # https://stackoverflow.com/questions/21522586/python-convert-set-cookies-response-to-array-of-cookies
        # https://gist.github.com/Ostrovski/c8d16ce16759eddf6664
        if "set-cookie" in self.headers:
            # for some reason SimpleCookie leaves commas in the value
            if is_py2:
                cookie_headers = self.headers.get("set-cookie", "")
                cookie_headers = cookie_headers.split(b", ")
                cs = SimpleCookie(b"\r\n".join(cookie_headers))
            else:
                cookie_headers = self.headers.get_all("set-cookie", "")
                cs = SimpleCookie("\r\n".join(cookie_headers))
            cookies = {cs[k].key:cs[k].value for k in cs}
        else:
            cookies = {}
        return cookies

    @property
    def content(self):
        return self.body

    @property
    def status_code(self):
        return self.code

    @property
    def body(self):
        if self.http.is_json(self.headers):
            body = self.json()
        else:
            body = self._body.decode(self.encoding)
#             if isinstance(self._body, basestring):
#                 body = self._body.decode(self.encoding)
#             else:
#                 body = self._body
        return body

    def __init__(self, code, body, headers, http, response):
        self.http = http
        self.response = response
        self.headers = headers
        self._body = body
        self.code = code

    def json(self):
        return json.loads(self._body)


class HTTP(object):
    """A Generic HTTP request client

    Because sometimes just for tests I don't want to install requests

    https://stackoverflow.com/questions/645312/what-is-the-quickest-way-to-http-get-in-python

    :Example:
        # make a simple get request
        c = HTTP("http://example.com")
        c.get("/foo/bar")

        # make a request with a cookie
        c = HTTP("http://example.com")
        c.get("/foo/bar", cookies={"foo": "1"})

        # make a request with a different method
        c = HTTP("http://example.com")
        c.fetch("PUT", "/foo/bar")

        # make a POST request
        c = HTTP("http://example.com")
        c.post("/foo/bar", {"foo": 1})

        # make a json POST request
        c = HTTP("http://example.com")
        c.post("/foo/bar", {"foo": 1}, json=True)
    """
    timeout = 10

    def __init__(self, base_url="", *args, **kwargs):
        self.base_url = base_url
        self.query = {}

        # these are the common headers that usually don't change all that much
        self.headers = {
            "X-Forwarded-For": "127.0.0.1",
            "User-Agent": "Testdata Client",
        }

        if kwargs.get("json", False):
            self.headers.update({
                "Content-Type": "application/json",
            })

        headers = kwargs.get("headers", {})
        if headers:
            self.headers.update(headers)

    def get(self, uri, query=None, **kwargs):
        """make a GET request"""
        return self.fetch('get', uri, query, **kwargs)

    def post(self, uri, body=None, **kwargs):
        """make a POST request"""
        return self.fetch('post', uri, kwargs.pop("query", None), body, **kwargs)

    def __getattr__(self, key):
        def callback(*args, **kwargs):
            return self.fetch(key, *args, **kwargs)
        return callback
        #return lambda *args, **kwargs: self.fetch(key, *args, **kwargs)

    def fetch(self, method, uri, query=None, body=None, **kwargs):
        """
        wrapper method that all the top level methods (get, post, etc.) use to actually
        make the request
        """
        if not query: query = {}
        fetch_url = self.get_fetch_url(uri, query)

        orig_timeout = socket.getdefaulttimeout()
        socket.setdefaulttimeout(self.timeout)

        fetch_kwargs = {}
        fetch_kwargs["headers"] = self.get_fetch_headers(
            method,
            kwargs.get("headers", {}),
            kwargs.get("cookies", {}),
        )

        if body:
            fetch_kwargs["data"] = self.get_fetch_body(fetch_kwargs["headers"], body)

        fetch_args = [fetch_url]
        req = self.get_fetch_request(method, fetch_args, fetch_kwargs)
        res = self.get_fetch_response(req)
        socket.setdefaulttimeout(orig_timeout)
        return res

    def get_fetch_request(self, method, args, kwargs):
        req = Request(*args, **kwargs)
        # https://stackoverflow.com/a/111988/5006
        req.get_method = lambda: method.upper()
        return req

    def get_fetch_response(self, req):
        """the goal of this method is to make the requests object more endpoints like
        res -- requests Response -- the native requests response instance, we manipulate
            it a bit to make it look a bit more like the internal endpoints.Response object
        """
        try:
            res = urlopen(req)
            ret = HTTPResponse(
                res.code,
                res.read(),
                res.headers,
                self,
                res
            )

        except HTTPError as e:
            ret = HTTPResponse(
                e.code,
                str(e),
                {},
                self,
                e
            )

        except URLError as e:
            ret = HTTPResponse(
                0,
                e.reason,
                {},
                self,
                e
            )

        return ret

    def get_fetch_query(self, query_str, query):

        all_query = getattr(self, "query", {})
        if not all_query: all_query = {}
        if query:
            all_query.update(query)

        if all_query:
            more_query_str = urlencode(all_query, doseq=True)
            if query_str:
                query_str += '&{}'.format(more_query_str)
            else:
                query_str = more_query_str

        return query_str

    def get_fetch_url(self, uri, query=None):
        if not isinstance(uri, basestring):
            # allow ["foo", "bar"] to be converted to "/foo/bar"
            uri = "/".join(uri)

        if re.match(r"^\S+://\S", uri):
            ret_url = uri

        else:
            base_url = self.base_url
            base_url = base_url.rstrip('/')

            uri = uri.lstrip('/')
            ret_url = "/".join([base_url, uri])

        query_str = ''
        if '?' in ret_url:
            i = ret_url.index('?')
            query_str = ret_url[i+1:]
            ret_url = ret_url[0:i]

        query_str = self.get_fetch_query(query_str, query)
        if query_str:
            ret_url = '{}?{}'.format(ret_url, query_str)

        return ret_url

    def get_fetch_headers(self, method, headers, cookies):
        """merge class headers with passed in headers
        :param method: string, (eg, GET or POST), this is passed in so you can customize
            headers based on the method that you are calling
        :param headers: dict, all the headers passed into the fetch method
        :returns: passed in headers merged with global class headers
        """
        all_headers = self.headers.copy()
        if headers:
            all_headers.update(headers)

        if cookies:
            cl = []
            for k, v in cookies.items():
                c = SimpleCookie()
                c[k] = v
                cl.append(c[k].OutputString())
            if cl:
                all_headers["Cookie"] =  ", ".join(cl)

        return all_headers

    def get_fetch_body(self, headers, body):
        if self.is_json(headers):
            ret = json.dumps(body)
        else:
            ret = urlencode(body, doseq=True)
        return ret if is_py2 else ret.encode(environ.ENCODING)

    def is_json(self, headers):
        """return true if content_type is a json content type"""
        ret = False
        ct = headers.get("Content-Type", headers.get("content-type", "")).lower()
        if ct:
            ret = ct.lower().rfind("json") >= 0
        return ret

    def basic_auth(self, username, password):
        '''
        add basic auth to this client
        link -- http://stackoverflow.com/questions/6068674/
        link -- https://docs.python.org/2/howto/urllib2.html#id6
        username -- string
        password -- string
        '''
        credentials = base64.b64encode('{}:{}'.format(username, password)).strip()
        auth_string = 'Basic {}'.format(credentials())
        self.headers['Authorization'] = auth_string

    def token_auth(self, access_token):
        """add bearer TOKEN auth to this client"""
        self.headers['Authorization'] = 'Bearer {}'.format(access_token)

    def remove_auth(self):
        self.headers.pop('Authorization', None)

