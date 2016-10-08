from django.db.models.sql.datastructures import BaseTable
from django.test import TestCase
from django.contrib.auth.models import User
from mock import Mock, patch

from django.test.client import Client
from django.core.urlresolvers import reverse
from channel_gmail.channel import GmailChannel
from channel_gmail.models import GmailAccount

SEND_MAIL = 100


class BaseTestCase(TestCase):

    def create_user(self):
        user = User.objects.create_user("John", "john@gmail.com", "secret")
        user.save()
        return user

    def setUp(self):
        self.user = self.create_user()
        self.user.save()
        self.client = Client()
        self.channel = GmailChannel()


class TestConnectView(BaseTestCase):

    def test_view_without_login(self):
        response = self.client.get(reverse('gmail:connect'))
        self.assertRedirects(response,
                             '/accounts/login/?next=/gmail/connect/')

    def test_view_with_logged_in_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('gmail:connect'))
        self.assertEqual(response.status_code, 302)


class TestCallbackView(BaseTestCase):

    class MockResponse:
        def __init__(self, data, status_code, ok):
            self.data = data
            self.status_code = status_code
            self.ok = ok

    def test_callback_without_code(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse('gmail:callback'))
        self.assertEqual(response.status_code, 400)

    def test_callback_with_user_not_authenticated(self):
        response = self.client.get(reverse('gmail:callback'))
        self.assertEqual(response.status_code, 400)

    @patch('requests.get')
    @patch('oauth2client.client.OAuth2WebServerFlow.step2_exchange')
    def test_callback_with_user_and_code(self, mock_step2_exchange, mock_get):
        self.client.force_login(self.user)
        flow = 'gANjb2F1dGgyY2xpZW50LmNsaWVudApPQXV0aDJXZWJTZXJ2ZXJGbG93CnEAKYFxAX1xAihYCAAAAGF1dGhfdXJpcQNYLAAAAGh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi92Mi9hdXRocQRYCgAAAHJldm9rZV91cmlxBVgrAAAAaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tL28vb2F1dGgyL3Jldm9rZXEGWA4AAAB0b2tlbl9pbmZvX3VyaXEHWC4AAABodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjMvdG9rZW5pbmZvcQhYCgAAAHVzZXJfYWdlbnRxCU5YBgAAAHBhcmFtc3EKfXELKFgNAAAAcmVzcG9uc2VfdHlwZXEMWAQAAABjb2RlcQ1YCwAAAGFjY2Vzc190eXBlcQ5YBwAAAG9mZmxpbmVxD3VYDAAAAHJlZGlyZWN0X3VyaXEQWC4AAABodHRwOi8vYmUxODJlZDUubmdyb2suaW8vZ21haWwvb2F1dGgtY2FsbGJhY2svcRFYDQAAAGNsaWVudF9zZWNyZXRxElgYAAAAMktiQkVlVy1iZ3ExUUNFOXNqRVY5STVPcRNYCgAAAGxvZ2luX2hpbnRxFE5YCQAAAGNsaWVudF9pZHEVWEcAAAA0MDAzODUyNjc2NC1tZzJibHA4NTc2bWY2dHE3YzdsNjVhbzJ0Mmdhbmdray5hcHBzLmdvb2dsZXVzZXJjb250ZW50LmNvbXEWWAoAAABkZXZpY2VfdXJpcRdYMAAAAGh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi9kZXZpY2UvY29kZXEYWAUAAABzY29wZXEZWCoAAABodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9hdXRoL2dtYWlsLnNlbmRxGlgUAAAAYXV0aG9yaXphdGlvbl9oZWFkZXJxG05YCQAAAHRva2VuX3VyaXEcWCoAAABodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjQvdG9rZW5xHXViLg=='
        mock_step2_exchange.return_value = 'gANjb2F1dGgyY2xpZW50LmNsaWVudApPQXV0aDJDcmVkZW50aWFscwpxACmBcQF9cQIoWA0AAABjbGllbnRfc2VjcmV0cQNYGAAAADJLYkJFZVctYmdxMVFDRTlzakVWOUk1T3EEWAwAAAB0b2tlbl9leHBpcnlxBWNkYXRldGltZQpkYXRldGltZQpxBkMKB+AJDw0oHguLTnEHhXEIUnEJWAgAAABpZF90b2tlbnEKTlgKAAAAdXNlcl9hZ2VudHELTlgMAAAAYWNjZXNzX3Rva2VucQxYSAAAAHlhMjkuQ2pCZkE5M2piQ0wzQVJPWm9icjRCTFM1OS1XNHhzQzZOSHJCZ2Eya0I3UmN0c0lVM0FXSHhjSHpyV2FGWkhRSEpJOHENWA4AAAB0b2tlbl9yZXNwb25zZXEOfXEPKFgKAAAAZXhwaXJlc19pbnEQTQ8OWAwAAABhY2Nlc3NfdG9rZW5xEWgNWAoAAAB0b2tlbl90eXBlcRJYBgAAAEJlYXJlcnETdVgHAAAAaW52YWxpZHEUiVgJAAAAY2xpZW50X2lkcRVYRwAAADQwMDM4NTI2NzY0LW1nMmJscDg1NzZtZjZ0cTdjN2w2NWFvMnQyZ2FuZ2trLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tcRZYDgAAAHRva2VuX2luZm9fdXJpcRdYLgAAAGh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92My90b2tlbmluZm9xGFgKAAAAcmV2b2tlX3VyaXEZWCsAAABodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvcmV2b2tlcRpYDQAAAHJlZnJlc2hfdG9rZW5xG05YBgAAAHNjb3Blc3EcY2J1aWx0aW5zCnNldApxHV1xHlgqAAAAaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vYXV0aC9nbWFpbC5zZW5kcR9hhXEgUnEhWAkAAAB0b2tlbl91cmlxIlgqAAAAaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vb2F1dGgyL3Y0L3Rva2VucSN1Yi4='
        gmailuser = GmailAccount(user=self.user,
                                 flow=flow)
        gmailuser.save()
        code = 'secret_code'
        data = {'code': code}

        get_resp = self.MockResponse(data, 200, True)
        mock_get.return_value = get_resp


        session = self.client.session
        session['state'] = 'test_state'
        session['gmail_next_url'] = '/'
        session.save()

        response = self.client.get(reverse('gmail:callback'),
                                   {'code': code})
        gmail_account = GmailAccount.objects.get(user=self.user)
        self.assertNotEqual(gmail_account, None)

    @patch('requests.get')
    @patch('oauth2client.client.OAuth2WebServerFlow.step2_exchange')
    def test_callback_no_user_but_code(self, mock_step2_exchange, mock_get):
        self.client.force_login(self.user)
        flow = 'gANjb2F1dGgyY2xpZW50LmNsaWVudApPQXV0aDJXZWJTZXJ2ZXJGbG93CnEAKYFxAX1xAihYCAAAAGF1dGhfdXJpcQNYLAAAAGh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi92Mi9hdXRocQRYCgAAAHJldm9rZV91cmlxBVgrAAAAaHR0cHM6Ly9hY2NvdW50cy5nb29nbGUuY29tL28vb2F1dGgyL3Jldm9rZXEGWA4AAAB0b2tlbl9pbmZvX3VyaXEHWC4AAABodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjMvdG9rZW5pbmZvcQhYCgAAAHVzZXJfYWdlbnRxCU5YBgAAAHBhcmFtc3EKfXELKFgNAAAAcmVzcG9uc2VfdHlwZXEMWAQAAABjb2RlcQ1YCwAAAGFjY2Vzc190eXBlcQ5YBwAAAG9mZmxpbmVxD3VYDAAAAHJlZGlyZWN0X3VyaXEQWC4AAABodHRwOi8vYmUxODJlZDUubmdyb2suaW8vZ21haWwvb2F1dGgtY2FsbGJhY2svcRFYDQAAAGNsaWVudF9zZWNyZXRxElgYAAAAMktiQkVlVy1iZ3ExUUNFOXNqRVY5STVPcRNYCgAAAGxvZ2luX2hpbnRxFE5YCQAAAGNsaWVudF9pZHEVWEcAAAA0MDAzODUyNjc2NC1tZzJibHA4NTc2bWY2dHE3YzdsNjVhbzJ0Mmdhbmdray5hcHBzLmdvb2dsZXVzZXJjb250ZW50LmNvbXEWWAoAAABkZXZpY2VfdXJpcRdYMAAAAGh0dHBzOi8vYWNjb3VudHMuZ29vZ2xlLmNvbS9vL29hdXRoMi9kZXZpY2UvY29kZXEYWAUAAABzY29wZXEZWCoAAABodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9hdXRoL2dtYWlsLnNlbmRxGlgUAAAAYXV0aG9yaXphdGlvbl9oZWFkZXJxG05YCQAAAHRva2VuX3VyaXEcWCoAAABodHRwczovL3d3dy5nb29nbGVhcGlzLmNvbS9vYXV0aDIvdjQvdG9rZW5xHXViLg=='
        mock_step2_exchange.return_value = 'gANjb2F1dGgyY2xpZW50LmNsaWVudApPQXV0aDJDcmVkZW50aWFscwpxACmBcQF9cQIoWA0AAABjbGllbnRfc2VjcmV0cQNYGAAAADJLYkJFZVctYmdxMVFDRTlzakVWOUk1T3EEWAwAAAB0b2tlbl9leHBpcnlxBWNkYXRldGltZQpkYXRldGltZQpxBkMKB+AJDw0oHguLTnEHhXEIUnEJWAgAAABpZF90b2tlbnEKTlgKAAAAdXNlcl9hZ2VudHELTlgMAAAAYWNjZXNzX3Rva2VucQxYSAAAAHlhMjkuQ2pCZkE5M2piQ0wzQVJPWm9icjRCTFM1OS1XNHhzQzZOSHJCZ2Eya0I3UmN0c0lVM0FXSHhjSHpyV2FGWkhRSEpJOHENWA4AAAB0b2tlbl9yZXNwb25zZXEOfXEPKFgKAAAAZXhwaXJlc19pbnEQTQ8OWAwAAABhY2Nlc3NfdG9rZW5xEWgNWAoAAAB0b2tlbl90eXBlcRJYBgAAAEJlYXJlcnETdVgHAAAAaW52YWxpZHEUiVgJAAAAY2xpZW50X2lkcRVYRwAAADQwMDM4NTI2NzY0LW1nMmJscDg1NzZtZjZ0cTdjN2w2NWFvMnQyZ2FuZ2trLmFwcHMuZ29vZ2xldXNlcmNvbnRlbnQuY29tcRZYDgAAAHRva2VuX2luZm9fdXJpcRdYLgAAAGh0dHBzOi8vd3d3Lmdvb2dsZWFwaXMuY29tL29hdXRoMi92My90b2tlbmluZm9xGFgKAAAAcmV2b2tlX3VyaXEZWCsAAABodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvcmV2b2tlcRpYDQAAAHJlZnJlc2hfdG9rZW5xG05YBgAAAHNjb3Blc3EcY2J1aWx0aW5zCnNldApxHV1xHlgqAAAAaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vYXV0aC9nbWFpbC5zZW5kcR9hhXEgUnEhWAkAAAB0b2tlbl91cmlxIlgqAAAAaHR0cHM6Ly93d3cuZ29vZ2xlYXBpcy5jb20vb2F1dGgyL3Y0L3Rva2VucSN1Yi4='

        code = 'secret_code'
        json_data = {'code': code}

        get_resp = self.MockResponse(json_data, 200, True)
        mock_get.return_value = get_resp

        session = self.client.session
        session['state'] = 'test_state'
        session['gmail_next_url'] = '/'
        session.save()

        response = self.client.get(reverse('gmail:callback'),
                                   {'code': code})
        gmail_account = GmailAccount.objects.get(user=self.user)
        self.assertNotEqual(gmail_account, None)


class TestDisconnectView(BaseTestCase):

    def test_disconnect_nonexixting_user(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('gmail:disconnect'))

        self.assertEqual(response.status_code, 302)

    def test_disconnect_created_user(self):
        self.client.force_login(self.user)
        GmailAccount(user=self.user).save()
        response = self.client.get(reverse('gmail:disconnect'))
        with self.assertRaises(GmailAccount.DoesNotExist):
            GmailAccount.objects.get(user=self.user)


