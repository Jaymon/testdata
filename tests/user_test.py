# -*- coding: utf-8 -*-
import re

from testdata.compat import *
from testdata.data.countries import COUNTRY_CODE_TO_IP
from . import TestCase, testdata


class UserTest(TestCase):
    def test_get_phone(self):
        ph = testdata.get_phone()
        self.assertRegex(ph, r"\d{3}-\d{3}-\d{4}")

        ph = testdata.get_phone(
            "+{country_code}-{area_code}-{exchange_code}-{line_number}"
        )
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
        bytes(name, encoding="ascii").decode('utf-8')

    def test_get_unicode_name(self):
        name = testdata.get_unicode_name()
        self.assertGreater(len(name), 0)
        with self.assertRaises(UnicodeEncodeError):
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

    def test_get_unique_email_address(self):
        email = testdata.get_unique_email_address()
        self.assertFalse(" " in email)

    def test_get_email_address(self):
        email = testdata.get_email_address()
        self.assertGreater(len(email), 0)
        self.assertTrue("'" not in email)
        self.assertTrue("-" not in email)

        email = testdata.get_email_address("foo")
        self.assertTrue(email.startswith("foo"))

        email = testdata.get_email_address("foo'bar")
        self.assertTrue(email.startswith("foobar"))

    def test_get_ipv4_address(self):
        ip = self.get_ipv4_address()
        self.assertIsNotNone(ip)
        self.assertEqual(3, ip.count("."))

        ip = self.get_ipv4_address(octets={1: 800, 3: 900})
        self.assertTrue("800." in ip)
        self.assertTrue(".900." in ip)

        country_code = self.choice(COUNTRY_CODE_TO_IP)
        ip = self.get_ipv4_address(country=country_code)
        self.assertTrue(
            int(ip.split(".", 1)[0]) in COUNTRY_CODE_TO_IP[country_code]
        )

    def test_get_ipv6_address(self):
        ip = self.get_ipv6_address()
        self.assertIsNotNone(ip)
        self.assertEqual(7, ip.count(":"))

        ip = self.get_ipv6_address(hextets={1: "effe"})
        self.assertTrue(ip.startswith("effe:"))

    def test_get_password(self):
        p = self.get_password()
        self.assertIsNotNone(p)

        p = self.get_password(digit=False)
        self.assertIsNotNone(p)

        p = self.get_password(digit=False, lower=False)
        self.assertIsNotNone(p)

    def test_get_version(self):
        v = self.get_version()
        self.assertIsNotNone(v)

        v = self.get_version(is_pre=True)
        self.assertIsNotNone(v)

        v = self.get_version(is_pre=True, is_local=True)
        self.assertIsNotNone(v)

        v = self.get_version(is_pre=True, is_dev=True)
        self.assertIsNotNone(v)

