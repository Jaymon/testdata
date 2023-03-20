# -*- coding: utf-8 -*-
import random

from datatypes import make_list, Dict

from ..compat import *
from ..base import TestData


###############################################################################
# testdata functions
###############################################################################
class SequenceData(TestData):
    def get_list(self, callback, max_size=100, **kwargs):
        """Create a list filled with values returned from callback

        https://github.com/Jaymon/testdata/issues/73

        :param callback: callable, each item in the list will be populated by calling this
        :param max_size: int, the maximum size of the list
        :returns: list, the randomly generated list
        """
        ret = []
        for x in self.get_range(max_size, **kwargs):
            ret.append(callback())
        return ret

    def choice(self, *args, **kwargs):
        """Wrapper around random.choice that makes sure everything is a list, handy
        for python 3 code where you have to wrap a lot of generators in list(...)

        :param *args: iter(s), one or more iterators or lists that will all be combined
            into one giant list
        :param exclude: list, a list of values that shouldn't be selected from *args
        :returns: a single object from all the *args
        """
        exclude = kwargs.pop("exclude", None)
        exclude = set(exclude) if exclude else set()
        vals = make_list(args)

        if exclude:
            vals = list(set(vals).difference(exclude))
            if not vals:
                raise ValueError("No more choices left")

        ret = random.choice(vals)

        return ret
    choose = choice
    get_choice = choice

    def choices(self, *args, **kwargs):
        """Wrapper around random.choices that makes sure all *args are sequences

        https://docs.python.org/3/library/random.html#random.choices

        :param *args: iter(s), one or more sequences that will be combined and chosen
            from
        :param **kwargs:
            k: how many values to choose from *args
            count: alias of k
            weights: check docs, passed through to random.choices()
            cum_weights: check docs, passed through to random.choices()
        :returns: list, k values from *args
        """
        kwargs = Dict(kwargs)
        k = kwargs.pops(["k", "count"], 1)
        population = make_list(args)
        weights = kwargs.pop("weights", None)
        cum_weights = kwargs.pop("cum_weights", None)
        return random.choices(
            population,
            weights=weights,
            cum_weights=cum_weights,
            k=k,
        )
    get_choices = choices

