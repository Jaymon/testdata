# -*- coding: utf-8 -*-
import os
import re
import sys
import pkgutil
import importlib
import inspect
import random
from contextlib import contextmanager
import zlib
import struct
import textwrap

from datatypes.path import (
    TempFilepath,
    TempDirpath,
    Dirpath,
    Filepath,
)
from datatypes.reflection import ReflectModule
from datatypes.collections import Namespace
from datatypes.csv import CSV

from .compat import *
from .config import environ
from .base import TestData


###############################################################################
# Supporting classes and methods
###############################################################################
class Path(object):
    @classmethod
    def gettempdir(cls):
        """Overrides parent to allow changing the temp directory"""
        return os.path.realpath(environ.TEMPDIR)

    @classmethod
    def tempdir_class(cls):
        return TempDirpath

    @classmethod
    def tempfile_class(cls):
        return TempFilepath

    @classmethod
    def tempmodule_class(cls):
        return TempModulepath

    @classmethod
    def file_class(cls):
        return Filepath

    @classmethod
    def dir_class(cls):
        return Dirpath

    def prepare_text(self, data, **kwargs):
        """Wraps parent's prepare_text to allow data and certain kwargs to be
        lists instead of strings, if they are lists then the list will be
        considered lines and will be joined with a newline.

        It makes sense for the main datatype paths to not take lists but I've
        really come to depend on this behavior in testdata
        """
        for k in ["header", "footer"]:
            if v := kwargs.get(k, ""):
                if not isinstance(v, basestring):
                    kwargs[k] = "\n".join(v)

        if isinstance(data, basestring):
            data = textwrap.dedent(data)

        else:
            data = "\n".join(data)

#         if not isinstance(data, basestring):
#             data = "\n".join(data)

        return super().prepare_text(data, **kwargs)


class Filepath(Path, Filepath):
    pass


class Dirpath(Path, Dirpath):
    pass


class TempDirpath(Path, TempDirpath):
    def module(self, module_path):
        return self.get_module(module_path)

    def get_module(self, module_path):
        """similar to modpath but returns the actual module instead of
        Modulepath instance

        Return the actual module imported via module_path
        """
        injected = False
        if self.path not in sys.path:
            injected = True
            sys.path.insert(0, self.path) 

        module = importlib.import_module(module_path)

        if injected:
            sys.path.pop(0) 

        return module

    def modules(self):
        return self.get_modules()

    def get_modules(self):
        """iterate through all the modules under this directory"""
        for modpath in self.modpaths():
            yield modpath.module()

    def modpath(self, module_path):
        """Return a module that is rooted in this directory"""
        return self.tempmodule_class()(module_path, dir=self.path)

    def modpaths(self):
        """Similar to modules, returns all the modules under this directory as
        Modulepath instances"""
        for module_info in pkgutil.iter_modules([self.path]):
            parts = self.relparts + [module_info[1]]
            yield self.tempmodule_class()(".".join(parts), dir=self.basedir)

            if module_info[2]: # module is a package because index 2 is True
                submodules = self.tempdir_class()(parts, dir=self.basedir)
                for submodule in submodules.modpaths():
                    yield submodule

    def __contains__(self, pattern):
        return self.has(pattern=pattern)


class TempFilepath(Path, TempFilepath):
    def run(self, arg_str="", cwd="", environ=None, **kwargs):
        """Treat this file like a script and execute it

        :param arg_str: string, flags you want to pass into the execution of the
            script
        :returns: string, the output of running the file/script
        """
        # avoid circular dependency
        from .client import FileCommand

        cwd = cwd if cwd else self.basedir
        cmd = FileCommand(self, cwd=cwd, environ=environ)
        return cmd.run(arg_str, **kwargs)


class TempModulepath(TempFilepath):
    """create a python module folder structure so that the module can be
    imported

    NOTE -- the import directory can be found at .basedir
    """
    @property
    def modparts(self):
        return self.split('.')

    @property
    def import_dir(self):
        """Returns the importable directory for this module"""
        return self.basedir

    @property
    def directory(self):
        """Return the directory this module lives in"""
        d = super().parent
        if self.is_package():
            d = d.directory
        return d

