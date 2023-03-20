# -*- coding: utf-8 -*-
import random
import sys
import itertools

from datatypes import Dict, HotSet

from ..compat import *
from ..config import environ
from ..base import TestData


###############################################################################
# testdata functions
###############################################################################
class NumberData(TestData):

    # used in the get_unique_int() function to make sure it never returns the same int twice
    # this is a possible memory leak if you are using this script in a very long running
    # process using get_int(), since this list will get bigger and bigger and never
    # be flushed, but seriously, you should just use get_int() or random.randint() in any
    # long running scripts. In order to minimize the memory leak we cap the list at
    # environ.MAX_UNIQUE unique values
    _previous_ints = HotSet(environ.MAX_UNIQUE)

    # similar to _previous_ints, used in get_unique_float() function
    _previous_floats = HotSet(environ.MAX_UNIQUE)

    def get_bounds(self, *args, **kwargs):
        kwargs = Dict(kwargs)
        start = kwargs.pop(
            "default_start",
            kwargs.pops(["default_min", "default_min_size", "default_min_count"], 0)
            #kwargs.pop("default_min", kwargs.pop("default_min_size", kwargs.pop("default_min_count", 0)))
        )
        stop = kwargs.pop(
            "default_stop",
            kwargs.pops(["default_max", "default_max_size", "default_max_count"], 0)
            #kwargs.pop("default_max", kwargs.pop("default_max_size", kwargs.pop("default_max_count", 0)))
        )

        if len(args) == 1:
            start = args[0]
            stop = args[0]

        elif len(args) > 1:
            start = args[0]
            stop = args[1]

        else:
            for k, v in kwargs.items():
                if v:
                    if k.startswith("min"):
                        start = v

                    elif k.startswith("max"):
                        stop = v

                    elif "count" in k or "size" in k:
                        start = v
                        stop = v

        if stop < start:
            stop = start

        return (start, stop)

    def randint(self, *args, **kwargs):
        """passthrough to random.ranint to make it so other TestData subclasses
        don't have to import random"""
        return random.randint(*args, **kwargs)

    def get_size(self, *args, **kwargs):
        start, stop = self.get_bounds(*args, **kwargs)
        if start == 0 and stop == 0:
            start = 1
            stop = self.get_int(start, 50)
        return random.randint(start, stop)

    def get_full_float(self, min_size=None, max_size=None):
        """return a random float

        sames as the random method but automatically sets min and max

        :param min_size: float, the minimum float size you want
        :param max_size: float, the maximum float size you want
        :returns: float, a random value between min_size and max_size
        """
        float_info = sys.float_info
        if min_size is None:
            min_size = float_info.min
        if max_size is None:
            max_size = float_info.max
        return random.uniform(min_size, max_size)

    def get_float(self, min_size=0.000001, max_size=None):
        """This used to be .get_full_float() but it turns out when I request a
        float I almost always want a positive float"""
        return self.get_full_float(min_size=min_size, max_size=max_size)

    def get_posfloat(self, max_size=None):
        """Similar to get_float but the random float will always be positive

        :param max_size: float, the maximum float size
        :returns: float, a random float between 0.0 and max_size
        """
        return self.get_float(0.0, max_size)
    get_positive_float = get_posfloat
    get_positivefloat = get_posfloat

    def get_unique_float(self, min_size=None, max_size=None):
        '''
        get a random unique float

        no different than random.uniform() except it automatically can set range, and
        guarrantees that no 2 floats are the same

        return -- float
        '''
        i = 0;
        while True:
            i = self.get_float(min_size, max_size)
            if i not in self._previous_floats:
                self._previous_floats.add(i)
                break

        return i
    get_uniq_float = get_unique_float

    def get_digits(self, count, n=None):
        """return a string value that contains count digits

        :param count: int, how many digits you want, so if you pass in 4, you would get
            4 digits
        :param n: int, if you already have a value and want it to for sure by count digits
        :returns: string, this returns a string because the digits might start with
            zero
        """
        max_size = int("9" * count)

        if n is None:
            n = self.get_int(0, max_size)
        else:
            if n > max_size:
                raise ValueError("n={} has more than {} digits".format(n, count))

        ret = "{{:0>{}}}".format(count).format(n)
        return ret
    get_digit = get_digits
    get_count_digits = get_digits

    def get_full_int(self, min_size=None, max_size=None):
        """This will get a random integer through the full range of integers, which
        means the value can be negative"""
        if min_size is None:
            min_size = -sys.maxsize - 1

        if max_size is None:
            max_size = sys.maxsize

        return random.randint(min_size, max_size)

    def get_posint(self, max_size=2**31-1):
        """just return a positive 32-bit integer, this is basically a wrapper around
        random.randint where you don't have to specify a minimum (or a maximum if you
        don't want)
        """
        min_size = 1
        return random.randint(min_size, max_size)
    get_positive_int = get_posint
    get_positive_integer = get_posint
    get_posinteger = get_posint
    get_pint = get_posint

    def get_int(self, min_size=1, max_size=2**31-1):
        return self.get_full_int(min_size=min_size, max_size=max_size)
    get_integer=get_int

    def get_int32(self, min_size=1):
        """returns a 32-bit positive integer"""
        return random.randint(min_size, 2**31-1)
    get_integer32=get_int32
    get_int4=get_int32

    def get_int64(self, min_size=1):
        """returns up to a 64-bit positive integer"""
        return random.randint(min_size, 2**63-1)
    get_integer64=get_int64
    get_int8 = get_int64
    get_bigint = get_int64

    def get_unique_int(self, min_size=1, max_size=sys.maxsize):
        '''
        get a random unique integer

        no different than random.randint except that it guarrantees no int will be
        the same, and also you don't have to set a range, it will default to all max
        int size

        return -- integer 
        '''
        i = 0;
        found = False
        max_count = max_size - min_size
        for x in range(max_count):
            i = random.randint(min_size, max_size)
            if i not in self._previous_ints:
                found = True
                self._previous_ints.add(i)
                break

        if not found:
            raise ValueError("no unique ints from {} to {} could be found".format(min_size, max_size))
        return i
    get_uniq_int = get_unique_int
    get_uniq_integer = get_unique_int
    get_unique_integer = get_unique_int

    def get_long(self, min_size=1, max_size=None):
        """Get a really big int, by default this will top out at Ethereum's BigNumber,
        which is 78 chars long"""
        if max_size is None:
            max_size = int("9" * self.get_size(len(str(min_size)), 78))
        return self.get_int(min_size=min_size, max_size=max_size)
    get_massive_int = get_long
    get_bignumber = get_long

    def get_counter(self, start=1, step=1):
        """Because sometimes you just want to count, this is just a wrapper around
        itertools.count

        :Example:
            c = testdata.get_counter()
            c() # 1
            c() # 2
            c() # 3

        :param start: int, the number to start at
        :param step: int, the increment each time the callback is called
        :returns: callable, everytime you invoke it it will increment by step
        """
        counter = itertools.count(start, step)
        return lambda: next(counter)

    def get_range(self, max_size=10, **kwargs):
        """Because sometimes you just want a random range

        https://github.com/Jaymon/testdata/issues/74

        :param max_size: int, the max range stop value you want
        :returns: range that can be iterated
        """
        start, stop = self.get_bounds(
            max_size=max_size,
            default_min_size=1 if self.yes() else 0,
            **kwargs
        )

