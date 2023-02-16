# -*- coding: utf-8 -*-
import re
import random
import string
import time

from datatypes import String

from .compat import *
from .data import (
    _unicode_names,
    _first_names_male,
    _first_names_female,
    _last_names,
    usa,
)
from .base import TestData


class Address(tuple):
    @property
    def street(self):
        return self[0]

    @property
    def address1(self):
        return self.street

    @property
    def section(self):
        return self[1]

    @property
    def address2(self):
        return self.section

    @property
    def city(self):
        return self[2]

    @property
    def state(self):
        return self[3]

    @property
    def zipcode(self):
        return self[4]

    @property
    def line(self):
        line = self.street
        if self.section:
            line += " " + self.section
        line += ", " + self.city + ", " + self.state + " " + self.zipcode
        return line

    @property
    def lines(self):
        lines = [self.street]
        if self.section:
            lines.append(self.section)
        lines.append("{}, {}".format(self.city, self.state))
        lines.append(self.zipcode)
        lines = "\n".join(lines)
        return lines

    def __new__(cls, *values):
        return super().__new__(cls, values)

    def __getitem__(self, i):
        if i == 5:
            ret = self.line

        elif i == 6:
            ret = self.lines

        else:
            ret = super().__getitem__(i)

        return ret

    def __str__(self):
        return self.line


