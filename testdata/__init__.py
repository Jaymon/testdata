# -*- coding: utf-8 -*-
'''
a module to make it easy to get some test data

NOTE: all methods that return strings will return unicode utf-8 strings

for a utf-8 stress test, see: http://www.cl.cam.ac.uk/~mgk25/ucs/examples/UTF-8-test.txt
you can get all the unicode chars and their names: ftp://ftp.unicode.org/
    ftp://ftp.unicode.org/Public/6.3.0/ucd/UnicodeData-6.3.0d2.txt
'''
from __future__ import unicode_literals, division, print_function, absolute_import
import re
import random
from random import randint, choice # expose common random functions so testdata.function works
import string
import sys
import tempfile
import os
import codecs
import datetime
from collections import deque, Sequence
import types
import imp
import inspect
import copy
import uuid
import hashlib
import logging
import time
from time import sleep
from contextlib import contextmanager

from .compat import *
from .data import (
    _names,
    _unicode_names,
    _ascii_paragraphs,
    _unicode_paragraphs,
    _ascii_words,
    _unicode_words,
    _words,
    _first_names_male,
    _first_names_female,
    _last_names
)

from . import environ
from .path import Dirpath, Filepath, Modulepath, ContentBytes, ContentString
from .threading import Thread
from .output import Capture
from .server import PathServer, CookieServer, CallbackServer
from .service import Upstart, InitD
from .client import Command, ModuleCommand, FileCommand, HTTP
from .test import TestCase


__version__ = '0.7.8'


# get rid of "No handler found" warnings (cribbed from requests)
logging.getLogger(__name__).addHandler(logging.NullHandler())


def basic_logging(**kwargs):
    """Lots of times, in tests, I have to add a basic logger, it's basically the
    same code over and over again, this will just make that a little easier to do

    :example:
        import testdata
        testdata.basic_logging() # near top of file

    this basically does this:
        import sys, logging
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)
        log_handler = logging.StreamHandler(stream=sys.stderr)
        log_formatter = logging.Formatter('[%(levelname).1s] %(message)s')
        log_handler.setFormatter(log_formatter)
        logger.addHandler(log_handler)

    :param **kwargs: key/val, these will be passed into logger.basicConfig method
    """
    levels = kwargs.pop("levels", [])

    # configure root logger
    kwargs.setdefault("format", "[%(levelname).1s] %(message)s")
    kwargs.setdefault("level", logging.DEBUG)
    kwargs.setdefault("stream", sys.stdout)
    logging.basicConfig(**kwargs)

    # configure certain loggers
    # https://github.com/Jaymon/testdata/issues/34
    for logger_name, logger_level in levels:
        l = logging.getLogger(logger_name)
        l.setLevel(getattr(logging, logger_level))

#     rlogger = logging.getLogger()
#     if not rlogger.handlers:
#         rlogger.setLevel(kwargs["level"])
#         handler = logging.StreamHandler(stream=kwargs["stream"])
#         formatter = logging.Formatter(kwargs["format"])
#         handler.setFormatter(formatter)
#         rlogger.addHandler(handler)


@contextmanager
def environment(thing=None, **kwargs):
    """Context manager to change the os.environ to something else for the life of
    the with statement

    :Example:
        with testdata.environ("FOO"="bar"):
            print(os.environ["FOO"]) # bar

        print(os.environ["FOO"]) # keyError

    :param **kwargs: key is the environment variable name and value is the value
    """
    normalize_value = lambda v: v
    if thing is None:
        thing = os.environ
        normalize_value = lambda v: String(v)

    def has_key(thing, k):
        if isinstance(thing, Mapping):
            ret = k in thing
        else:
            ret = hasattr(thing, k)
        return ret

    def set_key(thing, k, v):
        if isinstance(thing, Mapping):
            thing[k] = v
        else:
            setattr(thing, k, v)

    def get_key(thing, k):
        if isinstance(thing, Mapping):
            ret = thing[k]
        else:
            ret = getattr(thing, k)
        return ret

    def del_key(thing, k):
        if isinstance(thing, Mapping):
            thing.pop(k)
        else:
            delattr(thing, k)

    originals = {}
    try:
        for k, v in kwargs.items():
            if has_key(thing, k):
                originals[k] = get_key(thing, k)

            set_key(thing, k, normalize_value(v))

        yield originals

    finally:
        for k, v in kwargs.items():
            if k in originals:
                set_key(thing, k, originals[k])
            else:
                del_key(thing, k)
modify = environment
change = environment
configure = environment


def start_service(service_name, ignore_failure=True):
    """start a local service

    :param service_name: string, the service you want to start
    :param ignore_failure: bool, True if it should ignore a failure return code
    :returns: Service instance
    """
    for service_class in [Upstart, InitD]:
        s = service_class(service_name)
        s.ignore_failure = ignore_failure
        if s.exists():
            s.start()
            break
        else:
            s = None

    if s is None:
        raise RuntimeError("Could not find a valid service for {}".format(service_name))

    return s


