# -*- coding: utf-8 -*-
import tempfile

from datatypes import Environ, Bool


environ = Environ("TESTDATA_")


# should output pass through stdout and stderr as it captures it or suppress
# it?  set to either 0 (False) or 1 (True)
environ.setdefault("PASSTHROUGH", True, type=Bool)


# You can set this if you would like paths to be in a certain directory, None
# means it will use system temp directory
environ.setdefault("TEMPDIR", tempfile.gettempdir())


# if you have a directory where you put a lot of testdata data  files, you can
# set that directory and then use PathData.get_data_files to easily load those
# files
environ.setdefault("CONTENTS_DIR", "")


# the default encoding for things (not fully supported/used throughout the
# codebase), added 9-2018
environ.setdefault("ENCODING", "UTF-8", type=lambda x: x.upper())


# the cap for maximum unique values, this is just here to keep from leaking
# memory, the unique float and int functions will trim the list after this many
# unique values
environ.setdefault("MAX_UNIQUE", 1000000, type=int)


# True (default) if testdata should attempt to autoload testdata modules
# looking for TestData child classes
environ.setdefault("AUTOLOAD", True, type=Bool)


# Holds the autoloading name if modules are automatically loaded
environ.setdefault("AUTODISCOVER_NAME", "testdata")

