# -*- coding: utf-8 -*-

from ..compat import *
from ..base import TestData


###############################################################################
# testdata functions
###############################################################################
class MappingData(TestData):
    def get_dict(self, *keys, **kwargs):
        """Create a dict filled with key/values returned from kv

        https://github.com/Jaymon/testdata/issues/73

        :example:
            d = testdata.get_dict(
                {"foo": "value", "bar": testdata.get_float},
                "che"
            )
            print(d["foo"]) # "value
            print(d["bar"]) # N.NN
            print(d["che"]) # random value

            # dict will have random keys and values
            testdata.get_dict()

            # dict will at least have: "foo", "bar", and "che" keys
            testdata.get_dict("foo", "bar", "che")

        :param *keys: one or more strings representing keys the dict should
            have, if the value is a dict it will be merged with all the keys,
            everything else will be set as the key value
        :param **kv: each key/callable will be used to generate a random dict
            key/val. If key/Any then the final dict will have that key/value
        :returns: dict, the randomly generated dict
        """
        ret = {}

        kwargs.setdefault("default_max", 5)
        size = self.get_size(**kwargs)
        kv = {}

        if keys:
            for k in keys:
                if isinstance(k, Mapping):
                    kv.update(k)

                else:
                    if self.yes():
                        kv[k] = lambda: self.get_words(5)

                    else:
                        kv[k] = self.get_int

        for x in self.get_range(max(size - len(kv), 0)):
            k = self.get_ascii_string()
            if self.yes():
                kv[k] = lambda: self.get_words(5)

            else:
                kv[k] = self.get_int

        for k, callback in kv.items():
            if callable(callback):
                ret[k] = callback()

            else:
                ret[k] = callback

        return ret

    def find_value(self, needle, haystack, *default):
        if isinstance(haystack, Mapping):
            if needle in haystack:
                return haystack[needle]

            else:
                for hay in haystack.values():
                    try:
                        return self.find_value(needle, hay)

                    except (AttributeError, ValueError):
                        pass

        elif isinstance(haystack, basestring):
            pass

        elif isinstance(haystack, Sequence):
            for hay in haystack:
                try:
                    return self.find_value(needle, hay)

                except (AttributeError, ValueError):
                    pass

        else:
            try:
                return getattr(haystack, needle)

            except (AttributeError, ValueError):
                pass

        if default:
            return default[0]

        else:
            raise ValueError(f"Could not find a value for {needle}")