def stop_service(service_name, ignore_failure=True):
    """stop a local service

    :param service_name: string, the service you want to stop
    :param ignore_failure: bool, True if it should ignore a failure return code
    :returns: Service instance
    """
    for service_class in [Upstart, InitD]:
        s = service_class(service_name)
        s.ignore_failure = ignore_failure
        if s.exists():
            s.stop()
            break
        else:
            s = None

    if s is None:
        raise RuntimeError("Could not find a valid service for {}".format(service_name))

    return s


def capture(*args, **kwargs):
    """Capture stdout and stderr so you can inspect it

    this is handy for tests when you are trying to figure out if logging or whatnot
    is doing the correct thing

    I'd always wanted something similar to php's output buffering ob_start() method
    http://www.php.net/manual/en/function.ob-start.php

    :example:
        with testdata.capture() as c:
            print("foo")
        if "foo" in c:
            print("foo was captured")
    """
    c = Capture()
    return c(*args, **kwargs)


def yes(specifier=0):
    """
    Decide if we should perform this action, this is just a simple way to do something
    I do in tests every now and again

    example -- simple yes or no question

        if testdata.yes():
            # do this
        else:
            # don't do it

    example -- multiple choice

        choice = testdata.yes(3)
        if choice == 1:
            # do the first thing
        elif choice == 2:
            # do the second thing
        else:
            # do the third thing

    example -- do something 75% of the time

        if testdata.yes(0.75):
            # do it the majority of the time
        else:
            # but every once in a while don't do it

    https://github.com/Jaymon/testdata/issues/8
    """
    if specifier:
        if isinstance(specifier, int):
            choice = random.randint(1, specifier)

        else:
            if specifier > 1.0:
                specifier *= 100.0

            specifier = int(specifier)
            x = random.randint(0, 100)
            choice = 1 if x <= specifier else 0

    else:
        choice = random.choice([0, 1])

    return choice


def wait(callback, cb_args=None, cb_kwargs=None, timeout=30.0, interval=0.1): 
    """
    keep running callback(*cb_args, **cb_kwargs) until it returns True or timeout is
    reached

    :param callback: callable, the function to call, should return True/False
    :param cb_args: list, any callback arguments
    :param cb_kwargs: dict, any callback keyword arguments
    :param timeout: float, how long you should wait before failing with RuntimeError
    :param interval: float, sleep for this interval inbetween callback calls
    """
    if cb_args is None:
        cb_args = []
    else:
        if not isinstance(cb_args, list):
            cb_args = [cb_args]
    if not cb_kwargs: cb_kwargs = {}
    start = time.time()
    while not callback(*cb_args, **cb_kwargs):
        sleep(interval)
        if timeout:
            stop = time.time()
            if (stop - start) >= timeout:
                raise RuntimeError("wait() timed out after {} seconds".format(timeout))


def choice(*args):
    """Wrapper around random.choice that makes sure everything is a list, handy
    for python 3 code where you have to wrap a lot of generators in list(...)

    :param *args: iter(s), one or more iterators or lists that will all be combined
        into one giant list
    :returns: a single object from all the *args
    """
    vals = []
    for arg in args:
        vals.extend(arg)
    return random.choice(vals)


def get_bool():
    """Returns either True or False randomly"""
    return random.choice([True, False])


def run(cmd, arg_str="", **kwargs):
    """Run a command on the command line

    :param cmd: mixed, the command you want to run
    :param arg_str: string, extra flags that will be appended to the cmd
    :param **kwargs: allows you to pass into underlying Command.run() method
    :returns: string, the output from the command
    """
    if isinstance(cmd, Modulepath):
        ret = cmd.run(arg_str, **kwargs)

    elif isinstance(cmd, Filepath):
        ret = cmd.run(arg_str, **kwargs)

    else:
        cmd = Command(cmd)
        ret = cmd.run(arg_str, **kwargs)

    return ret


def fetch(url, body=None, query=None, **kwargs):
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


def create_fileserver(file_dict, tmpdir="", hostname="", port=0, encoding=""):
    """
    create a fileserver that can be used to test remote file retrieval

    :param file_dict: dict|list|str, same as create_files
    :param tmpdir: str, same as create_files
    :param hostname: str, usually leave this alone and it will use localhost
    :param port: int, the port you want to use
    """
    if isinstance(file_dict, Sequence):
        file_dict = {
            "index.html": file_dict
        }

    path = create_files(file_dict, tmpdir=tmpdir, encoding=encoding)
    return PathServer(path, hostname=hostname, port=port, encoding=encoding)


def create_cookieserver(cookies, hostname="", port=0):
    """
    create a fileserver that can be used to test remote file retrieval

    :param cookies: a dict of name: val or a list ot tuples(name, val)
    :param hostname: str, usually leave this alone and it will use localhost
    :param port: int, the port you want to use
    """
    return CookieServer(cookies, hostname=hostname, port=port)


