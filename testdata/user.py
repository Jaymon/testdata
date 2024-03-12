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
from .data.countries import country_lookup

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
        """Returns just a non-space ascii name, this is a very basic username
        generator"""
        if not name:
            if self.yes():
                name = self.get_ascii_first_name()

            else:
                name = self.get_ascii_last_name()

        name = re.sub(r"['-]", "", name)
        return name

    def get_unique_email_address(self, name=''):
        name = self.get_username(name)
        timestamp = "{:.6f}".format(time.time()).replace(".", "")
        return self.get_email_address(name + timestamp)
    get_uniq_email_address = get_unique_email_address

    def get_email_address(self, name=''):
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

    def get_password(self, **kwargs):
        """Get a user password

        :param **kwargs:
            * upper: bool, password should have an upper-case character
            * lower: bool, password should have a lower-case character
            * digit: bool, password should have a numeric digit character
            * special: bool, password should contain a punctuation character
            * unicode: bool, password should have a non-ascii character
        :returns: str, the password
        """
        password = []

        chars = set()
        for k in ["upper", "lower", "digit", "special", "unicode"]:
            if kwargs.get(k, True):
                chars.add(k)

        def get_char(k):
            if k == "upper":
                ch = self.get_char(chars=String.ASCII_UPPERCASE)

            elif k == "lower":
                ch = self.get_char(chars=String.ASCII_LOWERCASE)

            elif k == "digit":
                ch = self.get_digits(1)

            elif k == "special":
                ch = self.get_punctuation(1)

            elif k == "unicode":
                ch = random.choice(self.get_unicode_word())

            return ch

        kwargs.setdefault("default_min", len(chars) * 3)
        kwargs.setdefault("default_max", len(chars) * 20)
        str_size = self.get_size(**kwargs)

        for k in chars:
            password.append(get_char(k))
            str_size -= 1

        if str_size < 0:
            raise ValueError(
                "Cannot generate password with passed in settings"
            )

        for index in range(str_size):
            k = self.choice(chars)
            password.append(get_char(k))

        return "".join(password)

    def get_ipv4_address(self, **kwargs):
        """Generate an ip4 address

        https://en.wikipedia.org/wiki/Internet_Protocol_version_4

        :param **kwargs:
            * country: str, usually a 2 character country code (eg, "US")
            * octets: dict[int, str|int], a dict with keys 1, 2, 3, or 4 only,
                representing the octet value (eg, {1: 127} means the ip will
                start with "127.").

                I got the octet name from:

                    https://en.wikipedia.org/wiki/Octet_(computing)#Use_in_Internet_Protocol_addresses
        :returns: str, the ip4 address with 4 octets separated by periods
        """
        ip = []

        octets = kwargs.get(
            "octets",
            kwargs.get(
                "groups",
                kwargs.get(
                    "parts",
                    {}
                )
            )
        )

        if country_code := kwargs.get("country", ""):
            country_info = country_lookup[country_code]
            octets[1] = self.choice(country_info["ips"])

        for k in range(1, 5):
            i = octets.get(k, self.randint(1, 999))
            ip.append(str(i))

        return ".".join(ip)
    get_ip4_address = get_ipv4_address
    get_ipv4 = get_ipv4_address
    get_ip4 = get_ipv4_address

    def get_ipv6_address(self, **kwargs):
        """Generate an ip6 address

        https://en.wikipedia.org/wiki/IPv6

            IPv6 addresses are represented as eight groups of four hexadecimal
            digits each, separated by colons. The full representation may be
            shortened; for example, 2001:0db8:0000:0000:0000:8a2e:0370:7334
            becomes 2001:db8::8a2e:370:7334

        :param **kwargs:
            * hextets: dict[int, str|int], a dict with keys 1-8 only,
                representing the hextet value (eg, {1: "effe"} means the ip
                will start with "effe:").

                I got the hextet name from:

                    https://en.wikipedia.org/wiki/Octet_(computing)#Use_in_Internet_Protocol_addresses
        :returns: str, the ip6 address with 8 hextets separated by colons
        """
        ip = []

        hextets = kwargs.get(
            "hextets",
            kwargs.get(
                "groups",
                kwargs.get(
                    "parts",
                    {}
                )
            )
        )

        for k in range(1, 9):
            ip.append(hextets.get(k, self.get_hex(4)))

        return ":".join(ip)
    get_ip6_address = get_ipv6_address
    get_ipv6 = get_ipv6_address
    get_ip6 = get_ipv6_address

    def get_version(self, **kwargs):
        """Get a semver version

        In it's simplest version, a semver version consists of:

            <MAJOR>.<<MINOR>[.<PATCH>]

        But this can also generate python's more elaborate versions

        https://peps.python.org/pep-0440/

            [N!]N(.N)*[{a|b|rc}N][.postN][.devN]

            Public version identifiers are separated into up to five segments:

                * Epoch segment: N!
                * Release segment: N(.N)*
                * Pre-release segment: {a|b|rc}N
                * Post-release segment: .postN
                * Development release segment: .devN

        https://semver.org/

        :param **kwargs:
            * major: str|int, the major version fragment
            * minor: str|int, the minor version fragment
            * patch: str|int, the patch version fragment
            * is_pre: bool, generate pre-release version fragment
            * pre: str, pre-release version fragment
            * is_post: bool, generate post-release version fragment
            * post: str, post-release version fragment
            * is_dev: bool, generate dev version fragment
            * dev: str, dev-release version fragment
            * is_local: bool, generate local version fragment, joined to
                version with a plus (+) sign
            * local: str, local version fragment
        :returns: str, the version, by default it returns what is considered a
            final version which is a standard semver version
        """
        version = str(kwargs.get("major", self.randint(1, 99)))
        version += "." + str(kwargs.get("minor", self.randint(1, 99)))

        if patch := kwargs.get("patch", kwargs.get("micro", "")):
            version += f".{patch}"

        elif self.yes():
            version += ".{}".format(self.randint(1, 999))

        if p := kwargs.get("pre", ""):
            version += f".{p}"

        elif kwargs.get("is_pre", False):
            version += ".{}{}".format(
                self.choice(["a", "b", "rc"]),
                self.randint(1, 9999)
            )

        if p := kwargs.get("post", ""):
            version += f".{p}"

        elif kwargs.get("is_post", False):
            version += ".post{}".format(
                self.randint(1, 9999)
            )

        if p := kwargs.get("dev", ""):
            version += f".{p}"

        elif kwargs.get("is_dev", False):
            version += ".dev{}".format(
                self.randint(1, 9999)
            )

        if p := kwargs.get("local", ""):
            version += f"+{p}"

        elif kwargs.get("is_local", False):
            version += "+{}".format(
                self.get_str(chars=String.ALPHANUMERIC + ".")
            )

        return version
    get_semver = get_version

