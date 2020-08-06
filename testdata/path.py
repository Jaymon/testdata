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


from .compat import *
from . import environ
from .client import ModuleCommand, FileCommand
from .utils import ByteString, String


class Dirpath(String):
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
    def basename(self):
        return self.name

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
        instance = cls.get_instance(relpath, basedir)
        return instance.create()

    @classmethod
    def get_instance(cls, relpath="", basedir=""):
        instance = cls(relpath, basedir)
        return instance

    def create(self):
        oldmask = os.umask(0)
        dir_util.mkpath(self.path)
        os.umask(oldmask)
        return self

    def create_file(self, relpath, contents="", encoding=""):
        """create the file with path relative to this directory with contents"""
        return Filepath.create_instance(relpath, contents, self, encoding=encoding)

    def get_file(self, relpath, encoding=""):
        return Filepath.get_instance(relpath, self, encoding=encoding)

    def create_files(self, file_dict, encoding=""):
        """
        create a whole bunch of files all at once

        file_dict -- dict -- keys are the filepath relative to tmpdir, values are the
            file contents
        """
        for file_name, contents in file_dict.items():
            self.create_file(file_name, contents, encoding)
        return self

    def create_dir(self, relpath):
        """create a child directory relative to this directory"""
        return self.get_dir(relpath).create()

    def get_dir(self, relpath):
        """get a child directory relative to this directory"""
        return self.child(relpath)

    def create_dirs(self, dirs):
        for name in dirs:
            self.create_dir(name)
        return self

    def delete(self):
        """Remove this whole directory and all subdirectories and files in it"""
        shutil.rmtree(self.path)

    def clear(self):
        """Remove all the contents of this directory but leave the directory"""
        for root_dir, dirs, files in os.walk(self.path, topdown=True):
            for basename in files:
                filepath = os.path.join(root_dir, basename)
                os.unlink(filepath)

            for basename in dirs:
                dirpath = os.path.join(root_dir, basename)
                shutil.rmtree(dirpath)

    @classmethod
    def normalize(cls, relpath, basedir=""):
        '''normalize a path, accounting for things like windows dir seps'''
        relpath = String(relpath) if relpath else ""
        basedir = String(basedir) if basedir else ""

        if relpath and not basedir and re.match(r"^[\.~\\/]|(?:[a-zA-Z]\:)", relpath) and os.path.exists(relpath):
        #if relpath and not basedir and re.match(r"^[\.~\\/]|(?:[a-zA-Z]\:)", relpath):
            path = os.path.abspath(os.path.expanduser(relpath))
            if os.path.isdir(path):
                basedir = path
                relpath = ""
            elif os.path.isfile(path):
                basedir = os.path.dirname(path)
                relpath = os.path.basename(path)

        else:
            if relpath and relpath[0] == '.':
                raise ValueError("You cannot start a path with ./ or ../")

            if basedir:
                basedir = os.path.abspath(os.path.expanduser(basedir))
            else:
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

    def chmod(self, permissions):
        if isinstance(permissions, int):
            permissions = "{0:04d}".format(permissions)

        try:
            permissions = int(permissions, 8)
        except TypeError:
            pass

        os.chmod(self.path, permissions)

    def directories(self):
        for basedir, directories, files in os.walk(self.path, topdown=True):
            for basename in directories:
                path = os.path.join(basedir, basename)
                yield type(self)(path.replace(self.basedir, ""), self.basedir)

    def files(self):
        """iterate through all the files in this directory and subdirectories"""
        for basedir, directories, files in os.walk(self.path, topdown=True):
            for basename in files:
                path = os.path.join(basedir, basename)
                #yield Filepath(os.path.relpath(self.basedir, path), self.basedir)
                yield Filepath(path.replace(self.basedir, ""), self.basedir)

    def contents(self):
        """iterate through all the *directories* and *files* in this directory and subdirectories"""
        for basedir, directories, files in os.walk(self.path, topdown=True):
            for basename in directories:
                path = os.path.join(basedir, basename)
                yield type(self)(path.replace(self.basedir, ""), self.basedir)

            for basename in files:
                path = os.path.join(basedir, basename)
                yield Filepath(path.replace(self.basedir, ""), self.basedir)

    def read(self):
        """identical to contents()

        in this form instead of read = contents so that you can override contents
        and this will inherit the overridden functionality
        """
        return self.contents()

    def exists(self):
        """True if this directory actually exists"""
        return os.path.isdir(self.path)

    def child(self, *bits):
        """Return a child instance (Filepath or Dirpath) relative to this directory"""
        relpath = os.path.join(self.relpath, *filter(None, bits))
        fullpath = os.path.join(self.basedir, relpath)
        if os.path.isfile(fullpath):
            ret = Filepath(relpath, self.basedir)
        else:
            # if path ends with a / or doesn't have a dot in it it is a dir,
            # otherwise it's a file
            if relpath.endswith("/") or not "." in relpath:
                ret = type(self)(relpath, self.basedir)
            else:
                ret = Filepath(relpath, self.basedir)

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

    def __iter__(self):
        for f in self.files():
            yield f

    def __contains__(self, relpath):
        v = self.child(relpath)
        return v.exists()

    def __truediv__(self, other):
        """Synctactic sugar, allows self / "bit" to work"""
        return self.child(other)
    __div__ = __truediv__ # 2.x

    def copy_into(self, source_path):
        """Copy the contents of source_path into self"""
        relpath = ""
        if os.path.isdir(source_path):
            if relpath:
                dest_path = self.create_dir(relpath)
            else:
                dest_path = self
            # https://stackoverflow.com/a/15034373/5006
            dir_util.copy_tree(source_path, dest_path, update=1)

        else:
            if not relpath:
                relpath = os.path.basename(source_path)
            dest_path = self.create_file(relpath)
            file_util.copy_file(source_path, dest_path)

    def put(self, source_path):
        """This method exists to make sure children pick up this method also, we
        can't do put = copy_into because then put will only point to self.copy_into
        instead of child's copy_into"""
        return self.copy_into(source_path)
    copy_from = put

    def copy_to(self, dest_path):
        """copy self to dest_path"""
        source_path = self
        # https://stackoverflow.com/a/15034373/5006
        dir_util.copy_tree(source_path, dest_path, update=1)

    def place(self, dest_path):
        """see note on self.put()"""
        return self.copy_to(dest_path)


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

    def __new__(cls, relpath, basedir="", encoding=""):
        instance = super(Filepath, cls).__new__(cls, relpath, basedir)
        # if encoding is None then it is assumed this will be a bytes file, if
        # encoding is an empty string then it will be default encoded
        if encoding is not None and not encoding:
            encoding = environ.ENCODING
        instance.encoding = encoding
        return instance

    @classmethod
    def create_instance(cls, relpath, contents="", basedir="", encoding=""):
        instance = cls.get_instance(relpath, basedir, encoding)
        instance.create(contents)
        return instance

    @classmethod
    def get_instance(cls, relpath, basedir="", encoding=""):
        """returns an instance but makes no guarrantees the file exists or its contents"""
        instance = cls(relpath, basedir, encoding)
        return instance

    def exists(self):
        """True if the file exists, False otherwise"""
        return os.path.isfile(self.path)

    def open(self, mode=""):
        """open the file"""
        if not mode:
            mode = "r" if self.encoding else "rb"

        if self.encoding:
            return codecs.open(self.path, encoding=self.encoding, mode=mode)

        else:
            return open(self.path, mode=mode)

    def write(self, contents):
        """Unlike create, this will just write the contents into the file"""
        return self.append(contents)

    def replacing(self):
        mode = "w+" if self.encoding else "wb+"
        return self.open(mode)

    def replace(self, contents):
        """replaces the current contents of file with contents"""
        #mode = "w+" if self.encoding else "wb+"
        with self.replacing() as f:
        #with self.open(mode) as f:
            ret = f.write(self.normalize_contents(contents))
        return ret

    def appending(self):
        mode = "a+" if self.encoding else "ab+"
        return self.open(mode)
    writing = appending

    def append(self, contents):
        """append the contents onto the end of the file"""
        #mode = "a+" if self.encoding else "ab+"
        with self.appending() as f:
        #with self.open(mode) as f:
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
            self.replace(contents)

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
    linecount = lc

    def head(self, count):
        """
        get the first count lines of self.path

        :param count: int, how many lines you want from the start of the file
        :returns: list, the lines in a similar format to .lines()
        """
        if count == 0:
            ret = self.lines()
        else:
            ret = [l[1] for l in enumerate(self.lines()) if l[0] < count]
        return ret

    def tail(self, count):
        """
        get the last count lines of self.path

        https://stackoverflow.com/a/280083/5006

        :param count: int, how many lines you want from the end of the file
        :returns: list, the lines in a similar format to .lines()
        """
        if count == 0:
            ret = self.lines()
        else:
            ret = deque(self.lines(), maxlen=count)
        return ret

    def clear(self):
        """get rid of the contents from the file but leave the file"""
        self.write("")

    def delete(self):
        """remove the file"""
        os.unlink(self.path)

    def checksum(self):
        """return md5 hash of a file"""
        h = hashlib.md5()
        # http://stackoverflow.com/a/21565932/5006
        with self.open() as fp:
            h.update(ByteString(fp.read()))
        return h.hexdigest()
    def hash(self): return self.checksum()

    def contents(self):
        """Return the body of the file"""
        with self.open() as f:
            return f.read()
    body = contents
    content = contents

    def __iter__(self):
        for line in self.lines():
            yield line

    def __contains__(self, s):
        contents = self.contents()
        return s in contents

    def normalize_contents(self, contents):
        if not isinstance(contents, basestring):
            contents = "\n".join(contents)
        return contents

    def run(self, arg_str="", cwd="", environ=None, **kwargs):
        """Treat this file like a script and execute it

        :param arg_str: string, flags you want to pass into the execution of the script
        :returns: string, the output of running the file/script
        """
        cwd = cwd if cwd else self.basedir
        cmd = FileCommand(self, cwd=cwd, environ=environ)
        return cmd.run(arg_str, **kwargs)

    def copy_into(self, source_path):
        shutil.copy(source_path, self.path)

    def copy_to(self, dest_path):
        r = shutil.copy(self.path, dest_path)

    def child(self, *args, **kwargs):
        raise NotImplementedError()
    files = child
    directories = child
    get_file = child
    get_dir = child
    create_file = child
    create_files = child
    create_dir = child
    create_dirs = child


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

    def normalize_contents(self, contents):
        contents = super(Modulepath, self).normalize_contents(contents)
        add_encoding = not contents.lstrip().startswith("# -*- coding: utf-8 -*-")
        if "from __future__ import " not in contents:
            lines = [
                "from __future__ import (",
                "    unicode_literals,",
                "    division,",
                "    print_function,",
                "    absolute_import",
                ")",
                "",
            ]
            contents = "\n".join(lines) + contents

        if add_encoding:
            contents = "# -*- coding: utf-8 -*-\n" + contents.lstrip()

        if not contents.endswith("\n"):
            contents += "\n"

        return contents

    def is_package(self):
        """returns True if this module is a package (directory with __init__.py file
        in it)"""
        return self.relpath.endswith("__init__.py")

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


