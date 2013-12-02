"""
Runs a suite of unit tests to make sure the admin hooks are
working properly.
"""

import unittest

from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse

class AdminTests(TestCase):
    """
    Test running class for the admin model.
    """

    ADMIN_VIEWS = [
        ('admin:formunculous_form_changelist', 'builder-index', ),
        ('admin:formunculous_form_add', 'builder-add-ad', ),
    ]

    def setUp(self):
        """Setup test case by adding primary user."""

        super(AdminTests, self).setUp()
        self.user = User.objects.create_user('test_user',
                                             'test_user@formunculous.org',
                                             'foo')
        self.client = Client()

    def _make_root(self):
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()

    def test_admin_links(self):
        """
        Validate that the admin model works for showing add and change
        links for formunculous.
        """

        self._make_root()
        logged_in = self.client.login(username=self.user.username,
                                      password='foo')
        self.assertTrue(logged_in)
        response = self.client.get(reverse('admin:index'))
        for url in self.ADMIN_VIEWS:
            self.assertIn(reverse(url[0]), response.content)

        # Test that those links redirect to the right place
        for url in self.ADMIN_VIEWS:
            response = self.client.get(reverse(url[0]))
            self.assertRedirects(response, reverse(url[1]), status_code=301)

