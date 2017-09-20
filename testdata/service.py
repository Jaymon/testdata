# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import subprocess


# NOTE -- 9-20-2017 -- I'm still testing these with some projects trying to get
# the api right and so they aren't fully integrated yet

class Service(object):
    """base class for services"""

    sudo = True
    """If true then sudo should be added to the command"""

    ignore_failure = True
    """If True then failures when running the command will be ignored, failure is
    usually defined as an exit code >0"""

    def __init__(self, name):
        self.name = name

    def format_cmd(self, action, **kwargs):
        raise NotImplementedError()

    def is_running(self):
        raise NotImplementedError()

    def start(self):
        cmd, kwargs = self.format_cmd("start")
        self.run(cmd, kwargs)

    def restart(self):
        self.stop()
        self.start()

    def stop(self):
        cmd, kwargs = self.format_cmd("stop")
        self.run(cmd, kwargs)

    def run(self, cmd, kwargs):
        try:
            ret = subprocess.check_output(cmd, **kwargs)

        except subprocess.CalledProcessError as e:
            if self.ignore_failure:
                ret = None
            else:
                raise

        return ret

#         if self.ignore_failure:
#             subprocess.call(cmd, **kwargs)
# 
#         else:
#             subprocess.check_call(cmd, **kwargs)


class Upstart(Service):
    """Handle starting Upstart services"""
    def format_cmd(self, action, **kwargs):
        cmd = []
        if self.sudo:
            cmd.append("sudo")

        cmd.append(action)
        cmd.append(self.name)

        #kwargs["stdout"] = subprocess.PIPE
        #kwargs["stderr"] = subprocess.STDOUT
        return cmd, kwargs

    def start(self):
        cmd, kwargs = self.format_cmd("start")
        self.run(cmd, kwargs)

    def restart(self):
        self.stop()
        self.start()

    def stop(self):
        cmd, kwargs = self.format_cmd("stop")
        self.run(cmd, kwargs)

    def is_running(self):
        cmd, kwargs = self.format_cmd("status")
        ret = self.run(cmd, kwargs)
        return "start/running" in ret


class InitD(Service):
    """Handle starting init.d services"""
    def format_cmd(self, action, **kwargs):
        cmd = []
        if self.sudo:
            cmd.append("sudo")

        cmd.append("/etc/init.d/{}".format(self.name))
        cmd.append(action)
        return cmd, kwargs

    def is_running(self):
        cmd, kwargs = self.format_cmd("status")
        ret = self.run(cmd, kwargs)
        return ret is None

