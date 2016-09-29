from django.core.urlresolvers import reverse
from mock import patch

from channel_facebook.models import FacebookAccount
from .test_base import FacebookBaseTestCase


class TestStartAuthenticationView(FacebookBaseTestCase):
    def test_view_without_login(self):
        resp = self.client.get(reverse('facebook:connect'))
        self.assertRedirects(resp,
                             '/accounts/login/?next=/facebook/authenticate')

    @patch('uuid.uuid4')
    def test_view_with_logged_in_user(self,
                                      mock_uuid4):
        self.client.force_login(self.user)
        safe = 'keep it secret, keep it safe!'
        mock_uuid4.return_value = safe
        auth_url = 'https://facebook.com/login/oauth/authorize?'
        resp = self.client.get(reverse('facebook:connect'))
        self.assertEquals(resp.status_code, 302)


class TestStopAuthenticationView(FacebookBaseTestCase):
    def test_disconnect_deleting_facebook_account(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('facebook:disconnect'))
        with self.assertRaises(FacebookAccount.DoesNotExist):
            FacebookAccount.objects.get(user=self.user)
        self.assertRedirects(response, reverse('channels:list') + "?status=success")
        self.create_facebook_account(self.user)

    def test_disconnect_nonexisting_facebook_account(self):
        self.client.force_login(self.user)
        # disconnect user
        self.client.get(reverse('facebook:disconnect'))
        # redisconnect user
        response = self.client.get(reverse('facebook:disconnect'))
        self.assertRedirects(response, reverse('channels:list') + "?status=success")
        self.create_facebook_account(self.user)

    @patch('channel_facebook.views.StopAuthenticationView.deleteEntry')
    def test_disconnect_error_while_deleting(self, mock_deleteEntry):
        self.client.force_login(self.user)
        mock_deleteEntry.return_value = False
        response = self.client.get(reverse('facebook:disconnect'))
        self.assertRedirects(response, reverse('channels:list') + "?status=error")

    def test_delete_entry(self):
        self.client.force_login(self.user)

    def test_revoke_authentificatotion_not_valid(self):
        response = self.client.get(reverse("facebook:revokeauthentication"))
        self.assertEquals(response.status_code, 200)
