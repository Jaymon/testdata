# -*- coding: utf-8 -*-
import re

from testdata.compat import *
from . import TestCase, testdata


class UserTest(TestCase):
    def test_get_phone(self):
        ph = testdata.get_phone()
        self.assertRegex(ph, r"\d{3}-\d{3}-\d{4}")

        ph = testdata.get_phone("+{country_code}-{area_code}-{exchange_code}-{line_number}")
        self.assertRegex(ph, r"\+\d-\d{3}-\d{3}-\d{4}")

        ph = testdata.get_phone(line_number="5555")
        self.assertTrue(ph.endswith("-5555"))

    def test_get_usa_address(self):
        a = testdata.get_usa_address()
        self.assertEqual(a[0], a.street)
        self.assertEqual(a[0], a.address1)
        self.assertEqual(a[1], a.section)
        self.assertEqual(a[1], a.address2)
        self.assertEqual(a[2], a.city)
        self.assertEqual(a[3], a.state)
        self.assertEqual(a[4], a.zipcode)
        self.assertEqual(a[5], a.line)
        self.assertEqual(a[6], a.lines)

    def test_get_names(self):
        fname = testdata.get_first_name()
        fname = testdata.get_first_name("male")
        fname = testdata.get_first_name("m")
        fname = testdata.get_first_name("female")
        fname = testdata.get_first_name("f")
        fname = testdata.get_first_name(True)
        fname = testdata.get_first_name(1)
        fname = testdata.get_first_name(2)
        fname = testdata.get_first_name(False)

        fname = testdata.get_first_name(is_unicode=True)
        self.assertUnicode(fname)
        fname = testdata.get_first_name(is_unicode=False)
        self.assertAscii(fname)

        lname = testdata.get_last_name()
        lname = testdata.get_last_name(is_unicode=True)
        self.assertUnicode(lname)
        lname = testdata.get_last_name(is_unicode=False)
        self.assertAscii(lname)

        name = testdata.get_name(is_unicode=True)
        self.assertUnicode(name)
        name = testdata.get_name(is_unicode=False)
        self.assertAscii(name)

        for x in range(100):
            fname = testdata.get_first_name()
            self.assertFalse(re.search(r"\s+", fname))

            fname = testdata.get_ascii_first_name()
            self.assertFalse(re.search(r"\s+", fname))

    def test_get_ascii_name(self):
        name = testdata.get_ascii_name()
        self.assertGreater(len(name), 0)
        if is_py2:
            name.decode('utf-8') # this should not fail because the string is ascii
        elif is_py3:
            bytes(name, encoding="ascii").decode('utf-8')

    def test_get_unicode_name(self):
        name = testdata.get_unicode_name()
        self.assertGreater(len(name), 0)
        with self.assertRaises(UnicodeEncodeError):
            if is_py2:
                name.decode('utf-8')
            elif is_py3:
                bytes(name, encoding="ascii").decode('utf-8')

    def test_get_name(self):
        name = testdata.get_name()
        self.assertEqual(1, len(re.findall(r'\s+', name)))

        name = testdata.get_name(as_str=False)
        self.assertEqual(2, len(name))

        name = testdata.get_name(name_count=0)
        self.assertNotEqual(u"", name)

        name = testdata.get_name(name_count=1)
        self.assertNotEqual(u"", name)

    def test_get_unique_email(self):
        email = testdata.get_unique_email()
        self.assertFalse(" " in email)

    def test_get_email(self):
        email = testdata.get_email()
        self.assertGreater(len(email), 0)
        self.assertTrue("'" not in email)
        self.assertTrue("-" not in email)

        email = testdata.get_email("foo")
        self.assertTrue(email.startswith("foo"))

        email = testdata.get_email("foo'bar")
        self.assertTrue(email.startswith("foobar"))

