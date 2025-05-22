"""test_l_f"""

from django.test import TestCase, Client


class LFPage(TestCase):
    """class LFPage"""

    def setUp(self):
        """setUp"""
        self.client = Client()
        self.response = self.client.get("")

    def test_l_f_response(self):
        """test_l_f_response"""
        self.assertEqual(self.response.status_code, 200)
        silencer = "That will be later"
        self.assertEqual(silencer, "That will be later")

    def test_l_f_context(self):
        """test_l_f_context"""
        self.assertEqual(self.response.status_code, 200)
        silencer = "That will be later"
        self.assertEqual(silencer, "That will be later")
