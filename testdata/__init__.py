'''
a module to make it easy to get some test data

NOTE: all methods that return strings will return unicode utf-8 strings

for a utf-8 stress test, see: http://www.cl.cam.ac.uk/~mgk25/ucs/examples/UTF-8-test.txt
you can get all the unicode chars and their names: ftp://ftp.unicode.org/
    ftp://ftp.unicode.org/Public/6.3.0/ucd/UnicodeData-6.3.0d2.txt
'''
import re
import random
import string
import sys
import tempfile
import os
import codecs
import datetime
from random import randint # make it possible to do testdata.randint so 2 imports aren't needed
from collections import deque
import types
import imp
import inspect
import copy

from .data import _names, \
    _unicode_names, \
    _ascii_paragraphs, \
    _unicode_paragraphs, \
    _ascii_words, \
    _unicode_words, \
    _words

from .path import Dirpath, Filepath, Modulepath


__version__ = '0.6.8'


def create_dir(path=u"", tmpdir=u""):
    '''
    create a directory path using a tempdir as the root

    so, if you pass in "/foo/bar" that will be combined with a tempdir, so you end 
    up with the final path: /tmp/python/dir/foo/bar

    path -- string -- the temp dir path
    tmpdir -- string -- the temp directory to use as the base

    return -- Dirpath -- the full directory path
    '''
    return Dirpath.create_instance(path, tmpdir)


def create_file(path, contents=u"", tmpdir=u""):
    '''
    create a file and return the full path to that file

    path -- string -- the path to the file
    contents -- string -- the file contents
    tmpdir -- string -- the temp directory to use as the base

    return -- Filepath -- the full file path
    '''
    return Filepath.create_instance(path, contents, tmpdir)


def create_files(file_dict, tmpdir=u""):
    """
    create a whole bunch of files all at once

    file_dict -- dict -- keys are the filepath relative to tmpdir, values are the
        file contents
    tmpdir -- Dirpath -- same as create_module() tmpdir
    """
    base_dir = Dirpath(basedir=tmpdir)
    for file_name, contents in file_dict.items():
        base_dir.create_file(file_name, contents)
    return base_dir


def create_module(module_name, contents=u"", tmpdir=u"", make_importable=True):
    '''
    create a python module folder structure so that the module can be imported

    module_name -- string -- something like foo.bar
    contents -- string -- the contents of the module
    tmpdir -- string -- the temp directory that will be added to the syspath if make_importable is True
    make_importable -- boolean -- if True, then tmpdir will be added to the python path so it can be imported

    return -- Module -- the module file path
    '''
    return Modulepath.create_instance(module_name, contents, tmpdir, make_importable)


def create_modules(module_dict, tmpdir=u"", make_importable=True):
    """
    create a whole bunch of modules all at once

    module_dict -- dict -- keys are the module_name, values are the module contents
    tmpdir -- string -- same as create_module() tmpdir
    make_importable -- boolean -- same as create_module() tmpdir
    return -- Dirpath
    """
    module_base_dir = Dirpath(basedir=tmpdir)

    for module_name, contents in module_dict.iteritems():
        Modulepath.create_instance(module_name, contents, module_base_dir, make_importable)
        make_importable = False

    return module_base_dir


