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

