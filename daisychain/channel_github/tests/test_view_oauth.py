from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from mock import Mock, patch
import json

from channel_github.models import GithubAccount



class BaseTestCase(TestCase):

    def create_user(self):
        user = User.objects.create_user('Superuser',
            'superuser@super.com',
            'Password')
        user.save()
        return user

    def setUp(self):
        self.client = Client()
        self.user = self.create_user()
        self.user.save()

    def create_github_account(self):
        github_account = GithubAccount(user=self.user,
                                       access_token='old_token',
                                       username='paul')
        github_account.save()
        return github_account


class TestStartAuthenticationView(BaseTestCase):

    def test_view_without_login(self):
        resp = self.client.get(reverse('github:connect'))
        self.assertRedirects(resp,
                             '/accounts/login/?next=/github/authenticate')

    @patch('uuid.uuid4')
    def test_view_with_logged_in_user(self,
                                      mock_uuid4):
        self.client.force_login(self.user)
        safe = 'keep it secret, keep it safe!'
        mock_uuid4.return_value = safe
        auth_url = 'https://github.com/login/oauth/authorize?'
        resp = self.client.get(reverse('github:connect'))
        self.assertEquals(resp.status_code, 302)


class TestCallbackView(BaseTestCase):

    class MockResponse:
        def __init__(self, json_data, status_code, ok):
            self.json_data = json_data
            self.status_code = status_code
            self.ok = ok

        def json(self):
            return self.json_data

    @patch('requests.get')
    @patch('requests.post')
    def test_callback_with_valid_user(self, mock_post, mock_get):
        # mock returned json with the users access token
        self.client.force_login(self.user)
        data = {'access_token': 'test token'}
        post_resp = self.MockResponse(data, 200, True)
        mock_post.return_value = post_resp

        get_data = {'login': 'testname'}
        get_resp = self.MockResponse(get_data, 200, True)
        mock_get.return_value = get_resp

        session = self.client.session
        session['state'] = 'test_state'
        session['github_next_url'] = '/'
        session.save()
        resp = self.client.get(reverse('github:callback'),
                               {'state': 'test_state',
                                'code': 'test_code'})
        github_account = GithubAccount.objects.get(user=self.user)
        self.assertNotEqual(github_account, None)

    @patch('requests.get')
    @patch('requests.post')
    def test_callback_with_invalid_post_response(self, mock_post, mock_get):
        # mock returned json with the users access token
        self.client.force_login(self.user)
        data = {'access_token': 'test token'}
        post_resp = self.MockResponse(data, 403, False)
        mock_post.return_value = post_resp

        get_data = {'login': 'testname'}
        get_resp = self.MockResponse(get_data, 200, True)
        mock_get.return_value = get_resp

        session = self.client.session
        session['state'] = 'test_state'
        session['github_next_url'] = '/'
        session.save()
        resp = self.client.get(reverse('github:callback'),
                               {'state': 'test_state',
                                'code': 'test_code'})
        self.assertRaises(GithubAccount.DoesNotExist,
                          GithubAccount.objects.get,
                          user=self.user)
        self.assertEquals(resp.status_code, 400)

    @patch('requests.get')
    @patch('requests.post')
    def test_callback_with_invalid_get_response(self, mock_post, mock_get):
        # mock returned json with the users access token
        self.client.force_login(self.user)
        data = {'access_token': 'test token'}
        post_resp = self.MockResponse(data, 200, True)
        mock_post.return_value = post_resp

        get_data = {'login': 'testname'}
        get_resp = self.MockResponse(get_data, 400, False)
        mock_get.return_value = get_resp

        session = self.client.session
        session['state'] = 'test_state'
        session['github_next_url'] = '/'
        session.save()
        resp = self.client.get(reverse('github:callback'),
                               {'state': 'test_state',
                                'code': 'test_code'})
        self.assertRaises(GithubAccount.DoesNotExist,
                          GithubAccount.objects.get,
                          user=self.user)
        self.assertEquals(resp.status_code, 400)


    @patch('requests.get')
    @patch('requests.post')
    def test_callback_with_valid_already_existing_user(self,
                                                       mock_post,
                                                       mock_get):
        # mock returned json with the users access token
        self.client.force_login(self.user)
        github_account = GithubAccount(user=self.user,
                                       access_token='old_token',
                                       username='paul')
        github_account.save()
        data = {'access_token': 'a_different_token'}
        post_resp = self.MockResponse(data, 200, True)
        mock_post.return_value = post_resp

        get_data = {'login': 'a_different_name'}
        get_resp = self.MockResponse(get_data, 200, True)
        mock_get.return_value = get_resp

        session = self.client.session
        session['state'] = 'test_state'
        session['github_next_url'] = '/'
        session.save()
        resp = self.client.get(reverse('github:callback'),
                               {'state': 'test_state',
                                'code': 'test_code'})
        github_account = GithubAccount.objects.get(user=self.user)
        self.assertNotEqual(github_account, None)
        self.assertEquals(github_account.access_token, 'a_different_token')
        self.assertEquals(github_account.username, 'a_different_name')

    def test_callback_without_authentication(self):
        resp = self.client.get(reverse('github:callback'),
                               {'state': 'test_state',
                                'code': 'test_code'})
        self.assertEquals(resp.status_code, 400)

    def test_callback_with_wrong_state_string(self):
        # login the user!
        self.client.force_login(self.user)
        session = self.client.session
        session['state'] = 'test_state'
        session.save()
        resp = self.client.get(reverse('github:callback'),
                               {'state': 'wrong_state'})
        self.assertEquals(resp.status_code, 400)

    def test_callback_without_code(self):
        # login the user!
        self.client.force_login(self.user)
        session = self.client.session
        session['state'] = 'test_state'
        session.save()
        resp = self.client.get(reverse('github:callback'),
                               {'state': 'test_state'})
        self.assertRedirects(resp, '/?status=error',
                             status_code=302, target_status_code=302)

class TestEndAuthenticationView(BaseTestCase):

    def test_end_authentication_deleting_account(self):
        id = self.create_github_account().id
        self.client.force_login(self.user)
        self.client.get(reverse('github:disconnect'))
        with self.assertRaises(GithubAccount.DoesNotExist):
            GithubAccount.objects.get(id=id)
