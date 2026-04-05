from . import TestCase


class EmailDataTest(TestCase):
    def test_create_email_message(self):
        em = self.create_email_message()
        self.assertTrue(str(em))

