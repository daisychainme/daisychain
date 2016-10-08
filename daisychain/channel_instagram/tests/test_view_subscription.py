from django.core.urlresolvers import reverse
from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from channel_instagram import setup, channel
from channel_instagram.conf import Config
from channel_instagram.models import InstagramAccount
from channel_instagram.views import (SESSKEY_OAUTH_NEXT_URI,
                                     SESSKEY_OAUTH_VERIFY_TOKEN)
from django.contrib.auth.models import User
from mock import MagicMock, patch
from time import sleep
import json
import re
import requests
import responses
from urllib.parse import urlsplit, parse_qs


class SubscriptionTest(TransactionTestCase):
    fixtures = ["core/fixtures/initial_data.json"]

    def setUp(self):

        setup.setup()

        johndoe = User.objects.create_user("johndoe")
        InstagramAccount(user=johndoe,
                         instagram_id="1234567890",
                         access_token="1234567890.access.token").save()

        self.url = reverse("instagram:subscription")
        self.payload = '[{"changed_aspect": "media", "object": "user", ' \
            '"object_id": "3229602005", "time": 1464723248, ' \
            '"subscription_id": 0, ' \
            '"data": {"media_id": "1262512568025438949_3229602005"}}]'
        self.signature = "0d76b66ff74f0f7642b320f76fe847c685f56886"
        self.getParams = {
            'hub.mode': 'subscribe',
            'hub.challenge': 'foobarbaz',
            'hub.verify_token': ''
        }

    def test_confirmSubscription_correct(self):

        res = self.client.get(self.url,
                              self.getParams)
        self.assertEqual(200, res.status_code)
        self.assertEqual('foobarbaz', res.content.decode('utf-8'))

    def test_confirmSubscription_no_query(self):

        res = self.client.get(self.url)
        self.assertEqual(400, res.status_code)

    @patch("channel_instagram.views.SubscriptionView._calculate_signature")
    def test_sendSubscription_correct(self, mock_calculate_signature):

        mock_calculate_signature.return_value = self.signature

        res = self.client.post(self.url,
                               data=self.payload,
                               content_type="application/json",
                               HTTP_X_HUB_SIGNATURE=self.signature)
        self.assertEqual(200, res.status_code)

    def test_sendSubscription_wrongSignature(self):

        res = self.client.post(self.url,
                               data=self.payload,
                               content_type="application/json",
                               HTTP_X_HUB_SIGNATURE="wrong_signature")
        self.assertEqual(400, res.status_code)

    def test_sendSubscription_noPayload(self):

        res = self.client.post(self.url,
                               data='',
                               content_type="application/json",
                               HTTP_X_HUB_SIGNATURE=self.signature)
        self.assertEqual(400, res.status_code)
