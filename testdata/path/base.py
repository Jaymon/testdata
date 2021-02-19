# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import re
import tempfile
from distutils import dir_util, file_util
import codecs
import shutil
import sys
import pkgutil
import importlib
import stat
import inspect
#import glob
import fnmatch
import hashlib
from collections import deque
import csv

from datatypes.path import (
    TempFilepath,
    TempDirpath,
    Dirpath as DPath,
    Filepath as FPath,
)
from datatypes.csv import CSV

from ..compat import *
from .. import environ
from ..client import ModuleCommand, FileCommand
from ..utils import ByteString, String


class Dirpath(TempDirpath):
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
        return Modulepath(module_path, dir=self.path)

    def modpaths(self):
        """Similar to modules, returns all the modules under this directory as
        Modulepath instances"""
        for module_info in pkgutil.iter_modules([self.path]):
            pout.v(module_info)
            bits = self.relbits + [module_info[1]]
            yield Modulepath(".".join(bits), self.basedir)

            if module_info[2]: # module is a package because index 2 is True
                submodules = Dirpath(os.sep.join(bits), self.basedir)
                for submodule in submodules.modpaths():
                    #subbits = [module_info[1]] + submodule.relbits
                    #yield Modulepath(u".".join(subbits), self.basedir)
                    yield submodule

    def __contains__(self, pattern):
        return self.has(pattern)


class Filepath(TempFilepath):
    def prepare_text(self, data):
        if not isinstance(data, basestring):
            data = "\n".join(data)
        return super(Filepath, self).prepare_text(data)

    def run(self, arg_str="", cwd="", environ=None, **kwargs):
        """Treat this file like a script and execute it

        :param arg_str: string, flags you want to pass into the execution of the script
        :returns: string, the output of running the file/script
        """
        cwd = cwd if cwd else self.basedir
        cmd = FileCommand(self, cwd=cwd, environ=environ)
        return cmd.run(arg_str, **kwargs)


class Modulepath(Filepath):
    '''
    create a python module folder structure so that the module can be imported

    module_name -- string -- something like foo.bar
    contents -- string -- the contents of the module
    tmpdir -- string -- the temp directory that will be added to the syspath if make_importable is True
    make_importable -- boolean -- if True, then tmpdir will be added to the python path so it can be imported
    '''
#     @property
#     def parent(self):
#         """If self was foo.bar.che this would return foo.bar"""
#         ret = None
#         bits = self.relbits
#         bits.pop(-1)
#         if len(bits) > 0:
#             ret = type(self)(".".join(bits), self.basedir)
#         return ret
# 
#     @property
#     def directory(self):
#         """Return the directory this module lives in"""
#         f = Filepath(self.relpath, self.basedir)
#         return f.directory

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

#     @property
#     def relparts(self):
#         """If this module was foo.bar this would return ["foo", "bar"]"""
#         return self.split('.')
# 

#     @property
#     def fileroot(self):
#         """see name"""
#         return self.name
# 
#     @property
#     def name(self):
#         """Return the name of the module"""
#         return self.relbits.pop(-1)
# 
#     @property
#     def relpath(self):
#         relpath = ""
#         bits = self.relbits
#         basename = bits.pop(-1)
#         filebits = bits + ["{}.py".format(basename)]
#         module_f = Filepath(os.sep.join(filebits), self.basedir)
#         if module_f.exists():
#             relpath = str(module_f.relpath)
# 
#         else:
#             filebits = bits + [basename, "__init__.py"]
#             package_f = Filepath(os.sep.join(filebits), self.basedir)
#             relpath = str(package_f.relpath if package_f.exists() else module_f.relpath)
# 
#         return relpath
# 
#     @property
#     def path(self):
#         return os.path.join(self.basedir, self.relpath)



    @classmethod
    def normparts(cls, *parts, **kwargs):
        ps = []
        for p in parts:
            ps.extend(filter(None, p.split(".")))
        parts = super(Modulepath, cls).normparts(*ps, **kwargs)
        return parts

    @classmethod
    def normpath(cls, *parts, **kwargs):
        parts = list(parts)
        basename = parts.pop(-1)
        is_package = kwargs.get("is_package", False)

        if is_package:
            parts.append(basename)
            parts.append("__init__.py")

        else:
            parts.append("{}.py".format(basename))

        path = super(Modulepath, cls).normpath(*parts, **kwargs)
        return path

    @classmethod
    def normvalue(cls, *parts, **kwargs):
        return ".".join(parts[1:])
        #return super(Modulepath, cls).normvalue(*parts, **kwargs)

    @classmethod
    def create_as(cls, instance, **kwargs):
        instance = super(Modulepath, cls).create_as(instance, **kwargs)

        # add the path to the top of the sys path so importing the new module will work
        make_importable = kwargs.pop("make_importable", True)
        if make_importable:
            sys.path.insert(0, instance.basedir) 

        return instance


