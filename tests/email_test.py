from . import TestCase


class EmailDataTest(TestCase):
    def test_create_email(self):
        em = self.create_email()
        self.assertTrue(str(em))

