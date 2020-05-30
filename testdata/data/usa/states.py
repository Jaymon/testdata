# -*- coding: utf-8 -*-
from __future__ import unicode_literals, division, print_function, absolute_import
import collections


class States(collections.OrderedDict):
    """
    States Readonly Map.

    Adds `id` to state dict (ascending alphabetical order index).
    Add lookup by `name`.
    add lookup by `abbr`.
    """
    @property
    def names(self):
        """return just the full names of the supported states"""
        return [d["name"] for d in self.values()]

    @property
    def abbrs(self):
        """return just the abbreviations of the supported states"""
        return [d["abbr"] for d in self.values()]

    def __init__(self):
        vals = [
            {'name': 'Alabama', 'abbr': 'AL'},
            {'name': 'Alaska', 'abbr': 'AK'},
            {'name': 'Arizona', 'abbr': 'AZ'},
            {'name': 'Arkansas', 'abbr': 'AR'},
            {'name': 'California', 'abbr': 'CA'},
            {'name': 'Colorado', 'abbr': 'CO'},
            {'name': 'Connecticut', 'abbr': 'CT'},
            {'name': 'Delaware', 'abbr': 'DE'},
            {'name': 'District of Columbia', 'abbr': 'DC'}, # Not a state
            {'name': 'Florida', 'abbr': 'FL'},
            {'name': 'Georgia', 'abbr': 'GA'},
            {'name': 'Hawaii', 'abbr': 'HI'},
            {'name': 'Idaho', 'abbr': 'ID'},
            {'name': 'Illinois', 'abbr': 'IL'},
            {'name': 'Indiana', 'abbr': 'IN'},
            {'name': 'Iowa', 'abbr': 'IA'},
            {'name': 'Kansas', 'abbr': 'KS'},
            {'name': 'Kentucky', 'abbr': 'KY'},
            {'name': 'Louisiana', 'abbr': 'LA'},
            {'name': 'Maine', 'abbr': 'ME'},
            {'name': 'Maryland', 'abbr': 'MD'},
            {'name': 'Massachusetts', 'abbr': 'MA'},
            {'name': 'Michigan', 'abbr': 'MI'},
            {'name': 'Minnesota', 'abbr': 'MN'},
            {'name': 'Mississippi', 'abbr': 'MS'},
            {'name': 'Missouri', 'abbr': 'MO'},
            {'name': 'Montana', 'abbr': 'MT'},
            {'name': 'Nebraska', 'abbr': 'NE'},
            {'name': 'Nevada', 'abbr': 'NV'},
            {'name': 'New Hampshire', 'abbr': 'NH'},
            {'name': 'New Jersey', 'abbr': 'NJ'},
            {'name': 'New Mexico', 'abbr': 'NM'},
            {'name': 'New York', 'abbr': 'NY'},
            {'name': 'North Carolina', 'abbr': 'NC'},
            {'name': 'North Dakota', 'abbr': 'ND'},
            {'name': 'Ohio', 'abbr': 'OH'},
            {'name': 'Oklahoma', 'abbr': 'OK'},
            {'name': 'Oregon', 'abbr': 'OR'},
            {'name': 'Pennsylvania', 'abbr': 'PA'},
            {'name': 'Rhode Island', 'abbr': 'RI'},
            {'name': 'South Carolina', 'abbr': 'SC'},
            {'name': 'South Dakota', 'abbr': 'SD'},
            {'name': 'Tennessee', 'alt': ['Tennesee'], 'abbr': 'TN'},
            {'name': 'Texas', 'abbr': 'TX'},
            {'name': 'Utah', 'abbr': 'UT'},
            {'name': 'Vermont', 'abbr': 'VT'},
            {'name': 'Virginia', 'abbr': 'VA'},
            {'name': 'Washington', 'abbr': 'WA'},
            {'name': 'West Virginia', 'abbr': 'WV'},
            {'name': 'Wisconsin', 'abbr': 'WI'},
            {'name': 'Wyoming', 'abbr': 'WY'},
        ]

        super(States, self).__init__()
        self.update(vals)

    def normalize(self, k):
        """given a key k that can be id, name or abbr, return the full name"""
        if k:
            name = None
            try:
                name = self.lookup_keys[k.upper()]

            except (AttributeError, KeyError):
                try:
                    name = self.lookup_keys[k]

                except (TypeError, KeyError):
                    for key in ["abbr", "name"]:
                        if key in k:
                            name = self.normalize(k[key])
                            break
                    if name is None:
                        raise KeyError("Could not normalize {}".format(k))

        else:
            raise KeyError("no valid key to normalize")

        return name

    def __getitem__(self, k):
        nk = self.normalize(k)
        return super(States, self).__getitem__(nk)

    def __contains__(self, k):
        try:
            nk = self.normalize(k)
            ret = super(States, self).__contains__(nk)
        except KeyError:
            ret = False

        return ret

    def get(self, k, dv=None):
        try:
            v = self[k]
        except KeyError:
            v = dv

        return v

    def update(self, vals):
        self.is_readonly = False
        self.clear() # we start fresh on any update
        self.lookup_keys = {}
        args = []
        for i, v in enumerate(vals, 1):
            v["id"] = i
            args.append((v["name"], v))

            # build the lookup table
            self.lookup_keys[i] = v["name"]
            self.lookup_keys[v["name"].upper()] = v["name"]
            self.lookup_keys[v["abbr"].upper()] = v["name"]
            for alt in v.get("alt", []):
                self.lookup_keys[alt.upper()] = v["name"]

        super(States, self).update(args)
        self.is_readonly = True

    def __setitem__(self, k, v):
        if self.is_readonly:
            raise NotImplementedError()
        return super(States, self).__setitem__(k, v)

    def clear(self):
        if self.is_readonly:
            raise NotImplementedError()
        return super(States, self).clear()

    def pop(self, k, *args, **kwargs):
        raise NotImplementedError()
    def __delitem__(self, k):
        raise NotImplementedError()
    def viewitems(self):
        raise NotImplementedError()
    def viewvalues(self):
        raise NotImplementedError()
    def viewkeys(self):
        raise NotImplementedError()

    def is_valid_state(self, state):
        if state in self:
            if self[state]['abbr'] != "NR":  # "Non-US Resident"
                return True
        return False


states = States()

