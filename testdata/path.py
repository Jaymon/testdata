# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division
import os
import re
import tempfile
from distutils import dir_util
import codecs
import shutil
import sys
import pkgutil
import importlib
import stat

from .compat import *


class Dirpath(str):
    '''
    create a directory path using a tempdir as the root

    so, if you pass in "/foo/bar" that will be combined with a tempdir, so you end 
    up with the final path: /tmp/python/dir/foo/bar

    path -- string -- the temp dir path
    tmpdir -- string -- the temp directory to use as the base

    on instantiation this class will contain the full directory path
    '''
    relpath = ""

    basedir = ""

    @property
    def permissions(self):
        # https://stomp.colorado.edu/blog/blog/2010/10/22/on-python-stat-octal-and-file-system-permissions/
        mode = stat.S_IMODE(os.stat(self.path).st_mode)
        mode = oct(mode)
        return mode.replace("o", "")

    @permissions.setter
    def permissions(self, v):
        self.chmod(v)

    @property
    def path(self):
        """plain jane string for non traditional path children (like Module) to 
        be able to use most of the common functions with minimal override"""
        return str(self)

    @property
    def relbits(self):
        """returns the relative path bits, so foo/bar would return ["foo", "bar"]"""
        return self.relpath.split(os.sep)

    @property
    def directory(self):
        return self

    def __new__(cls, relpath="", basedir=""):
        basedir, relpath, path = cls.normalize(relpath, basedir)
        instance = super(Dirpath, cls).__new__(cls, path)
        instance.basedir = basedir
        if relpath: instance.relpath = relpath
        return instance

    @classmethod
    def create_instance(cls, relpath="", basedir=""):
        instance = cls(relpath, basedir)
        return instance.create()

    def create(self):
        oldmask = os.umask(0)
        dir_util.mkpath(self.path)
        os.umask(oldmask)
        return self

    def create_file(self, relpath, contents=""):
        """create the file with path relative to this directory with contents"""
        return Filepath.create_instance(relpath, contents, self)

    def delete(self):
        shutil.rmtree(self.path)

    @classmethod
    def normalize(cls, relpath, basedir=""):
        '''normalize a path, accounting for things like windows dir seps'''
        if relpath and relpath[0] == '.':
            raise ValueError("you cannot start a path with ./ or ../")

#         if isinstance(relpath, str):
#             relpath = relpath.decode("UTF-8")

        if not basedir: basedir = tempfile.mkdtemp()

        if relpath:
            relpath = os.path.normpath(relpath)
            # for some reason, os.path.split() wouldn't work with the windows slash (\)
            relpath = re.sub(r"[\\/]+", os.sep, relpath)
            relpath = relpath.lstrip(os.sep)
            path = os.path.join(basedir, relpath)

        else:
            path = basedir

        return basedir, relpath, path

    def __iter__(self):
        for f in self.files():
            yield f

    def chmod(self, permissions):
        if isinstance(permissions, int):
            permissions = "{0:04d}".format(permissions)

        try:
            permissions = int(permissions, 8)
        except TypeError:
            pass

        os.chmod(self.path, permissions)

    def files(self):
        for basedir, directories, files in os.walk(self.path, topdown=True):
            for basename in files:
                path = os.path.join(basedir, basename)
                #yield Filepath(os.path.relpath(self.basedir, path), self.basedir)
                yield Filepath(path.replace(self.basedir, ""), self.basedir)

    def exists(self):
        return os.path.isdir(self.path)

    def child(self, *bits):
        relpath = os.path.join(self.relpath, *bits)
        fullpath = os.path.join(self.basedir, relpath)
        if os.path.isfile(fullpath):
            ret = Filepath(relpath, self.basedir)
        else:
            ret = type(self)(relpath, self.basedir)

        return ret

    def parents(self):
        bits = self.relbits
        bits.pop(-1)
        ps = []

        while len(bits) > 0:
            ps.append(Dirpath(os.sep.join(bits), self.basedir))
            bits.pop(-1)

        return ps

    def module(self, module_path):
        return self.modpath(module_path).module

    def modpath(self, module_path):
        return Modulepath(module_path, self.path)

    def modules(self):
        for module_info in pkgutil.iter_modules([self.path]):
            bits = self.relbits + [module_info[1]]
            yield Modulepath(".".join(bits), self.basedir)

            if module_info[2]: # module is a package because index 2 is True
                submodules = Dirpath(os.sep.join(bits), self.basedir)
                for submodule in submodules.modules():
                    #subbits = [module_info[1]] + submodule.relbits
                    #yield Modulepath(u".".join(subbits), self.basedir)
                    yield submodule

    def __div__(self, other):
        # 2.x
        return self.__truediv__(other)

    def __truediv__(self, other):
        return self.child(other)


