# -*- coding: utf-8 -*-

from ..compat import *
from ..base import TestData


###############################################################################
# testdata functions
###############################################################################
class MappingData(TestData):
    def get_dict(self, *keys, **kv):
        """Create a dict filled with key/values returned from kv

        https://github.com/Jaymon/testdata/issues/73

        :param kv: dict, each key/callable will be used to generate a random dict key/val
        :returns: dict, the randomly generated dict
        """
        if keys:
            kv = {}
            for k in keys:
                kv[k] = (lambda: self.get_words(5)) if self.yes() else self.get_int

        if not kv:
            kv = {}
            for x in self.get_range(5):
                k = self.get_ascii_string()
                v = (lambda: self.get_words(5)) if self.yes() else self.get_int
                kv[k] = v

        ret = {}
        for k, callback in kv.items():
            ret[k] = callback()
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

