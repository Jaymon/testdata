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
from collections import deque, namedtuple
import types
import inspect
import copy
import uuid
import hashlib
import logging
import time
from time import sleep
from contextlib import contextmanager
import pkgutil
import itertools

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
    _last_names,
    usa,
)

from . import environ
from .threading import Thread, Tail
from .output import Capture
from .client import Command, ModuleCommand, FileCommand, HTTP
from .test import (
    TestCase,
    skip,
    SkipTest,
    skipIf,
    skipUnless,
    expectedFailure,
    skip_if,
    skip_unless,
    expected_failure,
    expect_failure,
)
from .path import *
from .service import *
from .mock import *
from .server import *


__version__ = '4.0.1'


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


def capture(stdout=True, stderr=True, loggers=True, *args, **kwargs):
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

    :param stdout: capture stdout streams
    :param stderr: capture stderr streams
    :param loggers: capture stdout and stderr streams of loggers
    :returns: output.Capture instance
    """
    c = Capture(stdout=stdout, stderr=stderr, loggers=loggers)
    return c(*args, **kwargs)


def tail(path, stream=None, encoding="UTF-8", **kwargs):
    """Tail/follow path in a separate thread

    :Example:
        testdata.tail("/path/to/tail")

    :param path: string, the path of the file you want to tail/follow
    :param stream: io.IOBase, a file object with a write method
    :param encoding: string, the encoding of lines
    :param **kwargs:
        prefix -- by default prefix is the path basename, but you can set
            something custom here
    """

    t = Tail(path, stream, encoding, **kwargs)
    t.start()
    return t


def yes(specifier=0):
    """
    Decide if we should perform this action, this is just a simple way to do something
    I do in tests every now and again

    :Example:
        # EXAMPLE -- simple yes or no question
        if testdata.yes():
            # do this
        else:
            # don't do it

        # EXAMPLE -- multiple choice
        choice = testdata.yes(3)
        if choice == 1:
            # do the first thing
        elif choice == 2:
            # do the second thing
        else:
            # do the third thing

        # EXAMPLE -- do something 75% of the time
        if testdata.yes(0.75):
            # do it the majority of the time
        else:
            # but every once in a while don't do it

    https://github.com/Jaymon/testdata/issues/8

    :param specifier: int|float, if int, return a value between 1 and specifier.
        if float, return 1 approximately specifier percent of the time, return 0
        100% - specifier percent of the time
    :returns: integer, usually 1 (True) or 0 (False)
    """
    if specifier:
        if isinstance(specifier, int):
            choice = random.randint(1, specifier)

        else:
            if specifier < 1.0:
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


def choice(*args, **kwargs):
    """Wrapper around random.choice that makes sure everything is a list, handy
    for python 3 code where you have to wrap a lot of generators in list(...)

    :param *args: iter(s), one or more iterators or lists that will all be combined
        into one giant list
    :param exclude: list, a list of values that shouldn't be selected from *args
    :returns: a single object from all the *args
    """
    exclude = kwargs.pop("exclude", None)
    exclude = set(exclude) if exclude else set()
    vals = []
    for arg in args:
        if isinstance(arg, basestring) or not isinstance(arg, Sequence):
            vals.append(arg)
        else:
            vals.extend(arg)

    ret = random.choice(vals)
    while ret in exclude:
        ret = random.choice(vals)
    return ret
choose = choice


def get_bool():
    """Returns either True or False randomly"""
    return random.choice([True, False])


def run(cmd, arg_str="", cwd="", environ=None, **kwargs):
    """Run a command on the command line

    :param cmd: mixed, the command you want to run
    :param arg_str: string, extra flags that will be appended to the cmd
    :param **kwargs: allows you to pass into underlying Command.run() method
    :returns: string, the output from the command
    """
    if isinstance(cmd, Path) and hasattr(cmd, "run"):
        ret = cmd.run(arg_str, cwd=cwd, environ=environ, **kwargs)

    else:
        cmd = Command(cmd, cwd=cwd, environ=environ)
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


def get_digits(count, n=None):
    """return a string value that contains count digits

    :param count: int, how many digits you want, so if you pass in 4, you would get
        4 digits
    :param n: int, if you already have a value and want it to for sure by count digits
    :returns: string, this returns a string because the digits might start with
        zero
    """
    max_size = int("9" * count)

    if n is None:
        n = get_int(0, max_size)
    else:
        if n > max_size:
            raise ValueError("n={} has more than {} digits".format(n, count))

    ret = "{{:0>{}}}".format(count).format(n)
    return ret
get_digit = get_digits
get_count_digits = get_digits


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
get_pint = get_posint


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


def get_counter(start=1, step=1):
    """Because sometimes you just want to count, this is just a wrapper around
    itertools.count

    :Example:
        c = testdata.get_counter()
        c() # 1
        c() # 2
        c() # 3

    :param start: int, the number to start at
    :param step: int, the increment each time the callback is called
    :returns: callable, everytime you invoke it it will increment by step
    """
    counter = itertools.count(start, step)
    return lambda: next(counter)


def get_range(max_size=10):
    """Because sometimes you just want a random range

    https://github.com/Jaymon/testdata/issues/74

    :param max_size: int, the max range stop value you want
    :returns: range that can be iterated
    """
    if yes():
        start = 1
        stop = get_int(1, max_size + 1)

    else:
        start = 0
        stop = get_int(max_size=max_size)

    return range(start, stop)


def get_list(callback, max_size=100):
    """Create a list filled with values returned from callback

    https://github.com/Jaymon/testdata/issues/73

    :param callback: callable, each item in the list will be populated by calling this
    :param max_size: int, the maximum size of the list
    :returns: list, the randomly generated list
    """
    ret = []
    for x in get_range(max_size):
        ret.append(callback())
    return ret


def get_dict(*keys, **kv):
    """Create a dict filled with key/values returned from kv

    https://github.com/Jaymon/testdata/issues/73

    :param kv: dict, each key/callable will be used to generate a random dict key/val
    :returns: dict, the randomly generated dict
    """
    if keys:
        kv = {}
        for k in keys:
            kv[k] = (lambda: get_words(5)) if yes() else get_int

    if not kv:
        kv = {}
        for x in get_range(5):
            k = get_ascii_string()
            v = (lambda: get_words(5)) if yes() else get_int
            kv[k] = v

    ret = {}
    for k, callback in kv.items():
        ret[k] = callback()
    return ret


def get_ascii_words(count=0, as_str=True, **kwargs):
    return get_words(count, as_str, words=_ascii_words, **kwargs)


def get_ascii_word():
    return get_words(1, as_str=True, words=_ascii_words)


def get_unicode_words(count=0, as_str=True, **kwargs):
    return get_words(count, as_str, words=_unicode_words, **kwargs)
get_uni_words = get_unicode_words


def get_unicode_word():
    return get_words(1, as_str=True, words=_unicode_words)
get_uni_word = get_unicode_word


def get_words(count=0, as_str=True, words=None, **kwargs):
    '''get some amount of random words

    :param count: integer, how many words you want, 0 means a random amount (at most 20)
    :param as_str: boolean, True to return as string, false to return as list of words
    :param words: list, a list of words to choose from, defaults to unicode + ascii words
    :returns: unicode|list, your requested words
    '''
    # since we specified we didn't care, randomly choose how many words there should be
    if count == 0:
        count = random.randint(kwargs.get("min_count", 1), kwargs.get("max_count", 20))

    if not words:
        words = _words

    ret_words = random.sample(words, count)
    return ret_words if not as_str else ' '.join(ret_words)


def get_word(words=None):
    return get_words(1, as_str=True, words=words)


def get_lines(count=0, as_str=True, words=None):
    if count == 0:
        count = random.randint(1, 20)

    if not words:
        words = _words

    ret_lines = []
    for i in range(count):
        if yes(0.75):
            ret_lines.append(get_words(as_str=True, words=words))
        else:
            ret_lines.append("\n")

    return ret_lines if not as_str else "\n".join(ret_lines)


def get_ascii_lines(count=0, as_str=True):
    return get_lines(count, as_str, words=_ascii_words)


def get_unicode_lines(count=0, as_str=True):
    return get_lines(count, as_str, words=_unicode_words)
get_uni_lines = get_unicode_lines


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


def get_phone(number_format="{area_code}-{exchange_code}-{line_number}", **kwargs):
    """Get a phone number

    part names come from:

        https://www.freshworks.com/freshcaller-cloud-pbx/phone-numbers/us-area-codes/

    to do an international format:

        "+{country_code}-{area_code}-{exchange_code}-{line_number}"

    :param number_format: string, allows you to format the number how you want, each of the
        names (eg, area_code, exchange_code) corresponds to a value you can pass into
        **kwargs
    :param **kwargs: dict, any values you want to customize, if no keywords are passed
        in then it will be generated
    :returns: string, the phone number matching number_format
    """
    kwargs.setdefault("country_code", kwargs.pop("country", "1"))
    kwargs.setdefault("area_code", kwargs.pop("area", get_digits(3)))
    kwargs.setdefault("exchange_code", kwargs.pop("exchange", get_digits(3)))
    kwargs.setdefault("line_number", kwargs.pop("line", get_digits(4)))
    return number_format.format(**kwargs)
get_phone_number = get_phone


def get_street_address(house_number="", street="", **kwargs):
    address = []
    if not house_number:
        house_number = get_int(max_size=99999)

    address.append(String(house_number))

    if street:
        address.append(street)

    else:
        if "street_dir" in kwargs:
            address.append(kwargs["street_dir"])

        else:
            if yes():
                address.append(random.choice([
                    "E", "East",
                    "W", "West",
                    "N", "North",
                    "S", "South",
                ]))

        if "street_name" in kwargs:
            address.append(kwargs["street_name"])

        else:
            if yes():
                address.append(get_ascii_words(max_count=3))
            else:
                if yes():
                    address.append(get_ascii_name())
                else:
                    address.append(get_ascii_last_name())

        if "street_type" in kwargs:
            address.append(kwargs["street_name"])

        else:
            if yes():
                address.append(random.choice([
                    "Boulevard",
                    "Blvd",
                    "Road",
                    "RD",
                    "Rd",
                    "Street",
                    "st",
                    "st.",
                    "Lane",
                    "Ln",
                    "Drive",
                    "Dr",
                    "Dr.",
                    "Trail",
                    "Court",
                    "Ct",
                    "Ct.",
                    "Circle",
                    "Cir",
                    "Cir.",
                    "Pike",
                    "Highway",
                    "Hwy",
                    "Fwy",
                    "Avenue",
                    "Ave",
                    "Ave.",
                    "Terrace",
                    "Pkwy",
                    "Parkway",
                    "Place",
                ]))

    return " ".join(address)

def get_address_section(section="", **kwargs):
    if not section:
        section = []
        if yes():
            section.append(random.choice([
                "Apt",
                "Apt.",
                "Apartment",
                "Suite",
                "Building",
            ]))

        number = String(get_int(max_size=9999))
        if yes():
            prefix = random.choice([
                "#",
                get_middle_initial(),
            ])

            number = "{}{}".format(prefix, number)

        section.append(number)
        section = " ".join(section)
    return section


def get_usa_city(city="", **kwargs):
    if not city:
        city = random.choice(usa.cities)
    return city
get_us_city = get_usa_city


def get_usa_state(state="", **kwargs):
    if not state:
        if yes():
            state = random.choice(usa.states.names)
        else:
            state = random.choice(usa.states.abbrs)
    return state
get_us_state = get_usa_state


def get_usa_zipcode(state=""):
    state = get_usa_state(state)
    state = usa.states[state]["abbr"]
    return random.choice(usa.zipcodes[state])
get_us_zipcdoe = get_usa_zipcode
get_usa_zip = get_usa_zipcode
get_us_zip = get_usa_zipcode


def get_usa_address(**kwargs):
    """get an address that looks like it can be in the united states

    the generated addresses are not real but should hopefully look plausible

    https://en.wikipedia.org/wiki/Address#United_States

    :returns: named tuple(street, section, city, state, zipcode, line, lines) where
        line is a string of the address on one line and lines is the address on multiple
        lines
    """
    Address = namedtuple("Address", ["street", "section", "city", "state", "zipcode", "line", "lines"])

    street = get_street_address(**kwargs)
    section = get_address_section(**kwargs) if yes() else ""
    city = get_usa_city(**kwargs)
    state = get_usa_state(**kwargs)
    zipcode = get_usa_zipcode(state)

    line = street
    if section:
        line += " " + section
    line += ", " + city + ", " + state + " " + zipcode

    lines = [street]
    if section:
        lines.append(section)
    lines.append("{}, {}".format(city, state))
    lines.append(zipcode)
    lines = "\n".join(lines)

    address = Address(
        street,
        section,
        city,
        state,
        zipcode,
        line,
        lines,
    )

    #address.line = line
    #address.lines = lines
    #address.__str__ = lambda: line
    return address
get_us_address = get_usa_address
get_us_addr = get_usa_address
get_usa_addr = get_usa_address


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


def get_middle_initial(*args, **kwargs):
    """Returns just a capital letter"""
    return get_str(str_size=1, chars=string.ascii_uppercase)


def get_middle_name(*args, **kwargs):
    """Get a middle name or initial"""
    middle_name = get_first_name(*args, **kwargs)
    if yes():
        middle_name = get_first_name(*args, **kwargs)
    else:
        middle_name = get_middle_initial()
    return middle_name
get_middlename = get_middle_name


def get_ascii_middle_name(gender=""):
    '''return one ascii safe name'''
    return get_middle_name(gender, is_unicode=False)
get_ascii_middlename = get_middle_name


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
get_lastname = get_last_name
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


def get_datetime(now=None, backward=False, **kwargs):
    """get a datetime

    :param now: datetime|date|int|float|timedelta
        datetime - just returned
        date - returned as a datetime
        int - assumed to be days and will be added/subtracted from utc now
        float - assumed to be seconds and will be added/subtracted from utc now
        timedelta - will be add/subtracted from utc now
    :param backward: if True, then a positive int, float, or timedelta will be
        subtracted from utc now, if False then it will be added
    :param **kwargs: these will be passed to timedelta
    :returns: datetime
    """
    if not now and kwargs:
        now = datetime.timedelta(**kwargs)

    if now:
        if isinstance(now, datetime.datetime):
            pass

        elif isinstance(now, datetime.timedelta):
            seconds = now.total_seconds()
            microseconds = (seconds * 1000000) % 1000000
            if backward and seconds > 0:
                seconds *= -1.0

            td = datetime.timedelta(seconds=seconds, microseconds=microseconds)
            now = datetime.datetime.utcnow() + td

        elif isinstance(now, datetime.date):
            now = datetime.datetime(now.year, now.month, now.day)

        elif isinstance(now, int):
            if backward and now > 0:
                now *= -1.0
            now = datetime.datetime.utcnow() + datetime.timedelta(days=now)

        elif isinstance(now, float):
            seconds = int(now)
            microseconds = (now * 1000000) % 1000000
            if backward and seconds > 0:
                seconds *= -1.0
            td = datetime.timedelta(seconds=now, microseconds=microseconds)
            now = datetime.datetime.utcnow() + td

        else:
            raise ValueError("Unknown value: {}".format(now))

    else:
        now = datetime.datetime.utcnow()

    return now


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
    now = get_datetime(now, backward=True)
    td = now - datetime.datetime(year=2000, month=1, day=1)
    return now - datetime.timedelta(
        days=random.randint(1, max(td.days, 1)),
        seconds=random.randint(1, max(td.seconds, 1))
    )
get_past_dt = get_past_datetime
get_passed_datetime = get_past_datetime
get_before_datetime = get_past_datetime
get_past_date_time = get_past_datetime


def get_past_date(now=None):
    dt = get_past_datetime(now)
    return datetime.date(dt.year, dt.month, dt.day)


def get_future_datetime(now=None):
    """return a datetime guaranteed to be in the future from now"""
    now = get_datetime(now)
    return now + datetime.timedelta(
        weeks=random.randint(1, 52 * 50),
        hours=random.randint(0, 24),
        days=random.randint(0, 365),
        seconds=random.randint(0, 86400)
    )
get_future_dt = get_future_datetime
get_after_dt = get_future_datetime
get_after_date_time = get_future_datetime
get_future_date_time = get_future_datetime


def get_future_date(now=None):
    dt = get_future_datetime(now)
    return datetime.date(dt.year, dt.month, dt.day)


def get_between_datetime(start, stop=None):
    """get a datetime between start and stop

    return a datetime guaranteed to be in the future from start and in the past from stop
    """
    start = get_datetime(start)
    stop = get_datetime(stop)

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
get_between_date_time = get_between_datetime


def get_between_date(start, stop=None):
    dt = get_between_datetime(start, stop)
    return datetime.date(dt.year, dt.month, dt.day)


# used in the get_unique_int() function to make sure it never returns the same int twice
# this is a possible memory leak if you are using this script in a very long running
# process using get_int(), since this list will get bigger and bigger and never
# be flushed, but seriously, you should just use get_int() or random.randint() in any
# long running scripts. In order to minimize the memory leak we cap the list at
# environ.MAX_UNIQUE unique values
_previous_ints = set()

# similar to _previous_ints, used in get_unique_float() function
_previous_floats = set()