def get_contents(fileroot, basedir="", encoding=""):
    """Returns the contents of a file matching basedir/fileroot.*

    :param fileroot: string, can be a basename (fileroot.ext) or just a file root, 
        in which case basedir/fileroot.* will be searched for and first file matched
        will be used
    :param basedir: string, the directory to search for fileroot.*, if not passed
        in then os.getcwd()/*/testdata will be searched for
    :returns: string, the contents of the found file
    """
    if encoding:
        return ContentString(fileroot, basedir=basedir, encoding=encoding)
    else:
        return ContentBytes(fileroot, basedir=basedir)
get_content = get_contents


def create_dir(path="", tmpdir=""):
    '''
    create a directory path using a tempdir as the root

    so, if you pass in "/foo/bar" that will be combined with a tempdir, so you end 
    up with the final path: /tmp/python/dir/foo/bar

    :param path: string, the temp dir path
    :param tmpdir: string, the temp directory to use as the base
    :returns: Dirpath, the full directory path
    '''
    return Dirpath.create_instance(path, tmpdir)
create_directory = create_dir
create_d = create_dir


def get_dir(path):
    """
    return a directory path

    :param path: string, the path to a real directory
    :returns: Dirpath, the path wrapped with all the Dirpath functionality
    """
    return Dirpath.get_instance(path)
get_directory = get_dir
get_d = get_dir


def create_file(path="", contents="", tmpdir="", encoding=""):
    '''
    create a file and return the full path to that file

    :param path: string, the path to the file
    :param contents: string, the file contents
    :param tmpdir: string, the temp directory to use as the base
    :param encoding: string, whatever encoding you want the file to have

    :returns: Filepath, the full file path
    '''
    if not path:
        path = get_module_name(prefix="cf")

    instance = Filepath.create_instance(path, contents, tmpdir, encoding)

    if encoding:
        instance = Filepath(path, tmpdir)
        instance.encoding = encoding
        instance.create(contents)
    else:
        instance = Filepath.create_instance(path, contents, tmpdir, encoding)
    return instance
create_f = create_file


def create_files(file_dict, tmpdir="", encoding=""):
    """
    create a whole bunch of files all at once

    file_dict -- dict -- keys are the filepath relative to tmpdir, values are the
        file contents
    tmpdir -- Dirpath -- same as create_module() tmpdir
    """
    base_dir = Dirpath(basedir=tmpdir)
    base_dir.create_files(file_dict, encoding)
    return base_dir
create_fs = create_files


def get_file(path="", tmpdir="", encoding=""):
    if not path:
        path = get_ascii()

    return Filepath(path, tmpdir, encoding)
get_f = get_file


def get_filename(ext="", prefix=""):
    """return a file name

    :param ext: the extension you want the file to have
    :param prefix: this will be the first part of the file's name
    :returns: the random filename
    """
    if ext and not ext.startswith("."):
        ext = "." + ext
    return get_module_name(prefix=prefix, postfix=ext)
get_file_name = get_filename


def get_module_name(bits=1, prefix="", postfix=""):
    """Returns a module name or module path

    :param bits: how many parts you want in your module path (1 is foo, 2 is foo.bar, etc)
    :param prefix: if you want the last bit to be prefixed with something
    :param postfix: if you want the last bit to be posfixed with something (eg, ".py")
    :returns: the modulepath
    """
    parts = []
    bits = max(bits, 1)

    for x in range(bits):
        parts.append(get_str(str_size=8, chars=string.ascii_letters).lower())

    if prefix:
        parts[-1] = "{}{}".format(prefix, parts[-1])

    if postfix:
        parts[-1] = "{}{}".format(parts[-1], postfix)

    return ".".join(parts)
get_package_name = get_module_name


def create_module(module_name="", contents="", tmpdir="", make_importable=True):
    '''
    create a python module folder structure so that the module can be imported

    module_name -- string -- something like foo.bar
    contents -- string -- the contents of the module
    tmpdir -- string -- the temp directory that will be added to the syspath if make_importable is True
    make_importable -- boolean -- if True, then tmpdir will be added to the python path so it can be imported

    return -- Module -- the module file path
    '''
    if not module_name:
        module_name = get_module_name(prefix="cm")
    return Modulepath.create_instance(module_name, contents, tmpdir, make_importable)


def create_modules(module_dict, tmpdir="", make_importable=True, prefix=""):
    """
    create a whole bunch of modules all at once

    :param module_dict: dict, keys are the module_name, values are the module contents
    :param tmpdir: string, same as create_module() tmpdir
    :param make_importable: boolean, same as create_module() tmpdir
    :param prefix: string, if you want all the modules in module_dict to have a prefix, you
        can pass this in, so if you did prefix is "foo.bar" then all the keys in module_dict
        will be prepended with "foo.bar"
    :returns: Dirpath
    """
    module_base_dir = Dirpath(basedir=tmpdir)

    if prefix:
        ks = list(module_dict.keys()) # we cast to list to make sure ks doesn't grow
        for k in ks:
            module_dict[".".join(filter(None, [prefix, k]))] = module_dict.pop(k)

    for module_name, contents in module_dict.items():
        Modulepath.create_instance(module_name, contents, module_base_dir, make_importable)
        make_importable = False

    return module_base_dir


