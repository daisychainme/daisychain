from django.test import TestCase
from django.contrib.auth.models import User
from mock import Mock, patch
from core.channel import (Channel, NotSupportedTrigger, NotSupportedAction,
                          ConditionNotMet, ChannelStateForUser)

from django.test.client import Client
from django.core.urlresolvers import reverse
from channel_gmail.channel import GmailChannel
from channel_gmail.models import GmailAccount

SEND_MAIL = 100


class BaseTestCase(TestCase):

    def create_user(self):
        user = User.objects.create_user("John", "john@gmail.com", "secret")
        gmail_user = GmailAccount(user=user,
                                  credentials='gANjb2F1dGgyY2xpZW50LmNsaWVudApPQXV0aDJDcmVkZW50aWFscwpxAC'
                                              'mBcQF9cQIoWA0AAABjbGllbnRfc2VjcmV0cQNYGAAAADJLYkJFZVctYmdxMVFDRTlzakVWOU'
                                              'k1T3EEWAwAAAB0b2tlbl9leHBpcnlxBWNkYXRldGltZQpkYXRldGltZQpxBkMKB+AJDw0oHg'
                                              'uLTnEHhXEIUnEJWAgAAABpZF90b2tlbnEKTlgKAAAAdXNlcl9hZ2VudHELTlgMAAAAYWNjZX'
                                              'NzX3Rva2VucQxYSAAAAHlhMjkuQ2pCZkE5M2piQ0wzQVJPWm9icjRCTFM1OS1XNHhzQzZOSH'
                                              'JCZ2Eya0I3UmN0c0lVM0FXSHhjSHpyV2FGWkhRSEpJOHENWA4AAAB0b2tlbl9yZXNwb25zZX'
                                              'EOfXEPKFgKAAAAZXhwaXJlc19pbnEQTQ8OWAwAAABhY2Nlc3NfdG9rZW5xEWgNWAoAAAB0b2'
                                              'tlbl90eXBlcRJYBgAAAEJlYXJlcnETdVgHAAAAaW52YWxpZHEUiVgJAAAAY2xpZW50X2lkcR'
                                              'VYRwAAADQwMDM4NTI2NzY0LW1nMmJscDg1NzZtZjZ0cTdjN2w2NWFvMnQyZ2FuZ2trLmFwcH'
                                              'MuZ29vZ2xldXNlcmNvbnRlbnQuY29tcRZYDgAAAHRva2VuX2luZm9fdXJpcRdYLgAAAGh0dH'
                                              'BzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92My90b2tlbmluZm9xGFgKAAAAcmV2b2'
                                              'tlX3VyaXEZWCsAAABodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvcmV2b2'
                                              'tlcRpYDQAAAHJlZnJlc2hfdG9rZW5xG05YBgAAAHNjb3Blc3EcY2J1aWx0aW5zCnNldApxHV'
                                              '1xHlgqAAAAaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vYXV0aC9nbWFpbC5zZW5kcR9hhX'
                                              'EgUnEhWAkAAAB0b2tlbl91cmlxIlgqAAAAaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vb2'
                                              'F1dGgyL3Y0L3Rva2VucSN1Yi4='
)
        gmail_user.save()
        user.save()
        return user

    def setUp(self):
        self.user = self.create_user()
        self.user.save()
        self.client = Client()
        self.channel = GmailChannel()


class TestChannel(BaseTestCase):

    def test_user_is_authenticated_authenticated(self):
        self.assertEqual(self.channel.user_is_connected(self.user), ChannelStateForUser.connected)

    @patch('googleapiclient.discovery.build')
    @patch('channel_gmail.channel.GmailChannel._send_message')
    def test_handle_action_send_mail(self, mock_build, mock_send_message):
        inputs = {'sender': 'dasiychain-dev@gmail.com','to': 'maggimagnus@web.de', 'subject': 'Betreff',
                  'message': 'pups'}
        
        self.channel.handle_action(SEND_MAIL, self.user.id, inputs)
        mock_build.assert_called_once()

    def test_handle_action_wrong_actiontype(self):
        inputs = {'sender': 'dasiychain-dev@gmail.com', 'to': 'maggimagnus@web.de', 'subject': 'Betreff',
                  'message': 'hallo'}
        with self.assertRaises(NotSupportedAction):
            self.channel.handle_action(-1, self.user.id, inputs)

    def test_create_message(self):
        response = self.channel._create_message('me', 'test@lala.de', 'betreff', 'hallo')
        self.assertEqual(response['raw'],'Q29udGVudC1UeXBlOiB0ZXh0L3BsYWluOyBjaGFyc2V0PSJ1cy1hc2NpaSIKTUlNRS1WZXJzaW9uO'
                                         'iAxLjAKQ29udGVudC1UcmFuc2Zlci1FbmNvZGluZzogN2JpdAp0bzogdGVzdEBsYWxhLmRlCmZyb2'
                                         '06IG1lCnN1YmplY3Q6IGJldHJlZmYKCmhhbGxv')
