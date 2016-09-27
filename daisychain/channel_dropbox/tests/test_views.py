from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from .models import DropboxAccount, DropboxUser
from django.test.client import Client
from django.http import HttpResponse
from unittest.mock import patch, Mock, MagicMock, PropertyMock
from config.keys import keys
from django.core.urlresolvers import reverse
import dropbox
from dropbox.files import ListFolderResult
from dropbox.users import Account, Name, SpaceUsage,\
    SpaceAllocation, IndividualSpaceAllocation
import json
import hmac
import logging
from hashlib import sha256
from . import views
import channel_dropbox.tasks

class FakeDropbox():
    def files_list_folder(self, path, recursive,
                include_media_info, include_deleted):
        result = ListFolderResult()
        result.cursor = "foo"
        return result
    def users_get_current_account(self):
        account = Account(
            name = Name(display_name="Display_test_name"),
            email = "test_email",
            profile_photo_url  = "url.org/to_profile_photo"
        )
        return account
    def users_get_space_usage(self):
        indi = self.get_individual()
        disk = SpaceUsage(
            used = 879879787,
            allocation = SpaceAllocation.individual(indi)
        )
        return disk
    def get_individual(self):
        individual = IndividualSpaceAllocation(allocated=132132132)
        return individual

class BaseTestCase(TestCase):

    def create_user(self):
        user = User.objects.create_user('user',
            'superuser@super.com',
            'Password')
        user.save()
        return user

    def create_dropbox_account(self, user):
        dropbox_account = DropboxAccount(
            user=user,
            access_token="test_token",
            cursor=''
        )
        dropbox_account.save()
        return dropbox_account

    def setUp(self):
        self.client = Client()
        self.user = self.create_user()
        #logging.disable(logging.CRITICAL)
        self.url='/dropbox/webhook'
        self.signature='test_signature'
        self.payload='[{"list_folder":{"accounts":[dbid:AasdasdrWxbNQ6asdasdc",]},"delta": {"users": [12345678,]}}]'
    #    self.payload = json.dumps(self.payload)

class TestStartAuthentication(BaseTestCase):
    def test_dbx_auth_start_without_login(self):
        response = self.client.get(reverse('dropbox:connect'))
        self.assertRedirects(response,
                             '/accounts/login/?next=/dropbox/authenticate')


    @patch('dropbox.client.DropboxOAuth2Flow.start')
    def test_dbx_auth_start_raise_notExists(self, mock_start):
        mock_start.return_value = "http://localhost:8000/dropbox/authenticate"
        self.client.force_login(self.user)
        response = self.client.get(reverse('dropbox:connect'))
        self.assertEqual(mock_start.return_value, response.url)
        self.assertRaises(DropboxAccount.DoesNotExist)
        self.assertEqual(response.status_code, 302)

    @patch('dropbox.Dropbox')
    def test_dbx_auth_existing_access_token(self,  mock_dbx):
        self.client.force_login(self.user)
        self.dbx_account = self.create_dropbox_account(self.user)
        self.assertEqual(len(DropboxAccount.objects.all()), 1)

        response = self.client.get(reverse('dropbox:connect'))
        self.assertEqual(response.url, '/?status=success')

