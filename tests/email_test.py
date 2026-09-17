from email.utils import getaddresses
import datetime

from datatypes import EmailAddress

from . import TestCase


class EmailDataTest(TestCase):
    def test_create_email_message(self):
        em = self.create_email_message()
        self.assertTrue(str(em))

    def test_get_email_address_1(self):
        email = self.get_email_address()
        self.assertGreater(len(email), 0)
        self.assertTrue("'" not in email)
        self.assertTrue("-" not in email)

        email = self.get_email_address("foo")
        self.assertTrue(email.startswith("foo"))

        email = self.get_email_address("foo'bar")
        self.assertTrue(email.startswith("foobar"))

    def test_get_email_address_name(self):
        name = self.get_name()
        email = self.get_email_address(name=name)
        self.assertEqual(name, email.name)

        email = self.get_email_address(
            name=name,
            address="\"Foo Bar\" <foo@bar.com>",
        )
        self.assertEqual(name, email.name) # name should override address

        email = self.get_email_address(address="\"Foo Bar\" <foo@bar.com>")
        self.assertEqual("Foo Bar", email.name)

    def test_create_email_thread_1(self):
        emails = self.create_email_thread(count=3)
        for i in range(1, len(emails)):
            a = EmailAddress(address=emails[i - 1]["To"])
            b = EmailAddress(address=emails[i]["From"])
            self.assertEqual(a, b)

            a = EmailAddress(address=emails[i - 1]["From"])
            b = EmailAddress(address=emails[i]["To"])
            self.assertEqual(a, b)

    def test_create_email_thread_tos(self):
        to_addresses = [
            self.get_email_address(name=self.get_name()),
            self.get_email_address(name=self.get_name()),
            self.get_email_address(name=self.get_name()),
        ]
        emails = self.create_email_thread(to_address=to_addresses)

        from_address = getaddresses(emails[1].get_all("From"))[0][1]
        to_addresses = [em[1] for em in getaddresses(emails[0].get_all("To"))]
        self.assertTrue(from_address in to_addresses)

    def test_thread_dates(self):
        emails = self.create_email_thread(count=5)
        prev_dt = None
        for em in emails:
            dt = datetime.datetime.strptime(
                em.get("Date"),
                "%a, %d %b %Y %H:%M:%S %z",
            )

            if prev_dt is not None:
                self.assertLess(prev_dt, dt)

            prev_dt = dt

    def test_encoding(self):
        encoding = "us-ascii"

        # only text/plain email
        email = self.create_email_message(
            data="foo bar",
            encoding=encoding,
        )
        self.assertEqual(encoding, email.get_charset())

        # multiple text/* parts 
        email = self.create_email_message(
            data={
                "text/html": "<p>foo bar</p>",
                "text/plain": "foo bar",
            },
            encoding=encoding,
        )

        for part in email.walk():
            if part.get_content_type().startswith("text/"):
                self.assertEqual(encoding, part.get_charset())

    def test_create_email_thread_datas(self):
        datas = [
            "one",
            "two",
            "three",
        ]
        emails = self.create_email_thread(datas=datas)

        self.assertEqual(3, len(emails))
        for i, email in enumerate(emails):
            self.assertTrue(email.plain.startswith(datas[i]))