class CSVpath(Filepath):
    """Read and write CSV files

    see testdata.create_csv() which wraps this class
    """
    def __new__(cls, relpath, basedir="", encoding="", header=True, **kwargs):
        instance = super(CSVpath, cls).__new__(
            cls,
            relpath=relpath,
            basedir=basedir,
            encoding=encoding,
        )

        instance.header = header

        kwargs.setdefault("dialect", csv.excel)
        kwargs.setdefault("restval", "")
        kwargs.setdefault("extrasaction", "ignore")
        kwargs.setdefault("quoting", csv.QUOTE_MINIMAL)
        instance.kwargs = kwargs

        return instance

    def replace(self, rows):
        """create a csv file using the given rows

        :param rows: list, a list of row dicts
        """
        # in order to make unicode csvs work we are going to do a round about
        # thing where we write to a string buffer and then pull that out and write
        # it to the file, this is the only way I can make utf-8 work (2020-02-20)
        queue = StringIO()

        self.kwargs.setdefault("fieldnames", list(rows[0].keys()))

        # https://docs.python.org/3/library/csv.html#csv.DictWriter
        writer = csv.DictWriter(queue, **self.kwargs)

        if self.header:
            writer.writeheader()

        with self.replacing() as f:
            for row in rows:
                self.writerow(writer, queue, f, row)

    def append(self, rows):
        """append the rows onto the end of the csv file"""
        queue = StringIO()
        writer = csv.DictWriter(queue, **self.kwargs)
        with self.appending() as f:
            for row in rows:
                self.writerow(writer, queue, f, row)

    def writerow(self, writer, queue, f, row):
        """this is more of an internal method that encapsulates common functionality
        for both replace and append"""
        row = {String(r[0]): ByteString(r[1]) for r in row.items()}
        writer.writerow(row)
        data = queue.getvalue()
        if is_py2:
            data = data.decode(self.encoding)
        f.write(data)
        queue.truncate(0)
        queue.seek(0)

    def lines(self):
        """yields rows of the csv file

        :returns: dict, a row from the csv with the columns mapped to the headers
        """
        if is_py2:
            # for some reason codecs.open doesn't work in python2 like it should, see:
            # https://alexwlchan.net/2018/12/reading-a-utf8-encoded-csv/
            opener = lambda: open(self.path, mode="rb")
        else:
            opener = self.open

        with opener() as f:
            fieldnames = self.kwargs.get("fieldnames", None)
            reader = csv.DictReader(f, fieldnames=fieldnames)

            first_row = True
            for row in reader:
                if is_py2:
                    row = {String(k): String(v) for k, v in row.items()}

                # if we pass in fieldnames then DictReader won't use the first
                # row as fieldnames, so we need to check to make sure the first
                # row isn't a field_name: field_name mapping
                if first_row and fieldnames:
                    first_row = False
                    skip = True
                    for fn in fieldnames:
                        if fn in row and row[fn] != fn:
                            skip = False
                            break

                    if skip:
                        continue

                yield row


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