class TestFinishAuthentication(BaseTestCase):

    def test_auth_without_login(self):
        response = self.client.post(reverse('dropbox:connect'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url,
            "/accounts/login/?next=/dropbox/authenticate")

    @patch("dropbox.users.SpaceAllocation.is_individual")
    @patch("dropbox.Dropbox.users_get_space_usage")
    @patch("dropbox.users.FullAccount")
    @patch("dropbox.files.ListFolderResult")
    @patch("dropbox.Dropbox")
    @patch('dropbox.client.DropboxOAuth2Flow.finish')
    def test_dbx_auth(self, mock_finish, mock_dbx, mock_cursor,
        mock_account, mock_disk, mock_individual):

        self.client.force_login(self.user)
        mock_finish.return_value = ['test_token', 42, '/home/']
        fbx = FakeDropbox()
        mock_dbx.return_value = fbx
        mock_cursor.return_value = fbx.files_list_folder(path='', recursive=True,
                    include_media_info=True, include_deleted=True)
        mock_account.return_value = fbx.users_get_current_account()
        mock_disk.return_value = fbx.users_get_space_usage()
        mock_individual.return_value = True
        res = self.client.get(reverse('dropbox:connect'), {'code':'not_null'})

        dropbox_account = DropboxAccount.objects.get(user=self.user)
        self.assertNotEqual(dropbox_account, None)
        dropbox_user = DropboxUser.objects\
            .get(dropbox_account=dropbox_account)
        self.assertNotEqual(dropbox_user, None)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, "/?status=success")

    @patch("dropbox.users.SpaceAllocation.is_individual")
    @patch("dropbox.Dropbox.users_get_space_usage")
    @patch("dropbox.users.FullAccount")
    @patch("dropbox.files.ListFolderResult")
    @patch("dropbox.Dropbox")
    @patch('dropbox.client.DropboxOAuth2Flow.finish')
    def test_dbx_auth_not_individual(self, mock_finish, mock_dbx, mock_cursor,
        mock_account, mock_disk, mock_individual):

        self.client.force_login(self.user)
        mock_finish.return_value = ['test_token', 42, '/home/']
        fbx = FakeDropbox()
        mock_dbx.return_value = fbx
        mock_cursor.return_value = fbx.files_list_folder(path='', recursive=True,
                    include_media_info=True, include_deleted=True)
        mock_account.return_value = fbx.users_get_current_account()
        mock_disk.return_value = fbx.users_get_space_usage()
        mock_individual.return_value = False
        res = self.client.get(reverse('dropbox:connect'), {'code':'not_null'})

        self.assertEqual(len(DropboxAccount.objects.all()), 0)
        self.assertEqual(len(DropboxUser.objects.all()), 0)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, "/?status=error")

    @patch('dropbox.client.DropboxOAuth2Flow.finish')
    def test_bad_request(self, mock_finish):
        self.client.force_login(self.user)
        mock_finish.side_effect = \
            dropbox.client.DropboxOAuth2Flow.BadRequestException
        res = self.client.get(reverse('dropbox:connect'), {'code':'not_null'})

        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, "/?status=error")

    @patch('dropbox.client.DropboxOAuth2Flow.finish')
    def test_bad_state(self, mock_finish):
        self.client.force_login(self.user)
        mock_finish.side_effect = \
            dropbox.client.DropboxOAuth2Flow.BadStateException
        res = self.client.get(reverse('dropbox:connect'), {'code':'not_null'})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, reverse('dropbox:connect'))


    @patch('dropbox.client.DropboxOAuth2Flow.finish')
    def test_bad_csrf(self, mock_finish):
        self.client.force_login(self.user)
    #    mock_finish.return_value = ['test_token', self.user, 'test_user_id']
        mock_finish.side_effect = dropbox.client.DropboxOAuth2Flow.CsrfException
        client = Client(enforce_csrf_checks=True)
        res = self.client.get(reverse('dropbox:connect'), {'code':'not_null'})

        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, "/?status=error")

    @patch('dropbox.client.DropboxOAuth2Flow.finish')
    def test_not_approved_exception(self, mock_finish):
        self.client.force_login(self.user)
        mock_finish.side_effect = \
            dropbox.client.DropboxOAuth2Flow.NotApprovedException
        res = self.client.get(reverse('dropbox:connect'), {'code':'not_null'})

        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, "/?status=error")

    @patch('dropbox.client.DropboxOAuth2Flow.finish')
    def test_provider_exception(self, mock_finish):
        self.client.force_login(self.user)
        mock_finish.side_effect = \
            dropbox.client.DropboxOAuth2Flow.ProviderException
        res = self.client.get(reverse('dropbox:connect'), {'code':'not_null'})

        self.assertEqual(res.status_code, 302)
        self.assertEqual(res.url, "/?status=error")

class TestWebhook(BaseTestCase):

    def test_dbx_webhook_get(self):
        response = self.client.get( reverse('dropbox:webhook'),
                                    {'challenge':'test-challenge'})
        self.assertContains(response, 'test-challenge')

    @patch('hmac.compare_digest')
    @patch('channel_dropbox.tasks.fireTrigger')
    def test_dbx_webhook_post(self, mock_fire_trigger, mock_digest):
        res = self.client.post(self.url,
                               data=self.payload,
                               content_type='application/json',
                               HTTP_X_DROPBOX_SIGNATURE=self.signature)
        self.assertEqual(res.status_code, 200)
        #mock_fire_trigger.assert_called_once_with(12345678)

    @patch('channel_dropbox.tasks.fireTrigger')
    def test_dbx_webhook_post_with_wrong_signature(self, mock_fire_trigger):
        res = self.client.post(self.url,
                       data=self.payload,
                       content_type='application/json',
                       HTTP_X_DROPBOX_SIGNATURE=self.signature)
        self.assertEqual(res.url, "/?status=error")