#     @classmethod
#     def splitparts(cls, *args, **kwargs):
#         kwargs.setdefault("root", "")
#         kwargs.setdefault("regex", r"[\.\\/]+")
#         return super().splitparts(*args, **kwargs)

#     @classmethod
#     def joinparts(cls, *args, **kwargs):
#         kwargs.setdefault("sep", ".")
#         kwargs.setdefault("root", "")
#         kwargs.setdefault("regex", r"[\.\\/]+")
#         return super().joinparts(*args, **kwargs)

    @classmethod
    def normpaths(cls, *args, **kwargs):
        kwargs.setdefault("root", "")
        kwargs.setdefault("regex", r"[\.\\/]+")
        return super().normpaths(*args, **kwargs)

    @classmethod
    def normparts(cls, *parts, **kwargs):
        kwargs.setdefault("root", "")
        kwargs.setdefault("regex", r"[\.\\/]+")
        parts = super().normparts(*parts, **kwargs)
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
            # check if we already have a package
            path = super().normpath(parts, basename)
            if os.path.isdir(path):
                if "is_package" in kwargs:
                    raise ValueError("Cannot convert package back to module")

                parts.append(basename) 
                parts.append("__init__.py")

            else:
                parts.append("{}.py".format(basename))

        path = super().normpath(*parts, **kwargs)
        return path

    @classmethod
    def normvalue(cls, *parts, **kwargs):
        return ".".join(parts[1:])

    @classmethod
    def create_as(cls, instance, **kwargs):
        instance = super().create_as(instance, **kwargs)

        # add the path to the top of the sys path so importing the new module
        # will work
        make_importable = kwargs.pop("make_importable", True)
        if make_importable:
            sys.path.insert(0, instance.basedir) 

        return instance

    def prepare_text(self, data, **kwargs):
        self.touch()

        data, encoding, errors = super().prepare_text(data, **kwargs)

        if kwargs.get("add_future", False):
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

        add_coding = kwargs.get("add_coding", False)
        if add_coding:
            data = f"# -*- coding: {encoding} -*-\n" + data.lstrip()

        if not data.endswith("\n"):
            data += "\n"

        return data, encoding, errors

    def touch(self, mode=0o666, exist_ok=True):
        super().touch(mode=mode, exist_ok=exist_ok)

        # we need to make sure every part/directory of the module path is a
        # valid python module with an __init__.py file

        mod_parts = filter(lambda p: not p.endswith(".py"), self.relparts)

        base_dir = self.basedir
        for modname in mod_parts:
            mod_file = self.create_file(
                base_dir,
                "{}.py".format(modname),
                touch=False
            )

            # turn module.py into a package (module/__init__.py)
            base_dir = self.create_dir(base_dir, modname)
            target = self.create_file(base_dir, "__init__.py", touch=False)

            if mod_file.isfile():
                mod_file.mv(target)

            else:
                target.touch()

    def modpaths(self):
        """Similar to modules, returns all the modules under this directory as
        Modulepath instances"""
        dp = self.tempdir_class()(self.modparts, dir=self.basedir)
        return dp.modpaths()

    def classes(self):
        return self.get_classes()

    def get_classes(self):
        """Return all the classes this module contains"""
        for m in self.get_modules():
            for klass_name, klass in inspect.getmembers(m, inspect.isclass):
                yield klass

    def module(self):
        return self.get_module()

    def get_module(self, module_path=""):
        """Return the actual module this Modulepath represents"""
        dp = self.tempdir_class()(dir=self.basedir)

        if module_path:
            module_path = self.joinparts(self, module_path, sep=".")

        else:
            module_path = self

        return dp.get_module(module_path)

    def modules(self):
        return self.get_modules()

    def get_modules(self):
        dp = self.tempdir_class()(dir=self.basedir)
        for m in dp.get_modules():
            if m.__name__.startswith(self):
                yield m

    def is_package(self):
        """returns True if this module is a package (directory with __init__.py
        file in it)"""
        return self.path.endswith("__init__.py")

    def run(self, arg_str="", cwd="", environ=None, **kwargs):
        """Run this module on the command line

        :param arg_str: string, flags you want to pass into the execution of
            this module
        :returns: string, the output of running the file/script
        """
        # avoid circular dependency
        from .client import ModuleCommand

        mod = self
        cwd = cwd if cwd else mod.basedir
        if self.endswith("__main__") or self.endswith("__init__"):
            modparts = self.modparts
            modparts.pop(-1)
            mod = ".".join(modparts)

        cmd = ModuleCommand(mod, cwd=cwd, environ=environ)
        return cmd.run(arg_str, **kwargs)


