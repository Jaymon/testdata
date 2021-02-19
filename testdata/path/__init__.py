# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import random
import inspect
import pkgutil
import string

from datatypes.csv import CSV

from ..compat import *
from ..utils import String, ByteString

from .base import (
    Dirpath,
    Filepath,
    Modulepath,
    ContentBytes,
    ContentString,
    ContentFilepath,
)
from ..image import make_png


def create_dir(path="", tmpdir=""):
    '''
    create a directory path using a tempdir as the root

    so, if you pass in "/foo/bar" that will be combined with a tempdir, so you end 
    up with the final path: /tmp/python/dir/foo/bar

    :param path: string, the temp dir path
    :param tmpdir: string, the temp directory to use as the base
    :returns: Dirpath, the full directory path
    '''
    return Dirpath(path, dir=tmpdir)
create_directory = create_dir
create_d = create_dir


def create_dirs(dirs, tmpdir=""):
    """
    create a whole bunch of directories all at once

    :param dirs: list, the directories to create relative to tmpdir
    :param tmpdir: string, the base directory
    :returns: Dirpath instance pointing to the base directory all of dirs were
        created in
    """
    base_dir = Dirpath(dir=tmpdir)
    base_dir.add(dirs)
    return base_dir
create_ds = create_dirs


def get_dir(path=""):
    """
    return a directory path

    :param path: string, the path to a real directory
    :returns: Dirpath, the path wrapped with all the Dirpath functionality
    """
    if not path:
        path = get_filename()
    return Dirpath(path)
get_directory = get_dir
get_d = get_dir


def create_file(contents="", path="", tmpdir="", encoding="", **kwargs):
    '''
    create a file and return the full path to that file

    :param path: string, the path to the file
    :param contents: string, the file contents
    :param tmpdir: string, the temp directory to use as the base
    :param encoding: string, whatever encoding you want the file to have
    :param **kwargs: anything else will be passed to constructor

    :returns: Filepath, the full file path
    '''
    return Filepath(path, data=contents, encoding=encoding, dir=tmpdir, **kwargs)
create_f = create_file


def create_files(file_dict, tmpdir=""):
    """
    create a whole bunch of files all at once

    file_dict -- dict -- keys are the filepath relative to tmpdir, values are the
        file contents
    tmpdir -- Dirpath -- same as create_module() tmpdir
    """
    base_dir = Dirpath(dir=tmpdir)
    base_dir.add(file_dict)
    return base_dir
create_fs = create_files


def get_file(path="", tmpdir="", encoding="", **kwargs):
    """
    :param **kwargs: key/vals will be passed to get_filename()
    """
    kwargs.setdefault(touch=False)
    return Filepath(path, encoding=encoding, dir=tmpdir, **kwargs)
get_f = get_file


def create_script(*args, **kwargs):
    """Similar to create_file() but will set permission to 777"""
    mode = kwargs.pop("mode", 777)
    path = create_file(*args, **kwargs)
    path.chmod(mode)
    return path


def create_csv(columns, count=0, path="", tmpdir="", encoding="", header=True, **kwargs):
    """Create a csv file using the generators/callbacks found in columns


    :param columns: dict, in the format of key: callback where the callback can
        generate a value for the row, so something like "foo": testdata.get_name
        would work
    :param count: int, how many rows you want, will be randomly created between 
        1 and 50 if not specified
    :param path: string, the path relative to tmpdir, default is randomly generated
    :param tmpdir: string, the temp directory to use as a base/prefix
    :param encoding: string, the encoding to use for the csv file
    :param **kwargs: dict, these will get passed to csv.DictWriter,
        https://docs.python.org/3/library/csv.html#csv.DictWriter
    :returns: testdata.path.CSVpath instance
    """
    if not count:
        if any((callable(c) for c in columns)):
            count = random.randint(1, 50)
        else:
            count = 1

    kwargs.setdefault("ext", "csv")
    path = Filepath(path, dir=tmpdir, encoding=encoding, **kwargs)
    csv = CSV(path, fieldnames=list(columns.keys()))
    with csv:
        if not header:
            csv.writer.has_header = True

        for i in range(count):
            d = {}
            for field_name, callback in columns.items():
                if callable(callback):
                    d[field_name] = callback()
                else:
                    d[field_name] = callback

            csv.add(d)

    return csv