#         if self.yes():
#             start = 1
#             stop = self.get_int(1, max_size + 1)
# 
#         else:
#             start = 0
#             stop = self.get_int(max_size=max_size)

        return range(start, stop)

    def get_coordinate(self, v1, v2, round_to=7):
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

        min_vs = v1
        max_vs = v2
        if v1[0] > v2[0]:
            min_vs = v2
            max_vs = v1

        min_size = min_vs[0]
        min_scale_range = [min_vs[1], scale_max]

        max_size = max_vs[0]
        max_scale_range = [0, max_vs[1]]

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
    get_coord = get_coordinate

    def yes(self, specifier=0):
        """
        Decide if we should perform this action, this is just a simple way to do something
        I do in tests every now and again

        :Example:
            # EXAMPLE -- simple yes or no question
            if testdata.yes():
                # do this
            else:
                # don't do it

            # EXAMPLE -- multiple choice
            choice = testdata.yes(3)
            if choice == 1:
                # do the first thing
            elif choice == 2:
                # do the second thing
            else:
                # do the third thing

            # EXAMPLE -- do something 75% of the time
            if testdata.yes(0.75):
                # do it the majority of the time
            else:
                # but every once in a while don't do it

        https://github.com/Jaymon/testdata/issues/8

        :param specifier: int|float, if int, return a value between 1 and specifier.
            if float, return 1 approximately specifier percent of the time, return 0
            100% - specifier percent of the time
        :returns: integer, usually 1 (True) or 0 (False)
        """
        if specifier:
            if isinstance(specifier, int):
                choice = random.randint(1, specifier)

            else:
                if specifier < 1.0:
                    specifier *= 100.0

                specifier = int(specifier)
                x = random.randint(0, 100)
                choice = 1 if x <= specifier else 0

        else:
            choice = random.choice([0, 1])

        return choice

    def get_bool(self):
        """Returns either True or False randomly"""
        return random.choice([True, False])