###############################################################################
# testdata functions
###############################################################################
class UserData(TestData):
    def get_username(self, name=""):
        """Returns just a non-space ascii name, this is a very basic username generator"""
        if not name:
            name = self.get_ascii_first_name() if self.yes() else self.get_ascii_last_name()
        name = re.sub(r"['-]", "", name)
        return name

    def get_unique_email(self, name=''):
        name = self.get_username(name)
        timestamp = "{:.6f}".format(time.time()).replace(".", "")
        return self.get_email(name + timestamp)
    get_uniq_email = get_unique_email

    def get_email(self, name=''):
        '''return a random email address'''
        name = self.get_username(name)
        email_domains = [
            "yahoo.com",
            "hotmail.com",
            "outlook.com",
            "aol.com",
            "gmail.com",
            "msn.com",
            "comcast.net",
            "hotmail.co.uk",
            "sbcglobal.net",
            "yahoo.co.uk",
            "yahoo.co.in",
            "bellsouth.net",
            "verizon.com",
            "earthlink.net",
            "cox.net",
            "rediffmail.com",
            "yahoo.ca",
            "btinternet.com",
            "charter.net",
            "shaw.ca",
            "ntlworld.com",
            "gmx.com",
            "gmx.net",
            "mail.com",
            "mailinator.com"
        ]

        return '{}@{}'.format(name.lower(), random.choice(email_domains))

    def get_phone(self, number_format="{area_code}-{exchange_code}-{line_number}", **kwargs):
        """Get a phone number

        part names come from:

            https://www.freshworks.com/freshcaller-cloud-pbx/phone-numbers/us-area-codes/

        to do an international format:

            "+{country_code}-{area_code}-{exchange_code}-{line_number}"

        :param number_format: string, allows you to format the number how you want, each of the
            names (eg, area_code, exchange_code) corresponds to a value you can pass into
            **kwargs
        :param **kwargs: dict, any values you want to customize, if no keywords are passed
            in then it will be generated
        :returns: string, the phone number matching number_format
        """
        kwargs.setdefault("country_code", kwargs.pop("country", "1"))
        kwargs.setdefault("area_code", kwargs.pop("area", self.get_digits(3)))
        kwargs.setdefault("exchange_code", kwargs.pop("exchange", self.get_digits(3)))
        kwargs.setdefault("line_number", kwargs.pop("line", self.get_digits(4)))
        return number_format.format(**kwargs)
    get_phone_number = get_phone

    def get_street_address(self, house_number="", street="", **kwargs):
        address = []
        if not house_number:
            house_number = self.get_int(max_size=99999)

        address.append(String(house_number))

        if street:
            address.append(street)

        else:
            if "street_dir" in kwargs:
                address.append(kwargs["street_dir"])

            else:
                if self.yes():
                    address.append(random.choice([
                        "E", "East",
                        "W", "West",
                        "N", "North",
                        "S", "South",
                    ]))

            if "street_name" in kwargs:
                address.append(kwargs["street_name"])

            else:
                if self.yes():
                    address.append(self.get_ascii_words(max_count=3))
                else:
                    if self.yes():
                        address.append(self.get_ascii_name())
                    else:
                        address.append(self.get_ascii_last_name())

            if "street_type" in kwargs:
                address.append(kwargs["street_name"])

            else:
                if self.yes():
                    address.append(random.choice([
                        "Boulevard",
                        "Blvd",
                        "Road",
                        "RD",
                        "Rd",
                        "Street",
                        "st",
                        "st.",
                        "Lane",
                        "Ln",
                        "Drive",
                        "Dr",
                        "Dr.",
                        "Trail",
                        "Court",
                        "Ct",
                        "Ct.",
                        "Circle",
                        "Cir",
                        "Cir.",
                        "Pike",
                        "Highway",
                        "Hwy",
                        "Fwy",
                        "Avenue",
                        "Ave",
                        "Ave.",
                        "Terrace",
                        "Pkwy",
                        "Parkway",
                        "Place",
                    ]))

        return " ".join(address)

    def get_address_section(self, section="", **kwargs):
        if not section:
            section = []
            if self.yes():
                section.append(random.choice([
                    "Apt",
                    "Apt.",
                    "Apartment",
                    "Suite",
                    "Building",
                ]))

            number = String(self.get_int(max_size=9999))
            if self.yes():
                prefix = random.choice([
                    "#",
                    self.get_middle_initial(),
                ])

                number = "{}{}".format(prefix, number)

            section.append(number)
            section = " ".join(section)
        return section

    def get_usa_city(self, city="", **kwargs):
        if not city:
            city = random.choice(usa.cities)
        return city
    get_us_city = get_usa_city

    def get_usa_state(self, state="", **kwargs):
        if not state:
            if self.yes():
                state = random.choice(usa.states.names)
            else:
                state = random.choice(usa.states.abbrs)
        return state
    get_us_state = get_usa_state

    def get_usa_zipcode(self, state=""):
        state = self.get_usa_state(state)
        state = usa.states[state]["abbr"]
        return random.choice(usa.zipcodes[state])
    get_us_zipcode = get_usa_zipcode
    get_usa_zip = get_usa_zipcode
    get_us_zip = get_usa_zipcode

    def get_usa_address(self, **kwargs):
        """get an address that looks like it can be in the united states

        the generated addresses are not real but should hopefully look plausible

        https://en.wikipedia.org/wiki/Address#United_States

        :returns: named tuple(street, section, city, state, zipcode, line, lines) where
            line is a string of the address on one line and lines is the address on multiple
            lines
        """
        #Address = namedtuple("Address", ["street", "section", "city", "state", "zipcode", "line", "lines"])

        street = self.get_street_address(**kwargs)
        section = self.get_address_section(**kwargs) if self.yes() else ""
        city = self.get_usa_city(**kwargs)
        state = self.get_usa_state(**kwargs)
        zipcode = self.get_usa_zipcode(state)

        address = Address(
            street,
            section,
            city,
            state,
            zipcode,
        )

        return address
    get_us_address = get_usa_address
    get_us_addr = get_usa_address
    get_usa_addr = get_usa_address

    def get_name(self, name_count=2, as_str=True, is_unicode=None):
        '''
        get a random name

        link -- http://stackoverflow.com/questions/30485/what-is-a-reasonable-length-limit-on-person-name-fields

        name_count -- integer -- how many total name parts you want (eg, "Jay marcyes" = 2 name_count)
        as_str -- boolean -- True to return as string, false to return as list of names

        return -- unicode|list -- your requested name
        '''
        # since we specified we didn't care, randomly choose how many surnames there should be
        if name_count <= 0:
            name_count = random.randint(1, 5)

        is_unicode_bit = lambda x: random.randint(0, 100) < 20 if x is None else x

        # decide if we should hyphenate the last name
        names = []
        if name_count > 0:
            add_last_name = name_count > 1
            for x in range(max(1, name_count - 1)):

                if is_unicode_bit(is_unicode):
                    names.append(self.get_unicode_first_name())
                else:
                    names.append(self.get_ascii_first_name())

            if add_last_name:
                if is_unicode_bit(is_unicode):
                    names.append(self.get_unicode_last_name())
                else:
                    names.append(self.get_ascii_last_name())

        return names if not as_str else ' '.join(names)

    def get_ascii_name(self):
        '''return one ascii safe name'''
        return self.get_name(is_unicode=False)

    def get_unicode_name(self):
        '''return one non-ascii safe name'''
        return self.get_name(is_unicode=True)
    get_uni_name = get_unicode_name

    def get_first_name(self, gender="", is_unicode=None):
        genders = ["m", "f"]
        if gender:
            gender = str(gender).lower()[0]
            gender = "m" if gender == "1" else "f"
            gender = "m" if gender == "t" else "f"
            if gender not in genders:
                raise ValueError("Unsupported gender, try [m, f, male, female] instead")
        else:
            gender = random.choice(genders)

        if is_unicode is None:
            is_unicode = random.randint(0, 100) < 20

        if is_unicode:
            name = random.choice(_unicode_names)
        else:
            if gender == "m":
                name = random.choice(_first_names_male)
            else:
                name = random.choice(_first_names_female)

        if random.randint(0, 20) == 5:
            name = '{}-{}'.format(name, self.get_first_name(gender, is_unicode))

        return name.capitalize()
    get_given_name = get_first_name
    get_firstname = get_first_name

    def get_ascii_first_name(self, gender=""):
        '''return one ascii safe name'''
        return self.get_first_name(gender, is_unicode=False)
    get_ascii_given_name = get_ascii_first_name
    get_ascii_firstname = get_ascii_first_name

    def get_unicode_first_name(self, gender=""):
        '''return one non-ascii name'''
        return self.get_first_name(gender, is_unicode=True)
    get_uni_first_name = get_unicode_first_name
    get_unicode_given_name = get_unicode_first_name
    get_unicode_firstname = get_unicode_first_name

    def get_middle_initial(self, *args, **kwargs):
        """Returns just a capital letter"""
        return self.get_str(str_size=1, chars=string.ascii_uppercase)

    def get_middle_name(self, *args, **kwargs):
        """Get a middle name or initial"""
        middle_name = self.get_first_name(*args, **kwargs)
        if self.yes():
            middle_name = self.get_first_name(*args, **kwargs)
        else:
            middle_name = self.get_middle_initial()
        return middle_name
    get_middlename = get_middle_name

    def get_ascii_middle_name(self, gender=""):
        '''return one ascii safe name'''
        return self.get_middle_name(self, gender, is_unicode=False)
    get_ascii_middlename = get_middle_name

    def get_last_name(self, is_unicode=None):
        if is_unicode is None:
            is_unicode = random.randint(0, 100) < 20

        if is_unicode:
            name = random.choice(_unicode_names)
        else:
            name = random.choice(_last_names)

        if random.randint(0, 20) == 5:
            name = '{}-{}'.format(name, self.get_last_name(is_unicode))

        return name.capitalize()
    get_lastname = get_last_name
    get_surname = get_last_name

    def get_ascii_last_name(self):
        '''return one ascii safe name'''
        return self.get_last_name(is_unicode=False)
    get_ascii_lastname = get_ascii_last_name
    get_ascii_surname = get_ascii_last_name

    def get_unicode_last_name(self):
        '''return one unicode name'''
        return self.get_last_name(is_unicode=True)
    get_uni_last_name = get_unicode_last_name
    get_unicode_lastname = get_unicode_last_name
    get_unicode_surname = get_unicode_last_name

