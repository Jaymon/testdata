# Testdata

Generate Random Test Data

These are a bunch of functions I've been using for years over numerous projects. I'm finally bundling them up into a proper module instead of the copy/pasting I've been doing up until now.

To use testdata in your tests, just include the `testdata.py` module:

    import testdata

To install, use Pip:

    pip install testdata

Or, with Pip using Github:

    pip install git+https://github.com/Jaymon/testdata#egg=testdata

## Functions

### `create_dir(path, tmpdir=u"")`

create a directory hierarchy

    base_dir = "/tmp"
    d = testdata.create_dir("/foo/bar", base_dir)
    print d # /tmp/foo/bar

### `create_file(path, contents=u"", tmpdir=u"")`

create a file with contents

    base_dir = "/tmp"
    f = testdata.create_dir("/foo/bar.txt", "The file contents", base_dir)
    print f # /tmp/foo/bar.txt

### `create_module(module_name, contents=u"", tmpdir=u"", make_importable=True)`

create a module with python contents that can be imported

    base_dir = "/tmp"
    f = testdata.create_dir("foo.bar", "class Che(object): pass", base_dir)
    print f # /tmp/foo/bar.py

### `get_ascii(str_size=0)`

return a string of ascii characters

    >>> testdata.get_ascii()
    u'IFUKzVAauqgyRY6OV'

### `get_float(min_size=None, max_size=None)`

return a floating point number between `min_size` and `max_size`.

    >>> testdata.get_float()
    2.932229899095845e+307

### `get_int(min_size=1, max_size=sys.maxsize)`

return an integer between `min_size` and `max_size`.

    >>> testdata.get_int()
    3820706953806377295

### `get_name(name_count=2, as_str=True)`

returns a random name that can be outside the ascii range (eg, name can be unicode)

    >>> testdata.get_name()
    u'jamel clarke-cabrera'

### `get_str(str_size=0, chars=None)`

return random characters, which can be unicode.

    >>> testdata.get_str()
    u'q\x0bwZ\u79755\ud077\u027aYm\ud0d8JK\x07\U0010df418tx\x16'

### `get_url()`

return a random url.

    >>> testdata.get_url()
    u'https://sK6rxrCa626TkQddTyf.com'

### `get_words(word_count=0, as_str=True)`

return a random amount of words, which can be unicode.

    >>> testdata.get_words()
    u'\u043f\u043e\u043d\u044f\u0442\u044c \u043c\u043e\u0436\u043d\u043e felis, \u0447\u0442\u043e\u0431\u044b habitasse ultrices Nam \u043d\u043e\u0447\u044c \u043c\u0438\u043d\u0443\u0442\u0430 In \u0441\u0438\u0434\u0435\u0442\u044c varius, \u0436\u0435\u043d\u0430'
