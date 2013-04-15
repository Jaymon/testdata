# Testdata -- Easily Generate Random Test Data

These are a bunch of functions I've been using for years over numerous projects. I'm finally bundling
them up into a proper module instead of the copy/pasting I've been doing.

To use testdata in your tests, just include the `testdata.py` module:

    import testdata

To install, use Pip:

   pip install git+https://github.com/Jaymon/testdata#egg=testdata


## Todo

- the `get_names()` function does not generate any names outside the ascii range, neither
does `get_words()`, these should be expanded
