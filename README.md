# Testdata

Generate Random Test Data.

These are just a bunch of functions designed to make it easier to test your code.

To use testdata in your tests, just include the `testdata.py` module:

    import testdata

To install, use Pip:

    pip install testdata

Or, with Pip using Github:

    pip install git+https://github.com/Jaymon/testdata#egg=testdata


## Functionality

This is an overview of some of the functions and classes found in the Testdata module, there are other functions (like `get_birthday`) that aren't listed here, for the complete list just look at the [source](https://github.com/Jaymon/testdata/blob/master/testdata.py).


### patch


#### Patching modules and classes

```python
patch(mod, **patches)
```

Patches a module, instance, or class with the given patches.

Suppose you had a module like this:

```python
# module foo.bar

def boom():
    return 1

class FooPatch(object):
    @classmethod
    def bam(cls): return boom()
```

Now you can easily patch it for testing:

```python
def mock_boom():
    return 2

foo_bar = testdata.patch('foo.bar', boom=mock_boom)
print foo_bar.FooPatch.bam() # 2

# but you can also just pass in objects or modules

from foo.bar import FooPatch
FooPatch = testdata.patch(FooPatch, boom=mock_boom)
print FooPatch.bam() # 2

from foo import bar
bar = testdata.patch(bar, boom=mock_boom)
print bar.FooPatch.bam() # 2
```


#### Patching class instances

You can also patch a specific instance

Suppose you had a module like this:

```python
# module foo.bar

class Foo(object):
    def boom(self): return 1
```

Now you can easily patch it for testing:

```python
def mock_boom():
    return 2

foo = Foo()
foo_patched = testdata.patch(foo, boom=mock_boom)
print foo_patched.boom() # 2

# be aware though, the original instance was modified, foo_patched == foo
print foo.boom() # 2
```


-------------------------------------------------------------------------------

### capture

Output buffering, handy when you want to make sure logging or print statements are doing what you think they should be doing.

```python
with testdata.capture() as c:
    print("foo")
if "foo" in c:
    print("foo was captured")
```


-------------------------------------------------------------------------------

### Threading

A wrapper around python's builtin `threading.Thread` class that bubbles errors up to the main thread because, by default, python's threading classes suppress errors, this makes it annoying when using threads for testing.

```python
def run():
    raise ValueError("join_2")

thread = testdata.Thread(target=run)
thread.start()
print(thread.exception)
```


-------------------------------------------------------------------------------

### create_dir

```python
create_dir(path, tmpdir=u"")
```

create a directory hierarchy

```python
base_dir = "/tmp"
d = testdata.create_dir("/foo/bar", base_dir)
print d # /tmp/foo/bar
```

-------------------------------------------------------------------------------

### create_file

```python
create_file(path, contents=u"", tmpdir=u"")
```

create a file with contents

```python
base_dir = "/tmp"
f = testdata.create_file("/foo/bar.txt", "The file contents", base_dir)
print f # /tmp/foo/bar.txt
```

-------------------------------------------------------------------------------

### create_files

```python
create_files(file_dict, tmpdir=u"")
```

Create a whole bunch of files, the `file_dict` key is the filename, the value is the contents of the file.
The `file_dict` is very similar to the `create_modules` param `module_dict`

```python
file_dict = {
    "foo/bar.txt": "the foo file contents",
    "baz.txt": "the baz file contents",
}
f = testdata.create_files(file_dict)
```

-------------------------------------------------------------------------------

### get_file

```python
get_file(path="", tmpdir="")
```

This will return a `Filepath` instance that you can manipulate but unlike `create_file` it won't actually create the file, just give you a path to a file that could be created.


-------------------------------------------------------------------------------

### create_module

```python
create_module(module_name, contents=u"", tmpdir=u"", make_importable=True)
```

create a module with python contents that can be imported

```python
base_dir = "/tmp"
f = testdata.create_module("foo.bar", "class Che(object): pass", base_dir)
print f # /tmp/foo/bar.py
```

-------------------------------------------------------------------------------

### create_modules

