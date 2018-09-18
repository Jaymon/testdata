# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import os
import tempfile


# should output pass through stdout and stderr as it captures it or suppress it?
# set to either 0 (False) or 1 (True)
PASSTHROUGH = bool(os.environ.get("TESTDATA_PASSTHROUGH", True))

# You can set this if you would like paths to be in a certain directory, None means
# it will use system temp directory
TEMPDIR = os.environ.get("TESTDATA_TEMPDIR", tempfile.gettempdir())

# if you have a directory where you put a lot of testdata files, you can set the
# directory and then use path.Contents to easily load those files
CONTENTS_DIR = os.environ.get("TESTDATA_CONTENTS_DIR", "")

# The server hostname and port information
HOSTNAME = os.environ.get("TESTDATA_HOSTNAME", "127.0.0.1")
HOSTPORT = int(os.environ.get("TESTDATA_HOSTPORT", 0))

# the default encoding for things (not fully supported/used throughout the
# codebase), added 9-2018
ENCODING = os.environ.get("TESTDATA_ENCODING", "UTF-8")

# the cap for maximum unique values, this is just here to keep from leaking
# memory, the unique float and int functions will trim the list after this many
# unique values
MAX_UNIQUE = int(os.environ.get("TESTDATA_MAX_UNIQUE", 1000000))

