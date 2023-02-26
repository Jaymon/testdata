# -*- coding: utf-8 -*-
"""
NOTE: most methods that return strings will return unicode utf-8 strings

for a utf-8 stress test, see: http://www.cl.cam.ac.uk/~mgk25/ucs/examples/UTF-8-test.txt
you can get all the unicode chars and their names: ftp://ftp.unicode.org/
    ftp://ftp.unicode.org/Public/6.3.0/ucd/UnicodeData-6.3.0d2.txt
"""
import random
import string
import sys
import uuid
import hashlib

from datatypes import Url, ByteString

from ..compat import *
from ..base import TestData

from ..data import (
    _ascii_words,
    _unicode_words,
    _words,
)

###############################################################################
# testdata functions
###############################################################################
class StringData(TestData):
    def get_url(self, *args, **kwargs):
        '''
        get a url, this is just a nice shortcut method to something I seemed to do a lot

        :param *args: path parts, these will be added to the generated urlstring
        :param **kwargs: keywords you can pass into Url
        :returns: Url instance
        '''
        urlstring = 'http{}://{}.com'.format(
            's' if random.choice([True, False]) else '',
            self.get_ascii()
        )
        return Url(urlstring, *args, **kwargs)

    def get_str(self, str_size=0, chars=None, **kwargs):
        """generate a random unicode string

        if chars is None, this can generate up to a 4-byte utf-8 unicode string, which can
        break legacy utf-8 things

        :param str_size: int, how long you want the string to be
        :param chars: sequence, the characters you want the string to use, if this is None, it
            will default to pretty much the entire unicode range of characters
        :param **kwargs:
            min_size: the minimum size the string should be
            max_size: the maximum size the string should be
        :returns: str
        """
        str_size = self.get_size(str_size=str_size, default_min=3, default_max=20, **kwargs)

        if chars:
            # we have a defined set of chars
            s = "".join(random.choices(chars, k=str_size))
            #s = "".join(random.choices(chars, k=str_size) for c in range(str_size))

        else:
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

            s = "".join(random_utf8_seq().decode('utf-8') for c in range(str_size))

        return s
    get_unicode = get_str
    get_string = get_str

    def get_hex(self, str_size=0, **kwargs):
        '''
        generate a string of just hex characters

        str_size -- integer -- how long you want the string to be
        return -- unicode
        '''
        return self.get_str(str_size=str_size, chars=string.hexdigits.lower(), **kwargs)

    def get_ascii(self, str_size=0, **kwargs):
        '''
        generate a random string full of just ascii characters

        str_size -- integer -- how long you want the string to be
        return -- unicode
        '''
        chars=string.ascii_letters + string.digits
        return self.get_str(str_size=str_size, chars=chars, **kwargs)
    get_ascii_str = get_ascii
    get_ascii_string = get_ascii
    get_alphanum = get_ascii
    get_alphanum_str = get_ascii
    get_alphanum_string = get_ascii
    get_alphanumeric = get_ascii
    get_alphanumeric_str = get_ascii
    get_alphanumeric_string = get_ascii

    def get_hash(self, str_size=32, **kwargs):
        """Returns a random hash, if you want an md5 use get_md5(), if you want an
        uuid use get_uuid()"""
        return self.get_ascii(str_size=str_size, **kwargs)

    def get_md5(self, *val):
        """Return an md5 hash of val, if no val then return a random md5 hash

        :param val: string, the value you want to md5 hash
        :returns: string, the md5 hash as a 32 char hex string
        """
        if val:
            val = map(String, filter(None, val))

        else:
            val = [self.get_uuid()]

        return hashlib.md5(ByteString("".join(val))).hexdigest()

    def get_uuid(self):
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

    def get_ascii_words(self, count=0, as_str=True, **kwargs):
        return self.get_words(count, as_str, words=_ascii_words, **kwargs)

    def get_ascii_word(self):
        return self.get_words(1, as_str=True, words=_ascii_words)

    def get_unicode_words(self, count=0, as_str=True, **kwargs):
        return self.get_words(count, as_str, words=_unicode_words, **kwargs)
    get_uni_words = get_unicode_words

    def get_unicode_word(self):
        return self.get_words(1, as_str=True, words=_unicode_words)
    get_uni_word = get_unicode_word

    def get_words(self, count=0, as_str=True, words=None, **kwargs):
        '''get some amount of random words

        :param count: int, how many words you want, 0 means a random amount (at most 20)
        :param as_str: bool, True to return as string, false to return as list of words
        :param words: list, a list of words to choose from, defaults to unicode + ascii words
        :returns: str|list, your requested words
        '''
        min_size, max_size = self.get_bounds(
            min_size=kwargs.get("min_size", 0),
            max_size=kwargs.get("max_size", 0),
        )

        # since we specified we didn't care, randomly choose how many words there should be
        count = self.get_size(
            count=count,
            default_min_count=1,
            default_max_count=20,
            min_count=kwargs.get("min_count", 0),
            max_count=kwargs.get("max_count", 0),
        )

        count = max(count, max_size)

        if not words:
            words = _words

        while count > len(words):
            words += words

        ret_words = random.sample(words, count)

        if as_str:
            ret_words = " ".join(ret_words)
            if max_size:
                tw = String(ret_words).truncate(size=max_size, postfix="")
                if len(ret_words) < min_size or len(ret_words) > max_size:
                    tw = ret_words[:self.get_size(min_size, max_size)]
                ret_words = tw

        return ret_words

    def get_word_list(self, count=0, words=None, **kwargs):
        return self.get_words(count=count, as_str=False, words=words, **kwargs)

    def get_word(self, words=None):
        return self.get_words(1, as_str=True, words=words)

    def get_lines(self, count=0, as_str=True, words=None, **kwargs):
        min_size, max_size = self.get_bounds(
            min_size=kwargs.get("min_size", 0),
            max_size=kwargs.get("max_size", 0),
        )

        # since we specified we didn't care, randomly choose how many words there should be
        count = self.get_size(
            count=count,
            default_min_count=1,
            default_max_count=20,
            min_count=kwargs.get("min_count", 0),
            max_count=kwargs.get("max_count", 0),
        )

        if not words:
            words = _words

        ret_lines = []
        for i in range(count):
            if self.yes(0.75):
                ret_lines.append(self.get_words(as_str=True, words=words))
            else:
                ret_lines.append("\n")


        if as_str:
            ret_lines = "\n".join(ret_lines)
            if max_size:
                tw = String(ret_lines).truncate(size=max_size, postfix="")
                if len(ret_words) < min_size or len(ret_words) > max_size:
                    tw = ret_lines[:self.get_size(min_size, max_size)]
                ret_lines = tw

        return ret_lines

    def get_ascii_lines(self, count=0, as_str=True, **kwargs):
        return self.get_lines(count, as_str, words=_ascii_words, **kwargs)

    def get_unicode_lines(self, count=0, as_str=True, **kwargs):
        return self.get_lines(count, as_str, words=_unicode_words, **kwargs)
    get_uni_lines = get_unicode_lines