#     @classmethod
#     def __new__(cls, *parts, **kwargs):
#         kwargs["touch"] = False
#         kwargs["create"] = False
#         kwargs.pop("data", None)
#         return super(Modulepath, cls).__new__(*parts, **kwargs)





#     def __new__2(cls, *parts, **kwargs):
#         parts = list(parts) if parts else cls.get_parts(**kwargs)
#         basename = parts.pop(-1)
#         module_base_dir = Dirpath(*parts)
#         is_package = kwargs.pop("is_package", False)
#         make_importable = kwargs.pop("make_importable", True)
# 
#         mod_parts = module_base_dir.relparts
#         base_dir = module_base_dir.basedir
#         for modname in mod_parts:
#             # check to see if there is a file that already exists
#             mod_file = Filepath(base_dir, "{}.py".format(modname), touch=False)
# 
#             # turn module.py into a package (module/__init__.py)
#             base_dir = Dirpath(base_dir, modname)
#             target = Filepath(base_dir, "__init__.py", touch=False)
#             if mod_file.isfile():
#                 mod_file.mv(target)
# 
#             else:
#                 # only add a blank package sentinel file if one already doesn't exist
#                 if not target.is_file():
#                     target.touch()
# 
#         # the basename gets treated differently becayse it can be a file
#         mod_dir = Dirpath(base_dir, basename, touch=False)
#         if mod_dir.isdir():
#             module_file = Filepath(mod_dir, "__init__.py")
# 
#         else:
#             if is_package:
#                 base_dir = Dirpath(base_dir, basename)
#                 module_file = Filepath(mod_dir, "__init__.py")
# 
#             else:
#                 module_file = Filepath(base_dir, "{}.py".format(basename))
# 
#         instance = super(Modulepath, cls).__new__(module_file, **kwargs)
# 
#         # add the path to the top of the sys path so importing the new module will work
#         if make_importable:
#             sys.path.insert(0, self.basedir) 
# 
#         return instance


    def modpaths(self):
        """Similar to modules, returns all the modules under this directory as
        Modulepath instances"""
        for module_info in pkgutil.iter_modules([self.directory]):
            bits = self.relparts + [module_info[1]]
            yield Modulepath(".".join(bits), dir=self.basedir)

            if module_info[2]: # module is a package because index 2 is True
                submodules = Dirpath(os.sep.join(bits), dir=self.basedir)
                for submodule in submodules.modpaths():
                    #subbits = [module_info[1]] + submodule.relbits
                    #yield Modulepath(u".".join(subbits), self.basedir)
                    yield submodule



    def prepare_text(self, data):
        self.touch()
        data, encoding, errors = super(Modulepath, self).prepare_text(data)
        add_encoding = not data.lstrip().startswith("# -*- coding: utf-8 -*-")
        if "from __future__ import " not in data:
            lines = [
                "from __future__ import (",
                "    unicode_literals,",
                "    division,",
                "    print_function,",
                "    absolute_import",
                ")",
                "",
            ]
            data = "\n".join(lines) + data

        if add_encoding:
            data = "# -*- coding: utf-8 -*-\n" + data.lstrip()

        if not data.endswith("\n"):
            data += "\n"

        return data, encoding, errors

    def touch(self, mode=0o666, exist_ok=True):
        super(Modulepath, self).touch(mode=mode, exist_ok=exist_ok)

        # we need to make sure every part/directory of the module path is a valid
        # python module with an __init__.py file

        mod_parts = filter(lambda p: not p.endswith(".py"), self.relparts)

        base_dir = self.basedir
        for modname in mod_parts:
            # check to see if there is a file that already exists
#             pout.b(modname)

            mod_file = FPath(base_dir, "{}.py".format(modname), touch=False)

            # turn module.py into a package (module/__init__.py)
            base_dir = DPath(base_dir, modname)
            target = FPath(base_dir, "__init__.py", touch=False)

#             pout.v(base_dir)
#             pout.v(mod_file)
#             pout.v(target)
#             continue

            if mod_file.isfile():
                mod_file.mv(target)

            else:
                target.touch()