class Filepath(Dirpath):
    '''
    create a file and return the full path to that file

    path -- string -- the path to the file
    contents -- string -- the file contents
    tmpdir -- string -- the temp directory to use as the base

    on instantiation this class will contain the full file path
    '''
    @property
    def directory(self):
        return Dirpath(
            os.path.dirname(self.relpath),
            self.basedir
        )

    @property
    def name(self):
        return os.path.basename(self.path)

    def __new__(cls, relpath, basedir=""):
        instance = super(Filepath, cls).__new__(cls, relpath, basedir)
        instance.encoding='UTF-8'
        return instance

    @classmethod
    def create_instance(cls, relpath, contents="", basedir=""):
        instance = cls(relpath, basedir)
        return instance.create(contents)

    def exists(self):
        return os.path.isfile(self.path)

    def open(self, mode="r"):
        return codecs.open(self.path, encoding=self.encoding, mode=mode)

    def write(self, contents):
        with self.open("w+") as f:
            f.truncate(0)
            ret = f.write(self.normalize_contents(contents))
        return ret

    def create(self, contents=""):
        d = self.directory # just by doing this the directory will be created
        d.create()
        if contents:
            self.write(contents)

        else:
            if not self.exists():
                with self.open("a") as f:
                    os.utime(self.path, None)

        return self

    def lines(self):
        """this is different than python built-in lines() method in that it strips
        the line endings from the end of the string"""
        with self.open("r") as f:
            for line in f:
                yield line.rstrip()

    def lc(self):
        """return line count"""
        return len(list(self.lines()))

    def exists(self):
        return os.path.isfile(self.path)

    def clear(self):
        self.write("")

    def delete(self):
        os.unlink(self.path)

    def contents(self):
        with self.open("r") as f:
            return f.read()

    def __iter__(self):
        for line in self.lines():
            yield line

    def normalize_contents(self, contents):
        if not isinstance(contents, basestring):
            contents = "\n".join(contents)
        return contents

    def child(self, *bits):
        raise NotImplementedError()

    def files(self):
        raise NotImplementedError()


class Modulepath(Filepath):
    '''
    create a python module folder structure so that the module can be imported

    module_name -- string -- something like foo.bar
    contents -- string -- the contents of the module
    tmpdir -- string -- the temp directory that will be added to the syspath if make_importable is True
    make_importable -- boolean -- if True, then tmpdir will be added to the python path so it can be imported
    '''
    @property
    def directory(self):
        f = Filepath(self.relpath, self.basedir)
        return f.directory

    @property
    def module(self):
        injected = False
        if self.basedir not in sys.path:
            injected = True
            sys.path.insert(0, self.basedir) 

        module = importlib.import_module(self)

        if injected:
            sys.path.pop(0) 

        return module

    @property
    def name(self):
        return self.relbits.pop(-1)

    @property
    def relbits(self):
        return self.split('.')

    @property
    def relpath(self):
        relpath = ""
        bits = self.relbits
        basename = bits.pop(-1)
        filebits = bits + ["{}.py".format(basename)]
        module_f = Filepath(os.sep.join(filebits), self.basedir)
        if module_f.exists():
            relpath = str(module_f.relpath)

        else:
            filebits = bits + [basename, "__init__.py"]
            package_f = Filepath(os.sep.join(filebits), self.basedir)
            relpath = str(package_f.relpath if package_f.exists() else module_f.relpath)

        return relpath

    @property
    def path(self):
        return os.path.join(self.basedir, self.relpath)

    def __new__(cls, module_name, basedir=""):
        instance = super(Modulepath, cls).__new__(cls, module_name, basedir)
        return instance

    @classmethod
    def create_instance(cls, module_name, contents="", basedir="", make_importable=True, is_package=False):
        instance = cls(module_name, basedir)
        return instance.create(contents, make_importable, is_package)

    @classmethod
    def normalize(cls, module_name, basedir=""):
        '''normalize a path, accounting for things like windows dir seps'''
        mod_bits = list(filter(None, module_name.split('.')))
        relpath = os.sep.join(mod_bits)

        basedir, relpath, path = super(Modulepath, cls).normalize(relpath, basedir)
        return basedir, None, ".".join(mod_bits)

    def create(self, contents="", make_importable=True, is_package=False):
        module_file = ''
        mod_bits = self.relbits
        base_modname = mod_bits.pop()

        module_base_dir = Dirpath("", self.basedir)
        module_base_dir.create()

        base_dir = self.basedir
        for modname in mod_bits:
            # check to see if there is a file that already exists
            mod_file = Filepath("{}.py".format(modname), base_dir)

            # turn module.py into a package (module/__init__.py)
            base_dir = Dirpath(modname, base_dir)
            base_dir.create()
            if os.path.isfile(mod_file):
                os.rename(mod_file, os.path.join(base_dir, "__init__.py"))

            else:
                # only add a blank package sentinel file if one already doesn't exist
                if not os.path.isfile(os.path.join(base_dir, "__init__.py")):
                    module_file = Filepath("__init__.py", base_dir)
                    module_file.create()

        # the basename gets treated differently becayse it can be a file
        mod_dir = os.path.join(base_dir, base_modname)
        if os.path.isdir(mod_dir):
            module_file = Filepath("__init__.py", mod_dir)

        else:
            if is_package:
                base_dir = Dirpath(base_modname, base_dir)
                base_dir.create()
                module_file = Filepath("__init__.py", mod_dir)

            else:
                module_file = Filepath("{}.py".format(base_modname), base_dir)

        module_file.create(contents)

        # add the path to the top of the sys path so importing the new module will work
        if make_importable:
            sys.path.insert(0, self.basedir) 

        return self

    def is_package(self):
        """returns True if this moduel is a package (directory with __init__.py file
        in it)"""
        return self.relpath.endswith("__init__.py")

