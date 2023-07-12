# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import

from datatypes import (
    HTTPClient as HTTP,
    Command,
    AsyncCommand,
    ModuleCommand,
    FileCommand,
)

from .compat import *
from .base import TestData


###############################################################################
# testdata functions
###############################################################################
class ClientData(TestData):
    def run_command(self, cmd, arg_str="", cwd="", environ=None, **kwargs):
        """Run a command on the command line

        :param cmd: mixed, the command you want to run
        :param arg_str: string, extra flags that will be appended to the cmd
        :param **kwargs: allows you to pass into underlying Command.run() method
        :returns: string, the output from the command
        """
        if isinstance(cmd, Command):
            ret = cmd.run(arg_str, cwd=cwd, environ=environ, **kwargs)

        elif hasattr(cmd, "run"):
            ret = cmd.run(arg_str, cwd=cwd, environ=environ, **kwargs)

        else:
            cmd = Command(cmd, cwd=cwd, environ=environ)
            ret = cmd.run(arg_str, **kwargs)

        return ret
    run_cmd = run_command
    run_cli = run_command

    def start_command(self, cmd, arg_str="", cwd="", environ=None, **kwargs):
        """Run a command on the command line asyncronously

        :param cmd: mixed, the command you want to run
        :param arg_str: string, extra flags that will be appended to the cmd
        :param **kwargs: allows you to pass into underlying Command.run() method
        :returns: Command
        """
        if isinstance(cmd, AsyncCommand):
            cmd.start(arg_str, cwd=cwd, environ=environ, **kwargs)

        else:
            cmd = AsyncCommand(cmd, cwd=cwd, environ=environ)
            cmd.start(arg_str, **kwargs)

        return cmd
    run_command_async = start_command
    run_cmd_async = run_command_async

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

