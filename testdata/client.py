# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import subprocess
import sys
import re
import signal
import time
import logging

from datatypes import (
    HTTPClient as HTTP,
    Dict,
    make_list,
)

from .compat import *
from .threading import Thread, Deque
from .base import TestData


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

        kwargs = Dict(kwargs)

        retcode = kwargs.pops([
            "code",
            "ret_code",
            "returncode",
            "retcode",
            "expected_ret_code",
            "expected_returncode",
            "codes",
            "ret_codes",
            "returncodes",
            "retcodes",
            "expected_ret_codes",
            "expected_returncodes",
        ], 0)
        options["expected_returncodes"] = set(make_list(retcode))

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

        expected_retcodes = process.options["expected_returncodes"]
        if process.returncode not in expected_retcodes:
            raise RuntimeError("{} returned {}, expected {}".format(
                self.process.cmd,
                process.returncode,
                expected_retcodes
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
            script_postfix = ".py"
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

    script_postfix = ""
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


###############################################################################
# testdata functions
###############################################################################
class ClientData(TestData):
    def run(self, cmd, arg_str="", cwd="", environ=None, **kwargs):
        """Run a command on the command line

        :param cmd: mixed, the command you want to run
        :param arg_str: string, extra flags that will be appended to the cmd
        :param **kwargs: allows you to pass into underlying Command.run() method
        :returns: string, the output from the command
        """
        if hasattr(cmd, "run"):
            ret = cmd.run(arg_str, cwd=cwd, environ=environ, **kwargs)

        else:
            cmd = Command(cmd, cwd=cwd, environ=environ)
            ret = cmd.run(arg_str, **kwargs)

        return ret

    def fetch(self, url, body=None, query=None, **kwargs):
        """fetch a url

        :Example:
            # make a simple get request
            c = testdata.fetch("http://example.com/foo/bar")

            # make a request with a cookie
            c = testdata.fetch("http://example.com/foo/bar", cookies={"foo": "1"})

            # make a request with a different method
            c = testdata.fetch("http://example.com/foo/bar", method="PUT")

            # make a POST request
            c = testdata.fetch("http://example.com/foo/bar", {"foo": 1})

            # make a json POST request
            c = testdata.fetch("http://example.com/foo/bar", {"foo": 1}, json=True)

        :param url: string, the full url you want to request
        :param body: dict, the body you want to POST, pass None for GET request
        :param query: dict, if you want to attach query params with ?
        :param **kwargs: anything else you want to pass to the underlying HTTP object
            method -- string, things like HEAD, or PUT
            cookies -- dict, the cookies you want to pass to the server
        :returns: HTTPResponse, has .code, .body, and other properties and methods
        """
        c = HTTP(url, **kwargs)
        method = kwargs.pop("method", "")
        if method:
            ret = c.fetch(method, url, query, body, **kwargs)

        else:
            if body is None:
                ret = c.get(url, query, **kwargs)
            else:
                ret = c.post(url, body, query=query, **kwargs)

        return ret

