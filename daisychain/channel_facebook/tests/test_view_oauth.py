from django.core.urlresolvers import reverse
from mock import patch

from channel_facebook.models import FacebookAccount
from .test_base import FacebookBaseTestCase


class TestCallbackView(FacebookBaseTestCase):
    def setUp(self):
        self.user = self.create_user()
        self.user.save()

    @patch('requests.get')
    @patch('requests.post')
    def test_callback_with_valid_user(self, mock_post, mock_get):
        # mock returned json with the users access token
        self.client.force_login(self.user)

        get_data = {'access_token': 'test token',
                    'expires_in': 1337,
                    'data': {
                        'user_id': '1337'
                    }
                    }
        get_resp = self.MockResponse(get_data, 200, True)
        mock_get.return_value = get_resp

        session = self.client.session
        session['state'] = 'test_state'
        session['facebook_next_url'] = '/'
        session.save()
        resp = self.client.get(reverse('facebook:callback'),
                               {'state': 'test_state',
                                'code': 'test_code'})
        facebook_account = FacebookAccount.objects.get(user=self.user)
        self.assertNotEqual(facebook_account, None)

    @patch('requests.get')
    @patch('requests.post')
    def test_callback_with_invalid_post_response(self, mock_post, mock_get):
        # mock returned json with the users access token
        self.client.force_login(self.user)
        data = {'access_token': 'test token', 'expires_in': 1337}
        post_resp = self.MockResponse(data, 403, False)
        mock_post.return_value = post_resp

        get_data = {'login': 'testname'}
        get_resp = self.MockResponse(get_data, 200, True)
        mock_get.return_value = get_resp

        session = self.client.session
        session['state'] = 'test_state'
        session['facebook_next_url'] = '/'
        session.save()
        resp = self.client.get(reverse('facebook:callback'),
                               {'state': 'test_state',
                                'code': 'test_code'})
        self.assertRaises(FacebookAccount.DoesNotExist,
                          FacebookAccount.objects.get,
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
        session['facebook_next_url'] = '/'
        session.save()
        resp = self.client.get(reverse('facebook:callback'),
                               {'state': 'test_state',
                                'code': 'test_code'})
        self.assertRaises(FacebookAccount.DoesNotExist,
                          FacebookAccount.objects.get,
                          user=self.user)
        self.assertEquals(resp.status_code, 400)

    @patch('requests.get')
    def test_callback_with_valid_already_existing_user(self,
                                                       mock_get):
        # mock returned json with the users access token
        self.client.force_login(self.user)
        facebook_account = FacebookAccount(user=self.user,
                                           access_token='old_token',
                                           username='paul')
        facebook_account.save()

        get_data = {'access_token': 'a_different_token',
                    'expires_in': 1337,
                    'data': {
                        'user_id': 'a_different_name'
                    }
                    }
        get_resp = self.MockResponse(get_data, 200, True)
        mock_get.return_value = get_resp

        session = self.client.session
        session['state'] = 'test_state'
        session['facebook_next_url'] = '/'
        session.save()
        resp = self.client.get(reverse('facebook:callback'),
                               {'state': 'test_state',
                                'code': 'test_code'})
        facebook_account = FacebookAccount.objects.get(user=self.user)
        self.assertNotEqual(facebook_account, None)
        self.assertEquals(facebook_account.access_token, 'a_different_token')
        self.assertEquals(facebook_account.username, 'a_different_name')

    def test_callback_without_authentication(self):
        resp = self.client.get(reverse('facebook:callback'),
                               {'state': 'test_state',
                                'code': 'test_code'})
        self.assertEquals(resp.status_code, 400)

    def test_callback_with_wrong_state_string(self):
        # login the user!
        self.client.force_login(self.user)
        session = self.client.session
        session['state'] = 'test_state'
        session.save()
        resp = self.client.get(reverse('facebook:callback'),
                               {'state': 'wrong_state'})
        self.assertEquals(resp.status_code, 400)

    def test_callback_with_aborted_authentification(self):
        # login the user!
        self.client.force_login(self.user)
        session = self.client.session
        session['state'] = 'test_state'
        session.save()
        resp = self.client.get(reverse('facebook:callback'),
                               {'state': 'test_state',
                                'error': 'true'})
        self.assertRedirects(resp, '/channels/?status=error',
                             status_code=302, target_status_code=200)

    def test_callback_without_code(self):
        # login the user!
        self.client.force_login(self.user)
        session = self.client.session
        session['state'] = 'test_state'
        session.save()
        resp = self.client.get(reverse('facebook:callback'),
                               {'state': 'test_state'})
        self.assertRedirects(resp, '/channels/?status=error',
                             status_code=302, target_status_code=200)
