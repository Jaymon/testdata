# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
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
import inspect

from .compat import *
from . import environ
from .client import ModuleCommand, FileCommand


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
    def parent(self):
        """return the directory portion of a directory/dirname path"""
        ret = None
        bits = self.relbits
        bits.pop(-1)
        if len(bits) > 0:
            ret = Dirpath(os.sep.join(bits), self.basedir)

        return ret

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
    def name(self):
        """Return the dirname portion of a directory/dirname path"""
        parentname, name = os.path.split(self.path)
        return name

    @property
    def fileroot(self):
        """see name"""
        return self.name

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
        """Return itself, this is just for api compatibility with children classes"""
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
        """Remove this whole directory and all subdirectories and files in it"""
        shutil.rmtree(self.path)

    @classmethod
    def normalize(cls, relpath, basedir=""):
        '''normalize a path, accounting for things like windows dir seps'''
        if relpath and relpath[0] == '.':
            raise ValueError("you cannot start a path with ./ or ../")

        if not basedir:
            basedir = tempfile.mkdtemp(dir=environ.TEMPDIR)

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
        """iterate through all the files in this directory and subdirectories"""
        for basedir, directories, files in os.walk(self.path, topdown=True):
            for basename in files:
                path = os.path.join(basedir, basename)
                #yield Filepath(os.path.relpath(self.basedir, path), self.basedir)
                yield Filepath(path.replace(self.basedir, ""), self.basedir)

    def exists(self):
        """True if this directory actually exists"""
        return os.path.isdir(self.path)

    def child(self, *bits):
        """Return a child instance (Filepath or Dirpath) relative to this directory"""
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
        """similar to modpath but returns the actual module instead of Modulepath
        instance"""
        return self.modpath(module_path).module

    def modules(self):
        """iterate through all the modules under this directory"""
        for modpath in self.modpaths():
            yield modpath.module

    def modpath(self, module_path):
        """Return a module that is rooted in this directory"""
        return Modulepath(module_path, self.path)

    def modpaths(self):
        """Similar to modules, returns all the modules under this directory as
        Modulepath instances"""
        for module_info in pkgutil.iter_modules([self.directory]):
            bits = self.relbits + [module_info[1]]
            yield Modulepath(".".join(bits), self.basedir)

            if module_info[2]: # module is a package because index 2 is True
                submodules = Dirpath(os.sep.join(bits), self.basedir)
                for submodule in submodules.modpaths():
                    #subbits = [module_info[1]] + submodule.relbits
                    #yield Modulepath(u".".join(subbits), self.basedir)
                    yield submodule

    def __truediv__(self, other):
        """Synctactic sugar, allows self / "bit" to work"""
        return self.child(other)
    __div__ = __truediv__ # 2.x


class Filepath(Dirpath):
    '''
    create a file and return the full path to that file

    path -- string -- the path to the file
    contents() -- string -- the file contents
    basedir -- string -- the temp directory to use as the base
    relpath -- string -- the directory tree from basedir

    on instantiation this class will contain the full file path
    '''
    @property
    def parent(self):
        """return the directory portion of a directory/fileroot.ext path"""
        return self.directory

    @property
    def directory(self):
        """return the directory portion of a directory/fileroot.ext path"""
        return Dirpath(
            os.path.dirname(self.relpath),
            self.basedir
        )

    @property
    def name(self):
        """Return the fileroot.ext portion of a directory/fileroot.ext path"""
        return os.path.basename(self.path)

    @property
    def fileroot(self):
        """Return the fileroot portion of a directory/fileroot.ext path"""
        # https://stackoverflow.com/questions/2235173/
        # https://stackoverflow.com/a/2235762/5006
        name = self.name
        fileroot, ext = os.path.splitext(name)
        return fileroot

    @property
    def ext(self):
        """Return the ext portion of a directory/fileroot.ext path"""
        name = self.name
        fileroot, ext = os.path.splitext(name)
        return ext.lstrip(".")

    def __new__(cls, relpath, basedir=""):
        instance = super(Filepath, cls).__new__(cls, relpath, basedir)
        instance.encoding='UTF-8'
        return instance

    @classmethod
    def create_instance(cls, relpath, contents="", basedir=""):
        instance = cls(relpath, basedir)
        return instance.create(contents)

    def exists(self):
        """True if the file exists, False otherwise"""
        return os.path.isfile(self.path)

    def open(self, mode="r"):
        """open the file"""
        return codecs.open(self.path, encoding=self.encoding, mode=mode)

    def write(self, contents):
        """Unlike create, this will just write the contents into the file"""
        with self.open("w+") as f:
            f.truncate(0)
            ret = f.write(self.normalize_contents(contents))
        return ret

    def create(self, contents=""):
        """This will create not only the file, but the directory also and place
        contents into the file

        :param contents: string, what you want the file to contain
        """
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

    def clear(self):
        """get rid of the contents from the file but leave the file"""
        self.write("")

    def delete(self):
        """remove the file"""
        os.unlink(self.path)

    def contents(self):
        """Return the body of the file"""
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

    def run(self, arg_str="", **kwargs):
        """Treat this file like a script and execute it

        :param arg_str: string, flags you want to pass into the execution of the script
        :returns: string, the output of running the file/script
        """
        cmd = FileCommand(self)
        return cmd.run(arg_str, **kwargs)


class Modulepath(Filepath):
    '''
    create a python module folder structure so that the module can be imported

    module_name -- string -- something like foo.bar
    contents -- string -- the contents of the module
    tmpdir -- string -- the temp directory that will be added to the syspath if make_importable is True
    make_importable -- boolean -- if True, then tmpdir will be added to the python path so it can be imported
    '''
    @property
    def parent(self):
        """If self was foo.bar.che this would return foo.bar"""
        ret = None
        bits = self.relbits
        bits.pop(-1)
        if len(bits) > 0:
            ret = type(self)(".".join(bits), self.basedir)
        return ret

    @property
    def directory(self):
        """Return the directory this module lives in"""
        f = Filepath(self.relpath, self.basedir)
        return f.directory

    @property
    def module(self):
        """Return the actual module this Modulepath represents"""
        injected = False
        if self.basedir not in sys.path:
            injected = True
            sys.path.insert(0, self.basedir) 

        module = importlib.import_module(self)

        if injected:
            sys.path.pop(0) 

        return module

    @property
    def classes(self):
        """Return all the classes this module contains"""
        m = self.module
        for m in self.modules():
            for klass_name, klass in inspect.getmembers(m, inspect.isclass):
                yield klass

    @property
    def fileroot(self):
        """see name"""
        return self.name

    @property
    def name(self):
        """Return the name of the module"""
        return self.relbits.pop(-1)

    @property
    def relbits(self):
        """If this module was foo.bar this would return ["foo", "bar"]"""
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
        """returns True if this module is a package (directory with __init__.py file
        in it)"""
        return self.relpath.endswith("__init__.py")

    def run(self, arg_str="", **kwargs):
        """Run this module on the command line

        :param arg_str: string, flags you want to pass into the execution of this module
        :returns: string, the output of running the file/script
        """
        mod = self
        if self.endswith("__main__") or self.endswith("__init__"):
            mod = self.parent
        cmd = ModuleCommand(mod, cwd=mod.basedir)
        return cmd.run(arg_str, **kwargs)

