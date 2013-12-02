"""
Runs a suite of unit tests to make sure builder is working
properly
"""

import unittest
import datetime

from django.contrib.auth.models import User, Permission
from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.utils import timezone

from formunculous.models import ApplicationDefinition, FieldDefinition

class BuilderTests(TestCase):
    """
    Test running class for the builder views
    """

    def setUp(self):
        """Setup test case by adding primary user."""

        super(BuilderTests, self).setUp()
        self.user = User.objects.create_user('test_user',
                                             'test_user@formunculous.org',
                                             'foo')
        self.client = Client()

    def _make_root(self):
        self.user.is_superuser = True
        self.user.is_staff = True
        self.user.save()

    def _give_change(self):
        perm = Permission.objects.get(codename='change_form')
        self.user.user_permissions.add(perm)

    def _give_add(self):
        perm = Permission.objects.get(codename='add_form')
        self.user.user_permissions.add(perm)

    def _add_test_app(self):
        self._give_add()
        self.client.login(username=self.user.username,
                          password='foo')
        response = self.client.post(reverse('builder-add-ad'),
                         { 'finish': 1, 'sites': 1,
                           'name': 'Test App',
                           'owner': 'x@carsongee.com', 'slug': 'test-app',
                           'start_date': '1970-1-1',
                           'stop_date': '9999-1-1',
                           'authentication': False,
                           'authentication_multi_submit': False,
                           'reviewers': self.user.id,
                           'notify_reviewers': False,
                           'email_only': False,
                       })
        return response

    def test_add_app_def(self):
        """Add an app definition, and make sure it exists"""

        response = self._add_test_app()
        self.assertRedirects(response, reverse('builder-index'),
                             target_status_code=302)
        self.assertIsNotNone(
            ApplicationDefinition.objects.get(slug='test-app')
        )

    def test_modify_app_def(self):
        """Add an app definition, and make sure it exists"""

        self._add_test_app()
        self._give_change()
        self.client.login(username=self.user.username,
                          password='foo')

        response = self.client.post(reverse('builder-edit-ad',
                                            kwargs={'slug': 'test-app'}),
                                    { 'edit': 1, 'sites': 1,
                                      'name': 'Test Apps Modded',
                                      'owner': 'x@carsongee.com', 'slug': 'test-app',
                                      'start_date': '1970-1-1',
                                      'stop_date': '9999-1-1',
                                      'authentication': False,
                                      'authentication_multi_submit': False,
                                      'reviewers': self.user.id,
                                      'notify_reviewers': False,
                                      'email_only': False,
                                  })
        self.assertRedirects(response, reverse('builder-edit-ad',
                                            kwargs={'slug': 'test-app'}))
        self.assertIsNotNone(
            ApplicationDefinition.objects.get(name='Test Apps Modded')
        )

    def test_edit_fields(self):
        """Add a field to our test app def."""
        self._add_test_app()
        self._give_change()
        self.client.login(username=self.user.username,
                          password='foo')

        ad = ApplicationDefinition.objects.get(slug='test-app')
        response = self.client.post(reverse('builder-edit-fields',
                                            kwargs={'slug': 'test-app'}),
                                    {'edit': 1,
                                     'fielddefinition_set-TOTAL_FORMS': 1,
                                     'fielddefinition_set-INITIAL_FORMS': 0,
                                     'fielddefinition_set-0-label': 'Name',
                                     'fielddefinition_set-0-type': 'TextField',
                                     'fielddefinition_set-0-page': '0',
                                     'fielddefinition_set-0-application': ad.id,
                                     'fielddefinition_set-0-pre_text': '',
                                     'fielddefinition_set-0-post_text': '',
                                     'fielddefinition_set-0-group': False,
                                     'fielddefinition_set-0-slug': 'name',
                                     'fielddefinition_set-0-help_text': '',
                                     'fielddefinition_set-0-require': True,
                                     'fielddefinition_set-0-reviewer_only': False,
                                     'fielddefinition_set-0-header': True,
                                     'fielddefinition_set-0-multi_select': False,
                                     'fielddefinition_set-0-use_radio': False,
                                     'fielddefinition_set-0-order': 1,
                                 })
        self.assertRedirects(response,reverse('builder-edit-fields',
                                            kwargs={'slug': 'test-app'}))
        self.assertEquals(1, len(FieldDefinition.objects.filter(application = ad)))


    def test_builder_permissions(self):
        """Make sure it requires change form permission."""

        # Check logged out
        response = self.client.get(reverse('builder-index'))
        self.assertRedirects(response, '{0}?next={1}'.format(
            reverse('formunculous-login'), reverse('builder-index')))

        # Check no permission
        self.client.login(username=self.user.username,
                          password='foo')
        response = self.client.get(reverse('builder-index'))
        self.assertRedirects(response, '{0}?next={1}'.format(
            reverse('formunculous-login'), reverse('builder-index')))

        # Check proper permission
        self._give_change()
        self.client.login(username=self.user.username,
                          password='foo')
        response = self.client.get(reverse('builder-index'))
        self.assertEqual(response.status_code, 200)

    # def test_admin_links(self):
    #     """
    #     Validate that the admin model works for showing add and change
    #     links for formunculous.
    #     """

    #     self._make_root()
    #     logged_in = self.client.login(username=self.user.username,
    #                                   password='foo')
    #     self.assertTrue(logged_in)
    #     response = self.client.get(reverse('admin:index'))
    #     for url in self.ADMIN_VIEWS:
    #         self.assertIn(reverse(url[0]), response.content)

    #     # Test that those links redirect to the right place
    #     for url in self.ADMIN_VIEWS:
    #         response = self.client.get(reverse(url[0]))
    #         self.assertRedirects(response, reverse(url[1]), status_code=301)