```python
create_modules(module_dict, tmpdir=u"", make_importable=True)
```

create a whole bunch of modules at once

```python
f = testdata.create_modules(
  {
    "foo.bar": "class Che(object): pass",
    "foo.bar.baz": "class Boom(object): pass",
    "foo.che": "class Bam(object): pass",
  }
)
```

-------------------------------------------------------------------------------

### get_ascii

```python
get_ascii(str_size=0)
```

return a string of ascii characters

    >>> testdata.get_ascii()
    u'IFUKzVAauqgyRY6OV'


-------------------------------------------------------------------------------

### get_md5

```python
get_md5(val="")
```

return an md5 hash of val (if passed in) or a random val if val is empty

    >>> testdata.get_md5()
    'b165765400b30772f1d9b3975ce77320'


-------------------------------------------------------------------------------

### get_hash

```python
get_hash(str_size=32)
```

return a random hash

    >>> testdata.get_hash()
    u"jYw3HseUl8GLoMc8QejLYFogC2lUYoUu"


-------------------------------------------------------------------------------

### get_bool

```python
get_bool()
```

return a boolean (either **True** or **False**)

    >>> testdata.get_bool()
    False
    >>> testdata.get_bool()
    True

-------------------------------------------------------------------------------
### get_float

```python
get_float(min_size=None, max_size=None)
```

return a floating point number between `min_size` and `max_size`.

    >>> testdata.get_float()
    2.932229899095845e+307

-------------------------------------------------------------------------------

### get_int

```python
get_int(min_size=1, max_size=sys.maxsize)
```

return an integer between `min_size` and `max_size`.

    >>> testdata.get_int()
    3820706953806377295

-------------------------------------------------------------------------------

### get_name

```python
get_name(name_count=2, as_str=True)
```

returns a random name that can be outside the ascii range (eg, name can be unicode)

    >>> testdata.get_name()
    u'jamel clarke-cabrera'

-------------------------------------------------------------------------------

### get_email

```python
get_email(name=u'')
```

returns a random email address in the ascii range.

    >>> testdata.get_email()
    u'shelley@gmail.com'

-------------------------------------------------------------------------------

### get_str

```python
get_str(str_size=0, chars=None)
```

return random characters, which can be unicode.

    >>> testdata.get_str()
    u"q\x0bwZ\u79755\ud077\u027aYm\ud0d8JK\x07\U0010df418tx\x16"

-------------------------------------------------------------------------------

### get_url

```python
get_url()
```

return a random url.

    >>> testdata.get_url()
    u'https://sK6rxrCa626TkQddTyf.com'

-------------------------------------------------------------------------------

### get_words

```python
get_words(word_count=0, as_str=True)
```

return a random amount of words, which can be unicode.

    >>> testdata.get_words()
    u"\u043f\u043e\u043d\u044f\u0442\u044c \u043c\u043e\u0436\u043d\u043e felis, habitasse ultrices Nam \u0436\u0435\u043d\u0430"

-------------------------------------------------------------------------------

### get_past_datetime

```python
get_past_datetime([now])
```

return a datetime guaranteed to be in the past from `now`

    >>> testdata.get_past_datetime()
    datetime.datetime(2000, 4, 2, 13, 40, 11, 133351)

-------------------------------------------------------------------------------

### get_future_datetime

```python
get_future_datetime([now])
```

return a datetime guaranteed to be in the future from `now`

    >>> testdata.get_future_datetime()
    datetime.datetime(2017, 8, 3, 15, 54, 58, 670249)

-------------------------------------------------------------------------------

### get_between_datetime

```python
get_between_datetime(start[, stop])
```

return a datetime guaranteed to be in the future from `start` and in the past from `stop`

    >>> start = datetime.datetime.utcnow() - datetime.timedelta(days=100)
    >>> testdata.get_between_datetime(start)
    datetime.datetime(2017, 8, 3, 15, 54, 58, 670249)


## Testing

Testing in 2.7 on most systems:

    $ python -m unittest testdata_test

Testing in 3.5 on MacOS:

    $ python3.5 -m unittest testdata_test

