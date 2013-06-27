# Testdata -- Easily Generate Random Test Data

These are a bunch of functions I've been using for years over numerous projects. I'm finally bundling
them up into a proper module instead of the copy/pasting I've been doing.

To use testdata in your tests, just include the `testdata.py` module:

    import testdata

To install, use Pip:

    pip install git+https://github.com/Jaymon/testdata#egg=testdata


## Functions

### `testdata.create_dir`

create a directory hierarchy

    base_dir = "/tmp"
    d = testdata.create_dir("/foo/bar", base_dir)
    print d # /tmp/foo/bar

### `testdata.create_file`

create a file with contents

    base_dir = "/tmp"
    f = testdata.create_dir("/foo/bar.txt", "this is the file contents", base_dir)
    print f # /tmp/foo/bar.txt

### `testdata.create_module`

create a module with python contents that can be imported

    base_dir = "/tmp"
    f = testdata.create_dir("foo.bar", "class Che(object): pass", base_dir)
    print f # /tmp/foo/bar.py

### `get_ascii(str_size=0)`

return a string of ascii characters

### `get_float(min_size=None, max_size=None)`

return a floating point number between `min_size` and `max_size`.

### `get_int(min_size=1, max_size=sys.maxsize)`

return an integer between `min_size` and `max_size`.


### `get_name(name_count=2, as_str=True)`

returns a random name that can be outside the ascii range (eg, name can be unicode)

    n = testdata.get_name()
    print n # John Doe

### `get_str(str_size=0, chars=None)`

return random characters, which can be unicode.

### `get_url()`

return a random url.

### `get_words(word_count=0, as_str=True)`

return a random amount of words, which can be unicode.

