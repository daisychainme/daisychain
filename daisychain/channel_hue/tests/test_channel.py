from django.test import TestCase
from channel_hue.models import HueAccount
from django.contrib.auth.models import User
from unittest.mock import patch, Mock
from channel_hue.channel import HueChannel, HueException
from core.channel import (NotSupportedAction, NotSupportedTrigger, Channel)
import requests
import json

class TestHueChannel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='John', id='123')
        self.user.save()
        self.hue = HueChannel()

    def create_hue_account(self):
        self.account = HueAccount(user=self.user, bridge_ip='132.123.123', access_token='770')
        self.account.save()

    def test_handle_unsupported_action(self):
        error = False
        try:
            self.hue.handle_action(101, 123, {})
        except NotSupportedAction:
            error = True

        self.assertEqual(error, True)

    @patch('requests.put.json')
    @patch('requests.put')
    def test_handle_unsupported_action(self, mock_put, mock_json):
        self.account = HueAccount(user=self.user, bridge_ip='132.123.123', access_token='770')
        self.account.save()
        error_action = False
        error_hue = False
        payload = {'state': 'True', 'light_id': '3'}

        err_res = {"error": {"type": 1,"address": "/lights","description": "unauthorized user"	}}
        err_res = json.dumps(err_res)
        mock_put.return_value = err_res
        try:
            self.hue.handle_action(100, 123, payload)
        except NotSupportedAction:
            error_action = True
        except (HueException, AttributeError):
            error_hue = True
        self.assertEqual(error_action, False)
        self.assertEqual(error_hue, True)

    def test_fill_recipe_mappings(self):
        error = False
        payload = {'state': 'True', 'light_id': '3'}
        try:
            self.hue.fill_recipe_mappings(trigger_type=100, userid=123, payload=payload,
                conditions={}, mappings={})
        except NotSupportedTrigger:
            error = True
        self.assertEqual(error, True)
