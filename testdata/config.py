# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import tempfile

from datatypes.config import Environ


environ = Environ("TESTDATA_")

# should output pass through stdout and stderr as it captures it or suppress it?
# set to either 0 (False) or 1 (True)
environ.setdefault("PASSTHROUGH", True, type=bool)

# You can set this if you would like paths to be in a certain directory, None means
# it will use system temp directory
environ.setdefault("TEMPDIR", tempfile.gettempdir())

# if you have a directory where you put a lot of testdata files, you can set the
# directory and then use path.Contents to easily load those files
environ.setdefault("CONTENTS_DIR", "")

# the default encoding for things (not fully supported/used throughout the
# codebase), added 9-2018
environ.setdefault("ENCODING", "UTF-8", type=lambda x: x.upper())

# the cap for maximum unique values, this is just here to keep from leaking
# memory, the unique float and int functions will trim the list after this many
# unique values
environ.setdefault("MAX_UNIQUE", 1000000, type=int)

environ.setdefault("TESTDATA_MODULEPATH", "") # DEPRECATED


# should output pass through stdout and stderr as it captures it or suppress it?
# set to either 0 (False) or 1 (True)
# PASSTHROUGH = bool(os.environ.get("TESTDATA_PASSTHROUGH", True))
# 
# # You can set this if you would like paths to be in a certain directory, None means
# # it will use system temp directory
# TEMPDIR = os.environ.get("TESTDATA_TEMPDIR", tempfile.gettempdir())
# 
# # if you have a directory where you put a lot of testdata files, you can set the
# # directory and then use path.Contents to easily load those files
# CONTENTS_DIR = os.environ.get("TESTDATA_CONTENTS_DIR", "")
# 
# # The server hostname and port information
# # DEPRECATED?
# HOSTNAME = os.environ.get("TESTDATA_HOSTNAME", "127.0.0.1")
# HOSTPORT = int(os.environ.get("TESTDATA_HOSTPORT", 0))
# 
# # the default encoding for things (not fully supported/used throughout the
# # codebase), added 9-2018
# ENCODING = os.environ.get("TESTDATA_ENCODING", "UTF-8")
# 
# # the cap for maximum unique values, this is just here to keep from leaking
# # memory, the unique float and int functions will trim the list after this many
# # unique values
# MAX_UNIQUE = int(os.environ.get("TESTDATA_MAX_UNIQUE", 1000000))
# 
# TESTDATA_MODULEPATH = os.environ.get("TESTDATA_TESTDATA_MODULEPATH", "")