#     @classmethod
#     def normalize(cls, module_name, basedir=""):
#         '''normalize a path, accounting for things like windows dir seps'''
#         mod_bits = list(filter(None, module_name.split('.')))
#         relpath = os.sep.join(mod_bits)
# 
#         basedir, relpath, path = super(Modulepath, cls).normalize(relpath, basedir)
#         return basedir, None, ".".join(mod_bits)
# 
#     def create(self, contents="", make_importable=True, is_package=False):
#         module_file = ''
#         mod_bits = self.relbits
#         base_modname = mod_bits.pop()
# 
#         module_base_dir = Dirpath("", self.basedir)
#         module_base_dir.create()
# 
#         base_dir = self.basedir
#         for modname in mod_bits:
#             # check to see if there is a file that already exists
#             mod_file = Filepath("{}.py".format(modname), base_dir)
# 
#             # turn module.py into a package (module/__init__.py)
#             base_dir = Dirpath(modname, base_dir)
#             base_dir.create()
#             if os.path.isfile(mod_file):
#                 os.rename(mod_file, os.path.join(base_dir, "__init__.py"))
# 
#             else:
#                 # only add a blank package sentinel file if one already doesn't exist
#                 if not os.path.isfile(os.path.join(base_dir, "__init__.py")):
#                     module_file = Filepath("__init__.py", base_dir)
#                     module_file.create()
# 
#         # the basename gets treated differently becayse it can be a file
#         mod_dir = os.path.join(base_dir, base_modname)
#         if os.path.isdir(mod_dir):
#             module_file = Filepath("__init__.py", mod_dir)
# 
#         else:
#             if is_package:
#                 base_dir = Dirpath(base_modname, base_dir)
#                 base_dir.create()
#                 module_file = Filepath("__init__.py", mod_dir)
# 
#             else:
#                 module_file = Filepath("{}.py".format(base_modname), base_dir)
# 
#         module_file.create(contents)
# 
#         # add the path to the top of the sys path so importing the new module will work
#         if make_importable:
#             sys.path.insert(0, self.basedir) 
# 
#         return self
# 
#     def normalize_contents(self, contents):
#         contents = super(Modulepath, self).normalize_contents(contents)
#         add_encoding = not contents.lstrip().startswith("# -*- coding: utf-8 -*-")
#         if "from __future__ import " not in contents:
#             lines = [
#                 "from __future__ import (",
#                 "    unicode_literals,",
#                 "    division,",
#                 "    print_function,",
#                 "    absolute_import",
#                 ")",
#                 "",
#             ]
#             contents = "\n".join(lines) + contents
# 
#         if add_encoding:
#             contents = "# -*- coding: utf-8 -*-\n" + contents.lstrip()
# 
#         if not contents.endswith("\n"):
#             contents += "\n"
# 
#         return contents

    def is_package(self):
        """returns True if this module is a package (directory with __init__.py file
        in it)"""
        return self.path.endswith("__init__.py")

    def run(self, arg_str="", cwd="", environ=None, **kwargs):
        """Run this module on the command line

        :param arg_str: string, flags you want to pass into the execution of this module
        :returns: string, the output of running the file/script
        """
        mod = self
        cwd = cwd if cwd else mod.basedir
        if self.endswith("__main__") or self.endswith("__init__"):
            mod = self.parent
        cmd = ModuleCommand(mod, cwd=cwd, environ=environ)
        return cmd.run(arg_str, **kwargs)


class ContentMixin(object):
    """Find the first file matching basedir/fileroot.* and read its contents"""
    @classmethod
    def _get_params(cls, fileroot, basedir="", encoding=""):
        path = cls._find_path(fileroot, basedir)
        if encoding:
            with codecs.open(path, encoding=encoding) as f:
                contents = f.read()

        else:
            with open(path) as f:
                contents = f.read()

        return contents, path

    @classmethod
    def _initialize(cls, instance, path):
        instance.path = Filepath(os.path.basename(path), basedir=os.path.dirname(path))
        instance.directory = instance.path.directory
        return instance

    @classmethod
    def _find_path(cls, fileroot, basedir):
        path = fileroot
        if not os.path.isfile(fileroot):
            d = cls._find_directory(basedir)
            path = os.path.join(d, fileroot)
            if not os.path.isfile(path):
                path = ""
                patterns = [fileroot, "{}.*".format(fileroot)]
                for root_dir, dirs, files in os.walk(d, topdown=True):
                    for basename in files:
                        for pattern in patterns:
                            if fnmatch.fnmatch(basename, pattern):
                                path = os.path.join(root_dir, basename)
                                break
                        if path: break
                    if path: break

                if not path:
                    raise IOError("Could not find a file matching {}".format(fileroot))

        return path

    @classmethod
    def _find_directory(cls, basedir):
        d = ""
        if basedir:
            d = basedir

        else:
            d = environ.CONTENTS_DIR

            if not d:
                d = os.getcwd()

        if not d:
            raise IOError("Could not find a testdata directory")
        return d


class ContentBytes(Bytes, ContentMixin):
    """This is returned when get_contents is called without an encoding"""
    def __new__(cls, fileroot, basedir=""):
        contents, path = cls._get_params(fileroot, basedir)
        instance = super(ContentBytes, cls).__new__(cls, contents)
        cls._initialize(instance, path)
        return instance


class ContentString(String, ContentMixin):
    """This is returned when get_contents is called with an encoding"""
    def __new__(cls, fileroot, basedir="", encoding=""):
        contents, path = cls._get_params(fileroot, basedir, encoding)
        instance = super(ContentString, cls).__new__(cls, contents)
        cls._initialize(instance, path)
        return instance


class ContentFilepath(Filepath, ContentMixin):
    """Return the filepath of a file in the contents directory"""
    def __new__(cls, fileroot, basedir="", encoding=""):
        path = cls._find_path(fileroot, basedir)
        return super(ContentFilepath, cls).__new__(cls, path, encoding=encoding)