###############################################################################
# testdata functions
###############################################################################
class PathData(TestData):
    def _make_png(self, width, height, color=None):
        """Make a png image of arbitrary width, height, and color

        The majority of this function comes from this great SO answer with
        public domain code:

            https://stackoverflow.com/a/25835368/5006

        it's been modified with help from:
            http://www.libpng.org/pub/png/spec/1.2/PNG-Chunks.html
            https://en.wikipedia.org/wiki/Portable_Network_Graphics
            https://www.w3.org/TR/PNG/

        to support arbitrary dimensions and 0-255 rgb colors

        :param width: int, the width of the image you want to generate
        :param height: int, the height of the image you want to generate
        :param color: list|tuple, a list/tuple of an (r, g, b) value where r,
            g, and b are integers between 0 and 255
        :returns: bytes, the raw png that can be written to a file
        """
        def I1(value):
            return struct.pack("!B", value & (2**8-1))

        def I4(value):
            return struct.pack("!I", value & (2**32-1))

        def B1(value):
            return value

        # PNG file header
        png = b"\x89" + "PNG\r\n\x1A\n".encode('ascii')

        # IHDR block
        # colortype values:
        #   6 for color: Each pixel is an R,G,B triple, followed by an alpha
        #     sample
        #   0 for b&w: Each pixel is a grayscale sample
        colortype = 6 if color else 0
        bitdepth = 8 # with one byte per pixel (0..255)
        compression = 0 # zlib (no choice here)
        filtertype = 0 # adaptive (each scanline seperately)
        interlaced = 0 # no
        IHDR = I4(width) + I4(height) + I1(bitdepth)
        IHDR += I1(colortype) + I1(compression)
        IHDR += I1(filtertype) + I1(interlaced)
        block = "IHDR".encode('ascii') + IHDR
        png += I4(len(IHDR)) + block + I4(zlib.crc32(block))

        # IDAT block (the actual image)
        # if we don't have a color then we just use a black pixel bit, but if
        # we do have a color we use 4 bits (r, g, b, a) for each pixel
        raw = bytearray()

        if color:
            # NOTE -- you could make the images smaller by creating a palette
            # (colortype 2) with one color and then just using the index like
            # the b&w image does, but that's way more work because we would
            # need to add a PLTE block with the palette information
            c = []
            for co in color:
                c.append(B1(co))
            c.append(B1(255)) # alpha
        else:
            c = [B1(0)] # default black pixel

        # populate the actual image data
        for y in range(height):
            raw.append(B1(0)) # no filter for this scanline
            for x in range(width):
                raw.extend(c)

        compressor = zlib.compressobj()
        compressed = compressor.compress(raw)
        compressed += compressor.flush()
        block = "IDAT".encode('ascii') + compressed
        png += I4(len(compressed)) + block + I4(zlib.crc32(block))

        # IEND block
        block = "IEND".encode('ascii')
        png += I4(0) + block + I4(zlib.crc32(block))

        return png

    def _make_jpg(width, height, color=None):
        """Looks like this would be possible but I don't really need it right
        now so I'm not bothering right now

        https://en.wikipedia.org/wiki/JPEG#The_JPEG_standard
        https://stackoverflow.com/a/16755049/5006

        you can probably pick apart how PIL does it:
            https://github.com/whatupdave/pil/blob/master/PIL/JpegImagePlugin.py

        search:
            create a jpeg of one color in pure python
        """
        raise NotImplementedError()

    def create_dir(self, path="", tmpdir=""):
        '''
        create a directory path using a tempdir as the root

        so, if you pass in "/foo/bar" that will be combined with a tempdir, so
        you end up with the final path: /tmp/python/dir/foo/bar

        :param path: string, the temp dir path
        :param tmpdir: string, the temp directory to use as the base
        :returns: Dirpath, the full directory path
        '''
        return TempDirpath(path, dir=tmpdir)
    create_directory = create_dir
    create_d = create_dir

    def create_dirs(self, dirs, tmpdir=""):
        """
        create a whole bunch of directories all at once

        :param dirs: list, the directories to create relative to tmpdir
        :param tmpdir: string, the base directory
        :returns: Dirpath instance pointing to the base directory all of dirs
            were created in
        """
        base_dir = TempDirpath(dir=tmpdir)
        base_dir.add(dirs)
        return base_dir
    create_ds = create_dirs

    def get_dir(self, path="", tmpdir="", **kwargs):
        """
        return a directory path

        :param path: string, the path to a real directory
        :returns: Dirpath, the path wrapped with all the Dirpath functionality
        """
        if not path:
            # we have to create a filename because otherwise the temp directory
            # will exist
            path = self.get_filename()
        kwargs.setdefault("touch", False)
        return TempDirpath(path, dir=tmpdir, **kwargs)
    get_directory = get_dir
    get_d = get_dir

    def create_file(self, data="", path="", tmpdir="", encoding="", **kwargs):
        '''
        create a file and return the full path to that file

        :param path: string, the path to the file
        :param data: string, the file contents
        :param tmpdir: string, the temp directory to use as the base
        :param encoding: string, whatever encoding you want the file to have
        :param **kwargs: anything else will be passed to constructor

        :returns: Filepath, the full file path
        '''
        return TempFilepath(
            path,
            data=data,
            encoding=encoding,
            dir=tmpdir,
            **kwargs
        )
    create_f = create_file

    def create_files(self, file_dict, tmpdir="", **kwargs):
        """
        create a whole bunch of files all at once

        :param file_dict: dict, keys are the filepath relative to tmpdir, values
            are the file contents
        :param tmpdir: Dirpath, same as create_module() tmpdir
        :param **kwargs:
            encoding -- the encoding for any files
            errors -- what to do if encoding encounters an error
        """
        base_dir = TempDirpath(dir=tmpdir)
        base_dir.add(file_dict, **kwargs)
        return base_dir
    create_fs = create_files

    def get_file(self, path="", tmpdir="", encoding="", **kwargs):
        """
        :param **kwargs: key/vals will be passed to get_filename()
        """
        kwargs.setdefault("touch", False)
        return TempFilepath(path, encoding=encoding, dir=tmpdir, **kwargs)
    get_f = get_file

    def create_script(self, *args, **kwargs):
        """Similar to create_file() but will set permission to 777"""
        mode = kwargs.pop("mode", 777)
        path = self.create_file(*args, **kwargs)
        path.chmod(mode)
        return path

    def create_csv(
        self,
        columns,
        path="",
        tmpdir="",
        encoding="",
        header=True,
        default=None,
        **kwargs
    ):
        """Create a csv file using the generators/callbacks found in columns

        :param columns: dict|list
            * dict[str, callable], where the callback can generate a value
                for the row, so something like "foo": testdata.get_name
                would work
            * dict[str, list], then each value at each index of the list
                will be used as the value for a row, `default` will be used
                if the list doesn't have a value at that index
            * list[dict], then each dict in the list will be considered one
                row of the csv
            * list[str], each item in the list is a key will be randomly
                given a callback to generate the csv
        :param path: string, the path relative to tmpdir, default is randomly
            generated
        :param tmpdir: string, the temp directory to use as a base/prefix
        :param encoding: string, the encoding to use for the csv file
        :param header: bool, True (default) if you want the column names to
            be the first line in the file
        :param default: str|int|None, the default value if the column is
            missing a value
        :param **kwargs: dict, these will get passed to csv.DictWriter,
            https://docs.python.org/3/library/csv.html#csv.DictWriter
        :returns: testdata.path.CSVpath instance
        """
        if isinstance(columns, list):
            d = {}

            for i in range(len(columns)):
                if isinstance(columns[i], str):
                    callback = self.get_words if self.yes() else self.get_int
                    d[columns[i]] = callback

                else:
                    for field_name, callback in columns[i].items():
                        if field_name not in d:
                            d[field_name] = [default] * i
                        d[field_name].append(callback)

                    for field_name in d.keys():
                        default_rows = max(1 + i - len(d[field_name]), 0)
                        d[field_name].extend([default] * default_rows)

            columns = d

        if any((callable(c) for c in columns.values())):
            kwargs.setdefault("default_min", 1)
            kwargs.setdefault("default_max", 50)

        elif any(isinstance(c, list) for c in columns.values()):
            count = 0
            for k, c in list(columns.items()):
                if not isinstance(c, Sequence):
                    columns[k] = c = [c]

                count = max(count, len(c))

            kwargs.setdefault("count", count)

        else:
            kwargs.setdefault("count", 1)

        fieldnames = list(columns.keys())

        count = self.get_size(**kwargs)

        kwargs.setdefault("ext", "csv")
        path = TempFilepath(path, dir=tmpdir, encoding=encoding, **kwargs)
        csv = CSV(path, fieldnames=fieldnames)
        with csv:
            csv.writer.has_header = not header

            for i in range(count):
                d = {}
                for field_name, callback in columns.items():
                    if callable(callback):
                        d[field_name] = callback()

                    elif isinstance(callback, list):
                        if i < len(callback):
                            d[field_name] = callback[i]

                        else:
                            d[field_name] = default

                    else:
                        d[field_name] = callback

                csv.add(d)

        return csv

    def get_csv(self, *args, **kwargs):
        """Wrapper around .create_csv but returns the csv body, because
        sometimes you just need the csv contents and don't care at all about
        the actual file

        :param *args: see .create_csv
        :param **kwargs: see .create_csv
        :returns: str, the csv contents, nothing else
        """
        csv = self.create_csv(*args, **kwargs)
        return csv.read_text()

    def create_image(self, image_type="", path="", tmpdir=""):
        """Creates an image using the images founc in the data/ directory

        :param image_type: string, the type of image you want, one of jpg, png,
            gif, agif, ico
        :param path: string, the path or basename (eg, foo/bar.jpg or che) of
            the image
        :param tmpdir: Dirpath, same as create_module() tmpdir
        :returns: Filepath, the path to the image file
        """
        images = [
            (set(["jpg", "jpeg"]), ".jpg", "static.jpg"),
            (set(["png"]), ".png", "static.png"),
            (set(["gif"]), ".gif", "static.gif"),
            (set(["agif", "animated_gif"]), ".gif", "animated.gif"),
            (set(["ico", "favicon", "ico"]), ".ico", "favicon.ico"),
        ]

        if image_type:
            image_type = image_type.lower()
            for itypes, ext, image in images:
                if image_type in itypes:
                    break

        else:
            image_type, ext, image = random.choice(images)

        # https://docs.python.org/2/library/pkgutil.html#pkgutil.get_data
        data = pkgutil.get_data(
            __name__.split(".")[0],
            "data/{}".format(image)
        )

        if path:
            if not path.lower().endswith(ext):
                path += ext
        else:
            path = self.get_filename(ext=ext)

        return self.create_file(
            data=data,
            path=path,
            tmpdir=tmpdir,
            encoding=None
        )

    def create_jpg(self, path="", tmpdir=""):
        """create a jpeg image"""
        return self.create_image(image_type="jpg", path=path, tmpdir=tmpdir)
    create_jpeg=create_jpg

    def create_png(self, path="", tmpdir="", width=0, height=0, color=None):
        """create a png image"""
        if width and height:
            ext = ".png"
            if path:
                if not path.lower().endswith(ext):
                    path += ext
            else:
                path = self.get_filename(ext=ext)

            return self.create_file(
                path=path,
                data=self._make_png(width, height, color=color),
                tmpdir=tmpdir,
                encoding=None
            )

        else:
            return self.create_image(image_type="png", path=path, tmpdir=tmpdir)

    def create_gif(self, path="", tmpdir=""):
        """create a static gif image"""
        return self.create_image(image_type="gif", path=path, tmpdir=tmpdir)

    def create_animated_gif(self, path="", tmpdir=""):
        """create an animated gif image"""
        return self.create_image(image_type="agif", path=path, tmpdir=tmpdir)
    create_agif=create_animated_gif

    def create_ico(self, path="", tmpdir=""):
        """create an icon image"""
        return self.create_image(image_type="ico", path=path, tmpdir=tmpdir)
    create_icon=create_ico
    create_favicon=create_ico

    def get_filename(self, ext="", name="", **kwargs):
        """return just a valid file name

        :param ext: str, the extension you want the file to have
        :param prefix: str, this will be the first part of the file's name
        :param name: str, the name you want to use (prefix will be added to
            the front of the name and ext will be added to the end of the name)
        :returns: str, the random filename
        """
        return TempFilepath.get_basename(ext=ext, name=name, **kwargs)
    get_file_name = get_filename
    filename = get_filename
    file_name = get_filename
    get_basename = get_filename

    def get_module_name(self, count=1, name="", **kwargs):
        """Returns just a valid module name or module path

        :param count: int, how many parts you want in your module path (1 is
            foo, 2 is foo.bar, etc)
        :param prefix: string, if you want the last bit to be prefixed with
            something
        :param postfix: str, if you want the last bit to be posfixed with
            something (eg, ".py")
        :param name: str, the name you want to use for the last bit
            (prefix will be added to the front of the name and postfix will be
            added to the end of the name)
        :returns: str, the modulepath
        """
        parts = TempModulepath.get_parts(count=count, name=name, **kwargs)
        return ".".join(parts)
    get_package_name = get_module_name
    get_modulename = get_module_name
    get_modname = get_module_name
    get_modpath = get_module_name
    get_modulepath = get_module_name
    get_module_path = get_module_name
    modulename = get_module_name
    module_name = get_module_name

    def get_classname(self, name=""):
        n = self.get_filename(name=name)
        return n if name else n.title()
    get_class_name = get_classname
    classname = get_classname
    class_name = get_classname

    def get_source_filepath(self, v):
        """Returns the full filepath of a given python object

        :param v: Any, a python object to find the source file for
        :returns: Filepath
        """
        try:
            ret = inspect.getsourcefile(v)
        except TypeError:
            ret = inspect.getsourcefile(v.__class__)
        return TempFilepath(ret)
    get_source_file = get_source_filepath
    get_source_path = get_source_filepath
    get_sourcepath = get_source_filepath
    get_sourcefilepath = get_source_filepath
    get_sourcefile = get_source_filepath

    def create_module(
        self,
        data="",
        modpath="",
        tmpdir="",
        make_importable=True,
        **kwargs
    ):
        """
        create a python module folder structure so that the module can be
        imported

        :param data: str|list|Mapping, the contents of the module
        :param modpath: str, something like foo.bar
        :param tmpdir: str, the temp directory that will be added to the
            syspath if make_importable is True
        :param make_importable: bool, if True, then tmpdir will be added to the
            python path so it can be imported
        :param **kwargs:
            load: bool, set to True to import the module
            is_package: bool, True if module should be a package (directory
                with __init__.py file instead of file.py)
        :return: Modulepath instance
        """
        if not data:
            data = kwargs.pop(
                "contents",
                kwargs.pop("content", kwargs.pop("text", ""))
            )

        load = kwargs.pop("load", kwargs.pop("import", False))
        ms = []

        if isinstance(data, Mapping):
            modpath = TempModulepath(
                modpath,
                dir=tmpdir,
                make_importable=make_importable,
                is_package=True,
                **kwargs
            )
            ms.append(modpath)

            modpaths = TempModulepath.normpaths(
                data,
                modpath,
            )

            # NOTE -- we don't pass in all kwargs to the submodules because
            # kwargs could contain keys like name and prefix, but we do care
            # about certain values
            smkwargs = {}
            for k in ["header", "footer"]:
                if k in kwargs:
                    smkwargs[k] = kwargs[k]

            for mname, mdata in modpaths:
                m = self.create_module(
                    data=mdata,
                    modpath=mname,
                    tmpdir=modpath.basedir,
                    make_importable=False,
                    **smkwargs
                )
                ms.append(m)

        else:
            modpath = TempModulepath(
                modpath,
                data=data,
                dir=tmpdir,
                make_importable=make_importable,
                **kwargs
            )
            ms.append(modpath)

        if load:
            # we import the module to load whatever it has into memory
            for m in ms:
                m.get_module()

        return modpath

    def create_modules(self, module_dict, modpath="", tmpdir="", **kwargs):
        """
        create a whole bunch of modules all at once

        :param module_dict: dict, keys are the module_name, values are the
            module contents
        :param modpath: str, if you want all the modules in module_dict to
            have a prefix, you can pass this in, so if you did prefix is
            "foo.bar" then all the keys in module_dict will be prepended with
            "foo.bar"
        :param tmpdir: str, same as create_module() tmpdir
        :returns: Dirpath
        """
        module_base_dir = self.create_dir(tmpdir=tmpdir)
        module_list = TempModulepath.normpaths(
            module_dict,
            modpath,
        )

        for modname, data in module_list:
            m = self.create_module(
                data=data,
                modpath=modname,
                tmpdir=module_base_dir,
                **kwargs
            )
            kwargs["make_importable"] = False

        return module_base_dir
    create_packages = create_module

    def create_module_classes(self, data="", modpath="", tmpdir="", **kwargs):
        """Create a python module using data and then return all the classes
        that were defined in that module

        :param data: str, the contents of the module
        :param modpath: str, something like foo.bar
        :param tmpdir: str, the temp directory where the module will reside
        :return: dict[str, type], the key is the class name and the value is
            the actual class object
        """
        d = Namespace()
        modpath = self.create_module(
            data=data,
            modpath=modpath,
            tmpdir=tmpdir,
            **kwargs
        )

        rm = ReflectModule(modpath.get_module())

        for c in rm.get_classes(ignore_imported=True):
            d[c.__qualname__] = c

        return d

    def create_module_class(
        self,
        data="",
        class_name="",
        modpath="",
        tmpdir="",
        **kwargs
    ):
        """Create a python module using data and then return the class defined
        in that module

        :param data: str, the contents of the module
        :param class_name: str, the name of the class defined in data that you
            want returned, if empty then the first class will be returned, so
            if there is more than one class defined in data then the class
            returned is undefined, but it won't be a class that starts with
            an underscore or has a period in the class's __qualname__ attribute
        :param modpath: str, something like foo.bar
        :param tmpdir: str, the temp directory where the module will reside
        :return: type, the class defined in the created module using data
        """
        classes = self.create_module_classes(
            data=data,
            modpath=modpath,
            tmpdir=tmpdir,
            **kwargs
        )

        if not class_name:
            for class_name in classes.keys():
                if not class_name.startswith("_") and "." not in class_name:
                    break

        return classes[class_name]

    def create_package(self, data="", modpath="", tmpdir="", **kwargs):
        '''create a python package folder structure so that the package can be
        imported

        a package is different than a module in that it is a module_name folder
        with an __init__.py instead of module_name.py

        :param module_name: str, something like foo.bar
        :param data: str, the contents of the module
        :param tmpdir: str, the temp directory that will be added to the syspath
            if make_importable is True
        :returns: TempModulepath, the module file path
        '''
        kwargs.setdefault("is_package", True)
        return self.create_module(
            data=data,
            modpath=modpath,
            tmpdir=tmpdir,
            **kwargs
        )

    def find_data_file(self, fileroot, basedir="", encoding=""):
        """find and return a file

        this is primarily used by find_data(), find_data_text(), and
        find_data_bytes()

        :param fileroot: string, if dirpath + fileroot is actually a full
            filepath then that will be returned, if not then dirpath/fileroot.*
            will be searched for
        :param basedir: string, the base directory used to search for fileroot
        :returns: Path, the found file
        """
        f = None

        filepath = Filepath(fileroot, dir=basedir)
        if filepath.exists():
            f = filepath

        else:
            basedir = basedir or environ.CONTENTS_DIR
            if not basedir:
                basedir = os.getcwd()

            if not basedir:
                raise IOError("Could not find a testdata data directory")

            basedir = Dirpath(basedir)
            patterns = [fileroot, "{}.*".format(fileroot)]
            for pattern in patterns:
                for f in basedir.rglob(pattern):
                    if f:
                        break

            if not f:
                raise IOError(
                    "Could not find a testdata data file matching {}".format(
                        fileroot
                    )
                )

        if encoding:
            f.encoding = encoding
        return f
    get_content_file = find_data_file
    get_content_path = find_data_file
    get_path = find_data_file
    get_data_path = find_data_file

    def find_data_text(self, fileroot, basedir="", encoding=""):
        f = self.find_data_file(fileroot, basedir, encoding)
        return f.read_text()

    def find_data_bytes(self, fileroot, basedir=""):
        f = self.find_data_file(fileroot, basedir)
        return f.read_bytes()

    def find_data(self, fileroot, basedir="", encoding=""):
        """Returns the contents of a file matching basedir/fileroot.*

        :param fileroot: string, can be a basename (fileroot.ext) or just a file
            root, in which case basedir/fileroot.* will be searched for and
            first file matched will be used
        :param basedir: string, the directory to search for fileroot.*, if not
            passed in then os.getcwd()/*/testdata will be searched for
        :returns: string, the contents of the found file
        """
        if encoding:
            return self.find_data_text(fileroot, basedir, encoding)

        else:
            return self.find_data_bytes(fileroot, basedir)
    get_content_body = find_data
    get_contents = find_data
    get_content_contents = find_data
    get_content_data = find_data
    get_data = find_data

    @contextmanager
    def chdir(self, curdir, **kwargs):
        """Change the directory for the current context

        :Example:
            with testdata.chdir("/new/current/directory"):
                print(os.getcwd())
            print(os.getcwd())

        :param curdir: str, the directory you want to now be the current
            directory
        """
        # backup the current directory to restore it when context resets
        cwd = os.getcwd()

        os.chdir(curdir)
        yield curdir

        # restore the original current directory 
        os.chdir(cwd)
    cwd = chdir
    curdir = chdir

    def get_interpreter(self):
        """Return the best python interpreter

        :returns: a Filepath
        """

        exe = sys.executable
        version_info = sys.version_info

        if re.search(r"\d+\.\d+", exe):
            ret = exe

        elif re.search(r"\d+", exe):
            ret = "{}.{}".format(exe, version_info[1])
            f = Filepath(ret)
            if not f.exists():
                ret = exe

        else:
            # try major.minor
            version = ".".join(map(String, version_info[0:2]))
            ret = "{}{}".format(exe, version)
            f = Filepath(ret)

            if not f.exists():
                # try major
                ret = "{}.{}".format(exe, version_info[1])
                f = Filepath(ret)
                if not f.exists():
                    # just return the found interpreter
                    ret = exe

        f = Filepath(ret)

        # https://semver.org/
        f.major = version_info[0]
        f.minor = version_info[1]
        f.patch = version_info[2]
        f.release = version_info[3]
        f.version = "{}.{}.{}".format(f.major, f.minor, f.patch)

        return f
    get_exe = get_interpreter
    get_exec = get_interpreter
    get_executable = get_interpreter
    get_python = get_interpreter