def create_package(module_name="", contents="", tmpdir="", make_importable=True):
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
    if not module_name:
        module_name = get_module_name(prefix="cp")

    return Modulepath.create_instance(
        module_name,
        contents,
        tmpdir,
        make_importable,
        is_package=True
    )


def get_url():
    '''
    get a url, this is just a nice shortcut method to something I seemed to do a lot

    return -- unicode
    '''
    return 'http{}://{}.com'.format(
        's' if random.choice([True, False]) else '',
        get_ascii()
    )


def get_str(str_size=0, chars=None):
    '''
    generate a random unicode string

    if chars is None, this can generate up to a 4-byte utf-8 unicode string, which can
    break legacy utf-8 things

    str_size -- integer -- how long you want the string to be
    chars -- sequence -- the characters you want the string to use, if this is None, it
        will default to pretty much the entire unicode range of characters
    return -- unicode
    '''
    if str_size == 0:
        str_size = random.randint(3, 20)

    sg = None

    if chars is None:
        # chars can be any range in unicode (based off of table 3.7 of Unicode 6.2.0
        # pg 42 - http://www.unicode.org/versions/Unicode6.2.0/ch03.pdf
        # via: http://stackoverflow.com/questions/1477294/generate-random-utf-8-string-in-python
        byte_range = lambda first, last: range(first, last+1)
        first_values = list(byte_range(0x00, 0x7F)) + list(byte_range(0xC2, 0xF4))
        trailing_values = list(byte_range(0x80, 0xBF))

        def random_utf8_seq():
            while True:
                first = random.choice(first_values)
                if first <= 0x7F: # U+0000...U+007F
                    return bytearray([first])
                elif (first >= 0xC2) and (first <= 0xDF): # U+0080...U+07FF
                    return bytearray([first, random.choice(trailing_values)])
                elif first == 0xE0: # U+0800...U+0FFF
                    return bytearray([first, random.choice(byte_range(0xA0, 0xBF)), random.choice(trailing_values)])
                elif (first >= 0xE1) and (first <= 0xEC): # U+1000...U+CFFF
                    return bytearray([first, random.choice(trailing_values), random.choice(trailing_values)])
                elif first == 0xED: # U+D000...U+D7FF
                    return bytearray([first, random.choice(byte_range(0x80, 0x9F)), random.choice(trailing_values)])
                elif (first >= 0xEE) and (first <= 0xEF): # U+E000...U+FFFF
                    return bytearray([first, random.choice(trailing_values), random.choice(trailing_values)])
                else:
                    if sys.maxunicode > 65535:
                        if first == 0xF0: # U+10000...U+3FFFF
                            return bytearray(
                                [
                                    first,
                                    random.choice(byte_range(0x90, 0xBF)),
                                    random.choice(trailing_values),
                                    random.choice(trailing_values)
                                ]
                            )
                        elif (first >= 0xF1) and (first <= 0xF3): # U+40000...U+FFFFF
                            return bytearray(
                                [
                                    first,
                                    random.choice(trailing_values),
                                    random.choice(trailing_values),
                                    random.choice(trailing_values)
                                ]
                            )
                        elif first == 0xF4: # U+100000...U+10FFFF
                            return bytearray(
                                [
                                    first,
                                    random.choice(byte_range(0x80, 0x8F)),
                                    random.choice(trailing_values),
                                    random.choice(trailing_values)
                                ]
                            )

        sg = (random_utf8_seq().decode('utf-8') for c in range(str_size))

    else:
        # we have a defined set of chars
        sg = (random.choice(chars) for c in range(str_size))

    s = ''.join(sg)
    return s
get_unicode = get_str
get_string = get_str


def get_hex(str_size=0):
    '''
    generate a string of just hex characters

    str_size -- integer -- how long you want the string to be
    return -- unicode
    '''
    return get_str(str_size=str_size, chars=string.hexdigits.lower())


def get_ascii(str_size=0):
    '''
    generate a random string full of just ascii characters

    str_size -- integer -- how long you want the string to be
    return -- unicode
    '''
    chars=string.ascii_letters + string.digits
    return get_str(str_size=str_size, chars=chars)
get_ascii_str = get_ascii
get_ascii_string = get_ascii
get_alphanum = get_ascii
get_alphanum_str = get_ascii
get_alphanum_string = get_ascii
get_alphanumeric = get_ascii
get_alphanumeric_str = get_ascii
get_alphanumeric_string = get_ascii


def get_hash(str_size=32):
    """Returns a random hash, if you want an md5 use get_md5(), if you want an
    uuid use get_uuid()"""
    return get_ascii(str_size)