def create_package(module_name, contents=u"", tmpdir=u"", make_importable=True):
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
    return u'http{}://{}.com'.format(
        u's' if random.choice([True, False]) else u'',
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
        first_values = byte_range(0x00, 0x7F) + byte_range(0xC2, 0xF4)
        trailing_values = byte_range(0x80, 0xBF)

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

    s = u''.join(sg)
    return s


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


def get_float(min_size=None, max_size=None):
    '''
    get a random float

    no different than random.uniform() except it automatically can set range, and
    guarrantees that no 2 floats are the same

    return -- float
    '''
    global _previous_floats

    float_info = sys.float_info
    if min_size is None:
        min_size = float_info.min
    if max_size is None:
        max_size = float_info.max

    i = 0;
    while True:
        i = random.uniform(min_size, max_size)
        if i not in _previous_floats:
            _previous_floats.add(i)
            # we cap the list at 100000 unique ints
            if len(_previous_floats) > 100000:
                _previous_floats.pop()
            break

    return i


def get_posint(max_size=2**31-1):
    """
    just return a positive 32-bit integer, this is basically a wrapper around
    random.randint where you don't have to specify a minimum (or a maximum if you
    don't want)
    """
    min_size = 1
    return random.randint(min_size, max_size)


def get_int(min_size=1, max_size=sys.maxsize):
    return get_unique_int(min_size, max_size)


def get_int32(min_size=1):
    """returns a unique 32-bit positive integer"""
    return get_unique_int(min_size, 2**31-1)


def get_int64(min_size=1):
    """returns up to a unique 64-bit positive integer"""
    return get_unique_int(min_size, 2**63-1)


def get_unique_int(min_size=1, max_size=sys.maxsize):
    '''
    get a random integer

    no different than random.randint except that it guarrantees no int will be
    the same, and also you don't have to set a range, it will default to all max
    int size

    return -- integer 
    '''
    global _previous_ints

    i = 0;
    found = False
    max_count = max_size - min_size
    for x in xrange(max_count):
        i = random.randint(min_size, max_size)
        if i not in _previous_ints:
            found = True
            _previous_ints.add(i)
            # we cap the list at 100000 unique ints
            if len(_previous_ints) > 100000:
                _previous_ints.pop()
            break

    assert found, "no unique ints from {} to {} could be found".format(min_size, max_size)
    return i


def get_ascii_words(word_count=0, as_str=True):
    return get_words(word_count, as_str, words=_ascii_words)


def get_unicode_words(word_count=0, as_str=True):
    return get_words(word_count, as_str, words=_unicode_words)


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
    return ret_words if not as_str else u' '.join(ret_words)


def get_birthday(as_str=False):
    """
    return a random YYYY-MM-DD

    as_str -- boolean -- true to return the bday as a YYYY-MM-DD string
    return -- datetime.date|string
    """
    year = random.randint(1950, 1999)
    month = random.randint(1, 12)
    day = 1
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


def get_email(name=u''):
    '''return a random email address'''
    if not name: name = get_ascii_name()
    name = re.sub("['-]", "", name)

    email_domains = [
        u"yahoo.com",
        u"hotmail.com",
        u"outlook.com",
        u"aol.com",
        u"gmail.com",
        u"msn.com",
        u"comcast.net",
        u"hotmail.co.uk",
        u"sbcglobal.net",
        u"yahoo.co.uk",
        u"yahoo.co.in",
        u"bellsouth.net",
        u"verizon.com",
        u"earthlink.net",
        u"cox.net",
        u"rediffmail.com",
        u"yahoo.ca",
        u"btinternet.com",
        u"charter.net",
        u"shaw.ca",
        u"ntlworld.com",
        u"gmx.com",
        u"gmx.net",
        u"mail.com",
        u"mailinator.com"
    ]

    return u'{}@{}'.format(name.lower(), random.choice(email_domains))


def get_name(name_count=2, as_str=True):
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

    # decide if we should hyphenate the last name
    names = []
    if name_count > 0:
        #names = random.sample(_names, name_count)
        for x in xrange(name_count):
            if random.randint(0, 100) < 20:
                names.append(get_unicode_name())
            else:
                names.append(get_ascii_name())

        if name_count > 1:
            if random.randint(0, 20) == 1:
                names[-1] = u'{}-{}'.format(names[-1], random.choice(_names))

    return names if not as_str else u' '.join(names)


def get_ascii_name():
    '''return one ascii safe name'''
    return random.choice(_names)


def get_unicode_name():
    '''return one none ascii safe name'''
    name = u''
    while True:
        # total hack to get around not all the names in _unicode_names being unicode
        try:
            name = random.choice(_unicode_names)
            name.decode('utf-8')
        except UnicodeEncodeError:
            break

    return name
    # return random.choice(_unicode_names)


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


def patch_module(mod_name, attr_name='', patches=None, **kwargs_patches):
    if not mod_name:
        raise ValueError("mod_name is empty")

    if not patches: patches = {}
    patches.update(kwargs_patches) # combine both dicts
    if not patches: raise ValueError("patches dict is empty")

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

    # http://stackoverflow.com/questions/4907054/
    def find_mod_path(p):
        if '.' in p:
            p, m = p.rsplit('.', 1)
            imod_path = find_mod_path(p)
            mod_path = os.path.join(imod_path, m)
            #mod = imp.load_module('{}_{}'.format(m, get_ascii(8)), *imp.find_module(m, imod.__path__))

        else:
            _, mod_path, _ = imp.find_module(p)

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

    if attr_name:
        m = getattr(m, attr_name)

    return m


def patch_instance(mod, patches=None, **kwargs_patches):
    if not mod:
        raise ValueError("mod is empty")

    if not patches: patches = {}
    patches.update(kwargs_patches) # combine both dicts
    if not patches: raise ValueError("patches dict is empty")

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
    if not patches: raise ValueError("patches dict is empty")

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

    # http://stackoverflow.com/questions/9541025/how-to-copy-a-python-class
    mod_patched = type(
        '{}Patched'.format(mod.__name__),
        mod.__bases__,
        #{k: copy.deepcopy(v) for k, v in mod.__dict__.items()}
        copy_dict(mod)
    )
    for name, patch in patches.items():
        setattr(mod_patched, name, patch)

    return mod_patched


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
        m = patch_module(mod, "", patches=patches, **kwargs_patches)

    elif inspect.ismodule(mod):
        m = patch_module(mod.__name__, "", patches=patches, **kwargs_patches)

    elif inspect.isclass(mod):
        m = patch_class(mod, patches=patches, **kwargs_patches)

    else:
        m = patch_instance(mod, patches=patches, **kwargs_patches) 

    return m


def get_past_datetime(now=None):
    if not now: now = datetime.datetime.utcnow()
    td = now - datetime.datetime(year=2000, month=1, day=1)
    return now - datetime.timedelta(
        days=random.randint(1, max(td.days, 1)),
        seconds=random.randint(1, max(td.seconds, 1))
    )


def get_future_datetime(now=None):
    if not now: now = datetime.datetime.utcnow()
    return now + datetime.timedelta(
        weeks=random.randint(1, 52 * 50),
        hours=random.randint(0, 24),
        days=random.randint(0, 365),
        seconds=random.randint(0, 86400)
    )


def get_between_datetime(start, stop=None):
    """get a datetime between start and stop"""
    if not stop:
        stop = datetime.datetime.utcnow()

    if start >= stop:
        raise ValueError("start datetime >= stop datetime")

    td = stop - start
    return start + datetime.timedelta(
        days=random.randint(0, td.days),
        seconds=random.randint(0, (td.seconds - 1)),
        microseconds=random.randint(0, (td.microseconds - 1)),
    )


# used in the get_int() method to make sure it never returns the same int twice
# this is a possible memory leak if you are using this script in a very long running
# process using get_int(), since this list will get bigger and bigger and never
# be flushed, but seriously, you should just use random.randint() in any long running
# scripts. In order to minimize the memory leak we cap the list at 100k unique values
_previous_ints = set()

# similar to get_int()
_previous_floats = set()


