from email.utils import getaddresses

from . import TestCase


class EmailDataTest(TestCase):
    def test_create_email_message(self):
        em = self.create_email_message()
        self.assertTrue(str(em))

    def test_get_email_address(self):
        email = self.get_email_address()
        self.assertGreater(len(email), 0)
        self.assertTrue("'" not in email)
        self.assertTrue("-" not in email)

        email = self.get_email_address("foo")
        self.assertTrue(email.startswith("foo"))

        email = self.get_email_address("foo'bar")
        self.assertTrue(email.startswith("foobar"))

    def test_create_email_thread_1(self):
        emails = self.create_email_thread(count=3)
        for i in range(1, len(emails)):
            self.assertEqual(emails[i - 1]["To"], emails[i]["From"])
            self.assertEqual(emails[i - 1]["From"], emails[i]["To"])

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