def get_md5(val=""):
    """Return an md5 hash of val, if no val then return a random md5 hash

    :param val: string, the value you want to md5 hash
    :returns: string, the md5 hash as a 32 char hex string
    """
    if not val:
        val = get_uuid()

    ret = ""
    if is_py2:
        ret = hashlib.md5(str(val)).hexdigest()
    else:
        if getattr(val, "encode", None):
            ret = hashlib.md5(val.encode("utf-8")).hexdigest()
        else:
            ret = hashlib.md5(val).hexdigest()

    return ret


def get_uuid():
    """Generate a random UUID"""
    return str(uuid.uuid4())
    # 3088D703-6AD0-4D62-B0D3-0FF824A707F5
#     return '{}-{}-{}-{}-{}'.format(
#         get_ascii(8).upper(),
#         get_ascii(4).upper(),
#         get_ascii(4).upper(),
#         get_ascii(4).upper(),
#         get_ascii(12).upper()
#     )


def get_float(min_size=None, max_size=None):
    """return a random float

    sames as the random method but automatically sets min and max

    :param min_size: float, the minimum float size you want
    :param max_size: float, the maximum float size you want
    :returns: float, a random value between min_size and max_size
    """
    float_info = sys.float_info
    if min_size is None:
        min_size = float_info.min
    if max_size is None:
        max_size = float_info.max
    return random.uniform(min_size, max_size)


def get_posfloat(max_size=None):
    """Similar to get_float but the random float will always be positive

    :param max_size: float, the maximum float size
    :returns: float, a random float between 0.0 and max_size
    """
    return get_float(0.0, max_size)
get_positive_float = get_posfloat
get_positivefloat = get_posfloat


def get_unique_float(min_size=None, max_size=None):
    '''
    get a random unique float

    no different than random.uniform() except it automatically can set range, and
    guarrantees that no 2 floats are the same

    return -- float
    '''
    global _previous_floats

    i = 0;
    while True:
        i = get_float(min_size, max_size)
        if i not in _previous_floats:
            _previous_floats.add(i)
            # we cap the list at 100000 unique values
            if len(_previous_floats) > environ.MAX_UNIQUE:
                _previous_floats.pop()
            break

    return i
get_uniq_float = get_unique_float


def get_posint(max_size=2**31-1):
    """
    just return a positive 32-bit integer, this is basically a wrapper around
    random.randint where you don't have to specify a minimum (or a maximum if you
    don't want)
    """
    min_size = 1
    return random.randint(min_size, max_size)
get_positive_int = get_posint
get_positive_integer = get_posint
get_posinteger = get_posint


def get_int(min_size=1, max_size=sys.maxsize):
    return random.randint(min_size, max_size)
get_integer=get_int


def get_int32(min_size=1):
    """returns a 32-bit positive integer"""
    return random.randint(min_size, 2**31-1)
get_integer32=get_int32


def get_int64(min_size=1):
    """returns up to a 64-bit positive integer"""
    return random.randint(min_size, 2**63-1)
get_integer64=get_int64


def get_unique_int(min_size=1, max_size=sys.maxsize):
    '''
    get a random unique integer

    no different than random.randint except that it guarrantees no int will be
    the same, and also you don't have to set a range, it will default to all max
    int size

    return -- integer 
    '''
    global _previous_ints

    i = 0;
    found = False
    max_count = max_size - min_size
    for x in range(max_count):
        i = random.randint(min_size, max_size)
        if i not in _previous_ints:
            found = True
            _previous_ints.add(i)
            # we cap the list at 100000 unique values
            if len(_previous_ints) > environ.MAX_UNIQUE:
                _previous_ints.pop()
            break

    if not found:
        raise ValueError("no unique ints from {} to {} could be found".format(min_size, max_size))
    return i
get_uniq_int = get_unique_int
get_uniq_integer = get_unique_int
get_unique_integer = get_unique_int


def get_ascii_words(word_count=0, as_str=True):
    return get_words(word_count, as_str, words=_ascii_words)


def get_ascii_word():
    return get_words(1, as_str=True, words=_ascii_words)


def get_unicode_words(word_count=0, as_str=True):
    return get_words(word_count, as_str, words=_unicode_words)
get_uni_words = get_unicode_words


def get_unicode_word():
    return get_words(1, as_str=True, words=_unicode_words)
get_uni_word = get_unicode_word



def get_words(word_count=0, as_str=True, words=None):
    '''
    get some amount of random words

    word_count -- integer -- how many words you want, 0 means a random amount (at most 20)
    as_str -- boolean -- True to return as string, false to return as list of words
    words -- list -- a list of words to choose from, defaults to unicode + ascii words

    return -- unicode|list -- your requested words
    '''

    # since we specified we didn't care, randomly choose how many surnames there should be
    if word_count == 0:
        word_count = random.randint(1, 20)

    if not words:
        words = _words

    ret_words = random.sample(words, word_count)
    return ret_words if not as_str else ' '.join(ret_words)


