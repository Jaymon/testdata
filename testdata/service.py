# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import subprocess


# 9-20-2017 -- I'm still testing these with some projects trying to get
# the api right and so they aren't fully integrated yet
# 3-29-2018 - I've further integrated this with the testdata.start_service() and
# testdata.stop_service() methods


class Service(object):
    """base class for services"""

    sudo = True
    """If true then sudo should be added to the command"""

    ignore_failure = True
    """If True then failures when running the command will be ignored, failure is
    usually defined as an exit code >0"""

    @property
    def path(self):
        raise NotImplementedError()

    def __init__(self, name, ignore_failure=True):
        self.name = name
        self.ignore_failure = ignore_failure

    def format_cmd(self, action, **kwargs):
        raise NotImplementedError()

    def is_running(self):
        raise NotImplementedError()

    def exists(self):
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


class Upstart(Service):
    """Handle starting Upstart services"""
    @property
    def path(self):
        return "/etc/init/{}".format(self.name)

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

    def exists(self):
        return os.path.isfile(self.path)


class InitD(Service):
    """Handle starting init.d services"""
    @property
    def path(self):
        return "/etc/init.d/{}".format(self.name)

    def format_cmd(self, action, **kwargs):
        cmd = []
        if self.sudo:
            cmd.append("sudo")

        cmd.append(self.path)
        cmd.append(action)
        return cmd, kwargs

    def is_running(self):
        cmd, kwargs = self.format_cmd("status")
        ret = self.run(cmd, kwargs)
        return ret is None

    def exists(self):
        return os.path.isfile(self.path)