def create_image(image_type="", path="", tmpdir=""):
    """Creates an image using the images founc in the data/ directory

    :param image_type: string, the type of image you want, one of jpg, png, gif, agif, ico
    :param path: string, the path or basename (eg, foo/bar.jpg or che) of the image
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
    contents = pkgutil.get_data(__name__.split(".")[0], "data/{}".format(image))

    if path:
        if not path.lower().endswith(ext):
            path += ext
    else:
        path = get_filename(ext=ext)

    return create_file(
        contents=contents,
        path=path,
        tmpdir=tmpdir,
        encoding=None
    )


def create_jpg(path="", tmpdir=""):
    """create a jpeg image"""
    return create_image(image_type="jpg", path=path, tmpdir=tmpdir)
create_jpeg=create_jpg


def create_png(path="", tmpdir="", width=0, height=0, color=None):
    """create a png image"""
    if width and height:
        ext = ".png"
        if path:
            if not path.lower().endswith(ext):
                path += ext
        else:
            path = get_filename(ext=ext)

        return create_file(
            path=path,
            contents=make_png(width, height, color=color),
            tmpdir=tmpdir,
            encoding=None
        )

    else:
        return create_image(image_type="png", path=path, tmpdir=tmpdir)


def create_gif(path="", tmpdir=""):
    """create a static gif image"""
    return create_image(image_type="gif", path=path, tmpdir=tmpdir)


def create_animated_gif(path="", tmpdir=""):
    """create an animated gif image"""
    return create_image(image_type="agif", path=path, tmpdir=tmpdir)
create_agif=create_animated_gif


def create_ico(path="", tmpdir=""):
    """create an icon image"""
    return create_image(image_type="ico", path=path, tmpdir=tmpdir)
create_icon=create_ico
create_favicon=create_ico


def get_filename(ext="", name="", **kwargs):
    """return just a valid file name

    :param ext: string, the extension you want the file to have
    :param prefix: string, this will be the first part of the file's name
    :param name: string, the name you want to use (prefix will be added to the front
        of the name and ext will be added to the end of the name)
    :returns: string, the random filename
    """
    return Filepath.get_basename(ext=ext, name=name, **kwargs)
get_file_name = get_filename
filename = get_filename
file_name = get_filename


def get_module_name(bits=1, name="", **kwargs):
    """Returns just a valid module name or module path

    :param bits: int, how many parts you want in your module path (1 is foo, 2 is foo.bar, etc)
    :param prefix: string, if you want the last bit to be prefixed with something
    :param postfix: string, if you want the last bit to be posfixed with something (eg, ".py")
    :param name: string, the name you want to use for the last bit
        (prefix will be added to the front of the name and postfix will be added to
         the end of the name)
    :returns: string, the modulepath
    """
    parts = Modulepath.get_parts(bits=bits, name=name, **kwargs)
    return ".".join(parts)
get_package_name = get_module_name
get_modulename = get_module_name
get_modname = get_module_name
get_modpath = get_module_name
get_modulepath = get_module_name
get_module_path = get_module_name
modulename = get_module_name
module_name = get_module_name


def get_classname(name=""):
    n = get_filename(name=name)
    return n.title()
get_class_name = get_classname
classname = get_classname
class_name = get_classname


def get_source_filepath(v):
    """Returns the full filepath of a given python object

    :param v: mixed, a python object to find the source file for
    :returns: Filepath
    """
    try:
        ret = inspect.getsourcefile(v)
    except TypeError:
        ret = inspect.getsourcefile(v.__class__)
    return Filepath(ret)
get_source_file = get_source_filepath
get_source_path = get_source_filepath


def create_module(data="", modpath="", tmpdir="", make_importable=True, **kwargs):
    '''
    create a python module folder structure so that the module can be imported

    :param data: str, the contents of the module
    :param modpath: str, something like foo.bar
    :param tmpdir: str, the temp directory that will be added to the syspath if make_importable is True
    :param make_importable: bool, if True, then tmpdir will be added to the python path so it can be imported
    :return: Modulepath instance
    '''
    if not data:
        data = kwargs.pop("contents", kwargs.pop("content", kwargs.pop("text", "")))

    return Modulepath(
        modpath,
        data=data,
        dir=tmpdir,
        make_importable=make_importable,
        **kwargs
    )


def create_modules(module_dict, modpath="", tmpdir="", make_importable=True):
    """
    create a whole bunch of modules all at once

    :param module_dict: dict, keys are the module_name, values are the module contents
    :param modpath: string, if you want all the modules in module_dict to have a prefix, you
        can pass this in, so if you did prefix is "foo.bar" then all the keys in module_dict
        will be prepended with "foo.bar"
    :param tmpdir: string, same as create_module() tmpdir
    :param make_importable: boolean, same as create_module() tmpdir
    :returns: Dirpath
    """
    module_base_dir = create_dir(tmpdir=tmpdir)

    if modpath:
        ks = list(module_dict.keys()) # we cast to list to make sure ks doesn't grow
        for k in ks:
            module_dict[".".join(filter(None, [modpath, k]))] = module_dict.pop(k)

    for modname, data in module_dict.items():
        create_module(
            data=data,
            modpath=modname,
            tmpdir=module_base_dir,
            make_importable=make_importable,
        )
        make_importable = False

    return module_base_dir
create_packages = create_module


def create_package(data="", modpath="", tmpdir="", make_importable=True, **kwargs):
    '''
    create a python package folder structure so that the package can be imported

    a package is different than a module in that it is a module_name folder with
    an __init__.py instead of module_name.py

    module_name -- string -- something like foo.bar
    contents -- string -- the contents of the module
    tmpdir -- string -- the temp directory that will be added to the syspath if make_importable is True
    make_importable -- boolean -- if True, then tmpdir will be added to the python path so it can be imported

    return -- Module -- the module file path
    '''
    kwargs.setdefault["is_package"] = True
    return create_module(
        data=data,
        modpath=modpath,
        dir=tmpdir,
        make_importable=make_importable,
        **kwargs
    )

#     if not data:
#         data = kwargs.pop("contents", kwargs.pop("content", kwargs.pop("text", "")))
# 
#     return Modulepath(
#         modpath,
#         data=data,
#         dir=tmpdir,
#         make_importable=make_importable,
#         is_package=True
#     )