def get_word(words=None):
    return get_words(1, as_str=True, words=words)


def get_username(name=""):
    """Returns just a non-space ascii name, this is a very basic username generator"""
    if not name:
        name = get_ascii_first_name() if yes() else get_ascii_last_name()
    name = re.sub(r"['-]", "", name)
    return name


def get_unique_email(name=''):
    name = get_username(name)
    timestamp = "{:.6f}".format(time.time()).replace(".", "")
    return get_email(name + timestamp)
get_uniq_email = get_unique_email


def get_email(name=''):
    '''return a random email address'''
    name = get_username(name)
    email_domains = [
        "yahoo.com",
        "hotmail.com",
        "outlook.com",
        "aol.com",
        "gmail.com",
        "msn.com",
        "comcast.net",
        "hotmail.co.uk",
        "sbcglobal.net",
        "yahoo.co.uk",
        "yahoo.co.in",
        "bellsouth.net",
        "verizon.com",
        "earthlink.net",
        "cox.net",
        "rediffmail.com",
        "yahoo.ca",
        "btinternet.com",
        "charter.net",
        "shaw.ca",
        "ntlworld.com",
        "gmx.com",
        "gmx.net",
        "mail.com",
        "mailinator.com"
    ]

    return '{}@{}'.format(name.lower(), random.choice(email_domains))


def get_name(name_count=2, as_str=True, is_unicode=None):
    '''
    get a random name

    link -- http://stackoverflow.com/questions/30485/what-is-a-reasonable-length-limit-on-person-name-fields

    name_count -- integer -- how many total name parts you want (eg, "Jay marcyes" = 2 name_count)
    as_str -- boolean -- True to return as string, false to return as list of names

    return -- unicode|list -- your requested name
    '''
    # since we specified we didn't care, randomly choose how many surnames there should be
    if name_count <= 0:
        name_count = random.randint(1, 5)

    is_unicode_bit = lambda x: random.randint(0, 100) < 20 if x is None else x

    # decide if we should hyphenate the last name
    names = []
    if name_count > 0:
        #names = random.sample(_names, name_count)
        add_last_name = name_count > 1
        for x in range(max(1, name_count - 1)):

            if is_unicode_bit(is_unicode):
                names.append(get_unicode_first_name())
            else:
                names.append(get_ascii_first_name())

        if add_last_name:
            if is_unicode_bit(is_unicode):
                names.append(get_unicode_last_name())
            else:
                names.append(get_ascii_last_name())

    return names if not as_str else ' '.join(names)


def get_ascii_name():
    '''return one ascii safe name'''
    return get_name(is_unicode=False)


def get_unicode_name():
    '''return one non-ascii safe name'''
    return get_name(is_unicode=True)
get_uni_name = get_unicode_name


def get_first_name(gender="", is_unicode=None):
    genders = ["m", "f"]
    if gender:
        gender = str(gender).lower()[0]
        gender = "m" if gender == "1" else "f"
        gender = "m" if gender == "t" else "f"
        if gender not in genders:
            raise ValueError("Unsupported gender, try [m, f, male, female] instead")
    else:
        gender = random.choice(genders)

    if is_unicode is None:
        is_unicode = random.randint(0, 100) < 20

    if is_unicode:
        name = random.choice(_unicode_names)
    else:
        if gender == "m":
            name = random.choice(_first_names_male)
        else:
            name = random.choice(_first_names_female)

    if random.randint(0, 20) == 5:
        name = '{}-{}'.format(name, get_first_name(gender, is_unicode))

    return name.capitalize()
get_given_name = get_first_name
get_firstname = get_first_name


def get_ascii_first_name(gender=""):
    '''return one ascii safe name'''
    return get_first_name(gender, is_unicode=False)
get_ascii_given_name = get_ascii_first_name
get_ascii_firstname = get_ascii_first_name


def get_unicode_first_name(gender=""):
    '''return one non-ascii name'''
    return get_first_name(gender, is_unicode=True)
get_uni_first_name = get_unicode_first_name
get_unicode_given_name = get_unicode_first_name
get_unicode_firstname = get_unicode_first_name


def get_last_name(is_unicode=None):
    if is_unicode is None:
        is_unicode = random.randint(0, 100) < 20

    if is_unicode:
        name = random.choice(_unicode_names)
    else:
        name = random.choice(_last_names)

    if random.randint(0, 20) == 5:
        name = '{}-{}'.format(name, get_last_name(is_unicode))

    return name.capitalize()
get_surname = get_last_name


def get_ascii_last_name():
    '''return one ascii safe name'''
    return get_last_name(is_unicode=False)
get_ascii_lastname = get_ascii_last_name
get_ascii_surname = get_ascii_last_name


def get_unicode_last_name():
    '''return one unicode name'''
    return get_last_name(is_unicode=True)
get_uni_last_name = get_unicode_last_name
get_unicode_lastname = get_unicode_last_name
get_unicode_surname = get_unicode_last_name


