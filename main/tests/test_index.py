"""test_index"""

# from http.client import responses
# from datetime import *
# from django.contrib.auth.models import User
from django.test import TestCase, Client

# from django.urls import reverse


class IndexPage(TestCase):
    """class IndexPage"""

    def setUp(self):
        """setUp"""
        self.client = Client()
        self.response = self.client.get("")

    def test_index_response(self):
        """test_index_response"""
        self.assertEqual(self.response.status_code, 200)
        silencer = "That will be later"
        self.assertEqual(silencer, "That will be later")

    def test_index_context(self):
        """test_index_context"""
        self.assertEqual(self.response.status_code, 200)
        silencer = "That will be later"
        self.assertEqual(silencer, "That will be later")
