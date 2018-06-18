# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import sys
from .compat import *


class ByteString(bytes):
    def __new__(cls, val, encoding="UTF-8"):
        if not encoding:
            # ??? use chardet to figure out what encoding val is?
            # https://stackoverflow.com/questions/196345/how-to-check-if-a-string-in-python-is-in-ascii/6988354#6988354
            encoding = sys.getdefaultencoding()

        if isinstance(val, unicode):
            val = val.encode(encoding)

        instance = super(ByteString, cls).__new__(cls, val)
        instance.encoding = encoding
        return instance

    def unicode(self):
        return self.decode(self.encoding)
    __unicode__ = unicode

    def __str__(self):
        return self if is_py2 else self.unicode()

    def __bytes__(self):
        return self


class String(unicode):
    def __new__(cls, val, encoding="UTF-8"):
        if not isinstance(val, unicode):
            val = ByteString(val, encoding).unicode()
        instance = super(String, cls).__new__(cls, val)
        instance.encoding = encoding
        return instance