def get_coordinate(v1, v2, round_to=7):
    '''
    this will get a random coordinate between the values v1 and v2

    handy for doing geo stuff where you want to make sure you have a coordinate within
    N miles of a central coordinate so you can make your tests repeatable

    v1 -- float -- the first coordinate
    v2 -- float -- the second coordinate

    return -- float -- a value between v1 and v2
    '''
    v1 = [int(x) for x in str(round(v1, round_to)).split('.')]
    v2 = [int(x) for x in str(round(v2, round_to)).split('.')]
    scale_max = int('9' * round_to)

    min = v1
    max = v2
    if v1[0] > v2[0]:
      min = v2
      max = v1

    min_size = min[0]
    min_scale_range = [min[1], scale_max]

    max_size = max[0]
    max_scale_range = [0, max[1]]

    scale = 0
    size = random.randint(min_size, max_size)

    if size == min_size:
      scale = random.randint(min_scale_range[0], min_scale_range[1])
    elif size == max_size:
        # if you get a random value from 0 to say 23456, you might get 9070, which is
        # less than 23456, but when put into a float it would be: N.9070, which is bigger
        # than the passed in v2 float, the following code avoids that problem
        left_zero_count = random.randint(0, round_to)
        if left_zero_count == round_to:
            scale = '0' * round_to
        elif left_zero_count > 0:
            scale = int(str(scale_max)[left_zero_count:])
            scale = str(random.randint(max_scale_range[0], scale)).zfill(round_to)
        else:
            scale = random.randint(int('1' + ('0' * (round_to - 1))), max_scale_range[1])
    else:
      scale = random.randint(0, scale_max)

    return float('{}.{}'.format(size, scale))
get_coord = get_coordinate


def patch_instance(mod, patches=None, **kwargs_patches):
    if not mod:
        raise ValueError("mod is empty")

    if not patches: patches = {}
    patches.update(kwargs_patches) # combine both dicts

    for name, patch in patches.items():
        val = getattr(mod, name, None)
        if inspect.isroutine(val):
            setattr(mod, name, types.MethodType(patch, mod))

        else:
            if name in mod.__class__.__dict__ and inspect.isdatadescriptor(mod.__class__.__dict__[name]):

                # http://stackoverflow.com/questions/30342212/override-attribute-access-precedence-having-a-data-descriptor/30578922#30578922
                monkey_class = patch_class(
                    mod.__class__,
                    **{name: patch}
                )
                mod.__class__ = monkey_class

            else:
                setattr(mod, name, patch)

    return mod


def patch_class(mod, patches=None, **kwargs_patches):
    if not mod:
        raise ValueError("mod is empty")

    if not patches: patches = {}
    patches.update(kwargs_patches) # combine both dicts

    def copy_dict(mod):
        d = {}
        for k, v in mod.__dict__.items():
            if k.startswith("__"):
                d[k] = v
            else:
                if inspect.isroutine(v):
                    d[k] = v

                elif inspect.isdatadescriptor(v):
                    d[k] = v

                else:
                    d[k] = copy.deepcopy(v)
        return d

    class_name = ""
    if is_py2:
        class_name = b'{}Patched'.format(mod.__name__)
    elif is_py3:
        class_name = '{}Patched'.format(mod.__name__)

    # http://stackoverflow.com/questions/9541025/how-to-copy-a-python-class
    mod_patched = type(
        class_name,
        mod.__bases__,
        #{k: copy.deepcopy(v) for k, v in mod.__dict__.items()}
        copy_dict(mod)
    )
    for name, patch in patches.items():
        setattr(mod_patched, name, patch)

    return mod_patched


def patch_module(mod, patches=None, **kwargs_patches):
    if not mod:
        raise ValueError("mod is empty")

    if not patches: patches = {}
    patches.update(kwargs_patches) # combine both dicts

    deferred_patches = []
    patched_modules = {}

    for name, patch in patches.items():
        if '.' in name:
            # when a module is imported like this, import foo.bar then it is placed
            # as an attribute to the parent module: getattr(getattr(mod, 'foo'), 'bar')
            # this should be useful in eventually supporting this, you can work down the sub
            # attributes and newly import them and patch
            raise RuntimeError("nested modules, eg, {} are not currently supported".format(name))

        else:
            deferred_patches.append((name, patch))

    # now we need to find the full module path so we can reload it
    if inspect.ismodule(mod):
        mod_name = mod.__name__
        mpath = inspect.getsourcefile(mod)
        mfile = mpath

    else:
        mod_name = mod

        # http://stackoverflow.com/questions/4907054/
        def find_mod_path(p):
            if '.' in p:
                p, m = p.rsplit('.', 1)
                imod_path = find_mod_path(p)
                mod_path = os.path.join(imod_path, m)
                #mod = imp.load_module('{}_{}'.format(m, get_ascii(8)), *imp.find_module(m, imod.__path__))

            else:
                # we fudge the paths a bit to make sure current working directory is
                # also checked
                paths = [os.getcwd()]
                paths.extend(sys.path)
                _, mod_path, _ = imp.find_module(p, paths)

            return mod_path

        mpath = find_mod_path(mod_name)

        mfile = mpath
        # figure out if we have a package or a module and set the appropriate file
        if os.path.isdir(mpath):
            mfile = os.path.join(mpath, '__init__.py')

        else:
            if not mfile.endswith(".py"):
                mfile = '{}.py'.format(mpath)

    m = imp.load_source('{}_{}'.format(mod_name, get_ascii(8)), mfile)

    # go through and apply all the patches
    for patch_name, patch in deferred_patches:
        setattr(m, patch_name, patch)

    return m


