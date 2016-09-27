from django.contrib.auth.models import User
from django.test import TestCase
from channel_hue.models import HueAccount
from django.test.client import Client
from django.core.urlresolvers import reverse
from unittest.mock import patch, Mock

import requests

class FakeResponseA():
    def json(self):
        return [{'internalipaddress':'132.123.123'}]

class FakeResponseB():
    def json(self):
        return [{'success':{'username':'John'}}]

class BaseTestCase(TestCase):

    def create_user(self):
        user = User.objects.create_user('user',
            'superuser@super.com',
            'Password')
        user.save()
        return user

    def create_Hue_account(self, user):
        hue_account = HueAccount(
            user=user,
            bridge_ip='123.123.123',
            access_token='test_token'
        )
        hue_account.save()
        return dropbox_account

    def setUp(self):
        self.client = Client()
        self.user = self.create_user()

class TestRegisterView(BaseTestCase):

    def test_unlogged_user(self):
        response = self.client.get(reverse('hue:connect'))
        self.assertRedirects(response,
                         '/accounts/login/?next=/hue/authenticate')

    @patch('requests.post')
    @patch('requests.get')
    def test_logged_user(self, mock_get, mock_post):
        self.client.force_login(self.user)
        res = FakeResponseA()
        mock_get.return_value = res
        res = FakeResponseB()
        mock_post.return_value = res
        response = self.client.get(reverse('hue:connect'))

        self.assertEqual(len(HueAccount.objects.all()), 1)