def patch(mod, patches=None, **kwargs_patches):
    '''
    import module_name and apply the patches to it

    mod -- string|module|class|instance -- the name of the thing you are patching
    patches -- dict -- the keys are functions, classes, or modules that should be
    patched in the module, the value is the patched value you want to replace the
    key with

    return -- module|object -- if you pass in an object, return the object, otherwise
        return the module
    '''
    if isinstance(mod, basestring):
        m = patch_module(mod, patches=patches, **kwargs_patches)

    elif inspect.ismodule(mod):
        m = patch_module(mod, patches=patches, **kwargs_patches)

    elif inspect.isclass(mod):
        m = patch_class(mod, patches=patches, **kwargs_patches)

    else:
        m = patch_instance(mod, patches=patches, **kwargs_patches) 

    return m


def get_birthday(as_str=False, start_age=18, stop_age=100):
    """
    return a random YYYY-MM-DD

    :param as_str: boolean, true to return the bday as a YYYY-MM-DD string
    :param start_age: int, minimum age of the birthday date
    :param stop_age: int, maximum age of the birthday date
    :returns: datetime.date|string
    """
    age = random.randint(start_age, stop_age)
    year = (datetime.datetime.utcnow() - datetime.timedelta(weeks=(age * 52))).year
    month = random.randint(1, 12)
    if month == 2:
        day = random.randint(1, 28)
    elif month in [9, 4, 6, 11]:
        day = random.randint(1, 30)
    else:
        day = random.randint(1, 31)

    bday = datetime.date(year, month, day)
    if as_str:
        bday = "{:%Y-%m-%d}".format(bday)

    return bday
get_bday = get_birthday


def get_past_datetime(now=None):
    """return a datetime guaranteed to be in the past from now"""
    if not now: now = datetime.datetime.utcnow()
    if isinstance(now, datetime.timedelta):
        now = datetime.datetime.utcnow() - now

    td = now - datetime.datetime(year=2000, month=1, day=1)
    return now - datetime.timedelta(
        days=random.randint(1, max(td.days, 1)),
        seconds=random.randint(1, max(td.seconds, 1))
    )
get_past_dt = get_past_datetime
get_passed_datetime = get_past_datetime
get_before_datetime = get_past_datetime


def get_future_datetime(now=None):
    """return a datetime guaranteed to be in the future from now"""
    if not now: now = datetime.datetime.utcnow()
    if isinstance(now, datetime.timedelta):
        now = datetime.datetime.utcnow() + now

    return now + datetime.timedelta(
        weeks=random.randint(1, 52 * 50),
        hours=random.randint(0, 24),
        days=random.randint(0, 365),
        seconds=random.randint(0, 86400)
    )
get_future_dt = get_future_datetime
get_after_dt = get_future_datetime


def get_between_datetime(start, stop=None):
    """get a datetime between start and stop

    return a datetime guaranteed to be in the future from start and in the past from stop
    """
    if not stop:
        stop = datetime.datetime.utcnow()

    # account for start or stop being a timedelta
    if isinstance(start, datetime.timedelta) and isinstance(stop, datetime.timedelta):
        now = datetime.datetime.utcnow()
        start = now - start
        stop = now - stop

    elif isinstance(start, datetime.timedelta):
        start = stop - start

    elif isinstance(stop, datetime.timedelta):
        stop = start + stop

    if start >= stop:
        raise ValueError("start datetime >= stop datetime")

    td = stop - start

    kwargs = {}
    if td.days > 0:
        kwargs["days"] = random.randint(0, td.days)

    if td.seconds - 1 > 0:
        kwargs["seconds"] = random.randint(0, td.seconds - 1)

    if td.microseconds - 1 > 0:
        kwargs["microseconds"] = random.randint(0, td.microseconds - 1)

    return start + datetime.timedelta(**kwargs)
get_between_dt = get_between_datetime


# used in the get_unique_int() function to make sure it never returns the same int twice
# this is a possible memory leak if you are using this script in a very long running
# process using get_int(), since this list will get bigger and bigger and never
# be flushed, but seriously, you should just use get_int() or random.randint() in any
# long running scripts. In order to minimize the memory leak we cap the list at
# environ.MAX_UNIQUE unique values
_previous_ints = set()

# similar to _previous_ints, used in get_unique_float() function
_previous_floats = set()


