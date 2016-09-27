'''
from django.core.urlresolvers import reverse
from django.test import TestCase, RequestFactory
from django.test.client import Client
from django.contrib.auth.models import User
from django.core.files import File
from django.http import HttpResponse
from mock import Mock, patch
from hashlib import sha256
import hmac
import time
import random
import json
import os
import sys
import urllib
import datetime
import dropbox
from . import views
import channel_dropbox.tasks
from config.keys import keys
from channel_dropbox.channel import DropboxChannel
from .models import DropboxAccount

from core.models import Channel, Trigger, TriggerOutput


"""
    Test cases for the dropbox channel.
"""


def make_dropbox_account(user):
    dropbox_account = DropboxAccount(
        user=user,
        access_token=keys['DROPBOX']['TEST_ACCESS_TOKEN'],
        dropbox_user_id=12345678,
        #last_modified=datetime.datetime.now()-datetime.timedelta(days=1),
        cursor=''
        )
    dropbox_account.save()
    return dropbox_account



class BaseTestCase(TestCase):

    def create_user(self):
        user = User.objects.create_user('user42',
            'superuser@super.com',
            'Password')
        user.save()
        return user

    def setUp(self):
        self.client = Client()
        self.user = self.create_user()


class TestStartAuthentication(BaseTestCase):
    def test_dbx_auth_start_without_login(self):
        response = self.client.get(reverse('dropbox:connect'))
        # user should be redirected to login page if they are not logged in
        self.assertRedirects(response,
                             '/accounts/login/?next=/dropbox/authenticate')


    @patch('dropbox.client.DropboxOAuth2Flow.start')
    def test_dbx_auth_start_raise_notExists(self, mock_start):
        #mock_start.return_value = "https://www.dropbox.com/1/oauth2/authorize?state=ubS9rWCSnh8HC6fpLYVWiA%3D%3D&redirect_uri=http%3A%2F%2Flocalhost%3A8000%2Fdropbox%2Fauth-finish&response_type=code&client_id=062urby9ev91yi9"
        mock_start.return_value = "http://localhost:8000/dropbox/auth-finish"
        self.client.force_login(self.user)
        response = self.client.get(reverse('dropbox:connect'))
        #print >>sys.stderr, response.url
        self.assertEqual(mock_start.return_value, response.url)
        self.assertRaises(DropboxAccount.DoesNotExist)
        # assert redirection

        self.assertEqual(response.status_code, 302)

    @patch('dropbox.Dropbox')
    def test_dbx_auth_existing_access_token(self,  mock_dbx):
        self.client.force_login(self.user)
        dbx = make_dropbox_account(self.user)
        self.assertEqual(len(DropboxAccount.objects.all()), 1)
        response = self.client.post(reverse('dropbox:connect'))
        self.assertEqual(response.url, '/home/')



class TestFinishAuthentication(BaseTestCase):

    @patch('dropbox.client.DropboxOAuth2Flow.finish')
    def test_dbx_auth_finish(self, mock_auth_finish):
        self.client.force_login(self.user)
        mock_auth_finish.return_value = ['test_token',
            self.user, 'test_user_id']
        response = self.client.get(reverse('dropbox:auth_finish'))
        dropbox_account = DropboxAccount.objects.get(user=self.user)
        self.assertNotEqual(dropbox_account, None)

    @patch('dropbox.client.DropboxOAuth2Flow.finish')
    def test_bad_request(self, mock_finish):
        self.client.force_login(self.user)
        mock_finish.side_effect = \
            dropbox.client.DropboxOAuth2Flow.BadRequestException
        response = self.client.post(reverse('dropbox:auth_finish'))
        self.assertEqual(response.status_code, 400)

    @patch('dropbox.client.DropboxOAuth2Flow.finish')
    def test_bad_state(self, mock_finish):
        self.client.force_login(self.user)
        mock_finish.side_effect = \
            dropbox.client.DropboxOAuth2Flow.BadStateException
        response = self.client.post(reverse('dropbox:auth_finish'))
        self.assertEqual(response.status_code, 302)

    @patch('dropbox.client.DropboxOAuth2Flow.finish')
    def test_bad_csrf(self, mock_finish):
        self.client.force_login(self.user)
        mock_finish.return_value = ['test_token', self.user, 'test_user_id']
        mock_finish.side_effect = dropbox.client.DropboxOAuth2Flow.CsrfException
    #    client = Client(enforce_csrf_checks=True)
        response = self.client.post(reverse('dropbox:auth_finish'))
        self.assertEqual(response.status_code, 403)

    @patch('dropbox.client.DropboxOAuth2Flow.finish')
    def test_not_approved_exception(self, mock_finish):
        self.client.force_login(self.user)
        mock_finish.side_effect = \
            dropbox.client.DropboxOAuth2Flow.NotApprovedException
        response = self.client.post(reverse('dropbox:auth_finish'))
        self.assertEqual(response.status_code, 302)

    @patch('dropbox.client.DropboxOAuth2Flow.finish')
    def test_provider_exception(self, mock_finish):
        self.client.force_login(self.user)
        mock_finish.side_effect = \
            dropbox.client.DropboxOAuth2Flow.ProviderException
        response = self.client.get(reverse('dropbox:auth_finish'))
        self.assertEqual(response.status_code, 403)


class TestWebhook(BaseTestCase):
    def test_dbx_webhook_get(self):
        response = self.client.get( reverse('dropbox:webhook'),
                                    {'challenge':'test-challenge'})
        self.assertContains(response, 'test-challenge')

    def test_dbx_webhook_post(self):
        trigger_data = {
            "list_folder": {
                "accounts": [
                    "dbid:AAHIb-OurWxbNQ6ywGRopQngc",
                    ]
            },
            "delta": {
                "users": [
                    12345678,
                ]
            }
        }
        data = json.dumps(trigger_data)
        signature = hmac.new("APP_SECRET".encode('utf-8'),
            data.encode('utf-8'), sha256 ).hexdigest()
        factory = RequestFactory()
        request = factory.post('/dropbox/webhook')
        request.headers = { 'Content-Type':'application/json; charset=UTF-8',
                            'X-Dropbox-Signature': signature}
        request.data = trigger_data
        #response = self.client.post(reverse('dropbox:webhook'), request)
        response = views.dropbox_webhook(request)
        self.assertEqual(response, None)

    def test_webhook_trigger_wrong_key(self):
        trigger_data = {
            "list_folder": {
                "accounts": [
                    "dbid:AAH4NIb-OurWxbNQ6ywGRopQngc",
                    ]
            },
            "delta": {
                "users": [
                    12345678,
                ]
            }
        }
        data = json.dumps(trigger_data)
        signature = hmac.new("APP_SECRET".encode('utf-8'),
            data.encode('utf-8'), sha256 ).hexdigest()
        factory = RequestFactory()
        request = factory.post('/dropbox/webhook')
        request.headers = { 'Content-Type':'application/json; charset=UTF-8',
                            'X-Dropbox-Signature': signature}
        request.data = trigger_data
        response = views.webhook(request)
        self.assertEqual(response.status_code, 403)


    #@patch('dropbox.Dropbox')
    @patch('channel_dropbox.tasks.fireTrigger')
    def test_process_user(self, mock_tasks):
        dbx = make_dropbox_account(self.user)
        wait_time = random.uniform(0, 0.05)
        time.sleep(wait_time)
        trigger_data = {
            "list_folder": {
                "accounts": [
                    "dbid:AAH4fOurWxbNQ6ywGRopQngc",
                    ]
            },
            "delta": {
                "users": [
                    12345678,
                ]
            }
        }
        data =  json.dumps(trigger_data)
        signature = hmac.new("v28le7tbmxga9qb".encode('utf-8'),
            data.encode('utf-8'), sha256 ).hexdigest()
        factory = RequestFactory()
        request = factory.post('/dropbox/webhook')
        request.headers = { 'Title':'application/json; charset=UTF-8',
                            'X-Dropbox-Signature': signature}
        request.data = trigger_data
        response = views.webhook(request)
    #    mock_dbx.assert_called_once_with("test_access_token")
        mock_tasks.assert_called_once_with(12345678)


class TestChannel(BaseTestCase):

    def test_get_trigger_inputs(self):
        setup.setup()
        dropbox_account = make_dropbox_account(self.user)
        inputs = {}
        inputs['image']='blabla'
        inputs['data']='{New/Modified Text}'
        inputs['description']='text_file'
        inputs['caption']='new'
        payload = {'path':'/test//test.txt'}
        #payload = {}
        #payload['path'] = '/test/test.txt'
        dropBox = DropboxChannel()
        inputs = dropBox.get_trigger_inputs(101, self.user.pk, payload, inputs)
        result = inputs['data'].decode('utf-8')
        self.assertEqual(result, "test 1")

    def test_get_trigger_inputs_fail(self):
        setup.setup()
        dropbox_account = make_dropbox_account(self.user)
        inputs = {}
        inputs['image']='blabla'
        inputs['data']='{New/Modified Text}'
        inputs['description']='text_file'
        inputs['caption']='new'
        payload = {'path':'/file_does_not_exists/test.txt'}
        #payload = {}
        #payload['path'] = '/test/test.txt'
        dropBox = DropboxChannel()
        inputs = dropBox.get_trigger_inputs(101, self.user.pk, payload, inputs)
        result = inputs['data']
        self.assertIsNone(result)

    def test_handle_action_upload(self):
        dropbox_account = make_dropbox_account(self.user)
        inputs = {'source':'.//channel_dropbox/testdata/test_1.txt', 'destination':'/test/test_upload.txt', 'overwrite':'False'}
        dropBox = DropboxChannel()
        response = dropBox.handle_action(Action.upload, self.user.pk, inputs)
        #print(response)
        self.assertEqual(response.name, 'test_upload.txt')

    def test_handle_action_wrong_upload(self):
        dropbox_account = make_dropbox_account(self.user)
        inputs = {'source':'.//channel_dropbox/testdata/test_1.txt', 'destination':'/../../', 'overwrite':'False'}
        dropBox = DropboxChannel()
        response = dropBox.handle_action(Action.upload, self.user.pk, inputs)
        #print(response)
        self.assertIsNone(response)

    def test_handle_action_downlaod_to_destination(self):
        dropbox_account = make_dropbox_account(self.user)
        inputs = {'source':'//test/test_upload.txt', 'destination':'./channel_dropbox/testdata/test_download_2.txt'}
        dropBox = DropboxChannel()
        response = dropBox.handle_action(Action.download_to_destination, self.user.pk, inputs)
        self.assertTrue(os.path.isfile('./channel_dropbox/testdata/test_download_1.txt'))

    def test_handle_action_downlaod_to_wrong_destination(self):
        dropbox_account = make_dropbox_account(self.user)
        inputs = {'source':'/file_not_exists/test_upload.txt', 'destination':'./channel_dropbox/testdata/test_download.txt'}
        dropBox = DropboxChannel()
        response = dropBox.handle_action(Action.download_to_destination, self.user.pk, inputs)
        self.assertIsNone(response)

    def test_handle_action_wrong_action(self):
        dropbox_account = make_dropbox_account(self.user)
        inputs = {'source':'/testdata/test_1.txt', 'destination':'/test/test_upload.txt'}
        dropBox = DropboxChannel()
        response = dropBox.handle_action(999, self.user.pk, inputs)
        self.assertIsNone(response)

    '''
'''
    @patch('dropbox.Dropbox.files_download')
    def test_download(self, mock_download):
        fp = open('./channel_dropbox/testdata/test_download.txt')
        res = HttpResponse(fp, content_type="text/plain")
        res['Content-Disposition'] = 'attachment; filename="test_download.txt"'
        path = "./testdata/"
        name = "test_download.txt"
        md = {'title':'foo_title'}
        mock_download.return_value = [ md, res ]
        response = views.dbx_download("test_access_token", path, name)
        self.assertEqual(len(response), 28, msg="response was not None")

        #print (response, file=sys.stderr)

    @patch('dropbox.Dropbox.files_download')
    def test_download_fail(self, mock_download):
        fp = open('./channel_dropbox/testdata/test_download.txt')
        res = HttpResponse(fp, content_type="text/plain")
        res['Content-Disposition'] = 'attachment; filename="test_download.txt"'
        path = "./testdata/"
        name = "test_download.txt"
        md = {'title':'foo_title'}
        mock_download.return_value = [ md, res ]
        mock_download.side_effect = dropbox.exceptions.HttpError('12','404','')
        response = views.dbx_download("test_access_token", path, name)
        self.assertIsNone(response)

    @patch('dropbox.Dropbox.files_upload')
    def test_upload(self, mock_upload):
        path = './channel_dropbox/testdata/test_download.txt'
        res = self
        res.name = 'test_name'
        mock_upload.return_value = res
        response = views.dbx_upload("test_access_token", path, False)
        self.assertEqual(res, response)

    @patch('dropbox.Dropbox.files_upload')
    def test_fail_upload(self, mock_upload):
        path = './channel_dropbox/testdata/test_download.txt'
        res = self
        res.name = 'test_name'
        mock_upload.return_value = res
        mock_upload.side_effect = dropbox.exceptions.ApiError('request_id', 'error', 'user_message_text', 'user_message_locale')
        response = views.dbx_upload("test_access_token", path, False)
        self.assertIsNone(response)'''
'''

class TestTasks(BaseTestCase):

    def test_fireTrigger(self):

        dropbox_account = make_dropbox_account(self.user)

        wait_time = 2
        time.sleep(wait_time)

        dbx = dropbox.Dropbox(dropbox_account.access_token)

        #try:
        dbx.files_delete('/test1')
        dbx.files_delete('/test2')
        dbx.files_delete('/test3')
        #except dropbox.exceptions.ApiError as err:
        #    pass
        time.sleep(wait_time)
        dbx.files_create_folder('/test1')
        dbx.files_create_folder('/test2')
        dbx.files_create_folder('/test3')
        dbx.files_create_folder('/test1/test11')
        dbx.files_create_folder('/test2/test22')
        dbx.files_create_folder('/test3/test33')
        time.sleep(wait_time)
        channel_dropbox.tasks.fireTrigger(self, userid=12345678)
        with open('./channel_dropbox/testdata/test_1.txt', 'w') as fw:
            fw.write("test 1")
            fw.close()
        with open('./channel_dropbox/testdata/test_1.txt', 'rb') as f:
            data = f.read()
            f.close()
        dbx.files_upload(data, '/test1/test1.txt', dropbox.files.WriteMode.add)
        dbx.files_upload(data, '/test2/test2.txt', dropbox.files.WriteMode.add)
        dbx.files_upload(data, '/test3/test3.txt', dropbox.files.WriteMode.add)
        dbx.files_upload(data, '/test1/test11/test1.txt', dropbox.files.WriteMode.add)
        dbx.files_upload(data, '/test2/test22/test2.txt', dropbox.files.WriteMode.add)
        dbx.files_upload(data, '/test3/test33/test3.txt', dropbox.files.WriteMode.add)
        time.sleep(wait_time)

        channel_dropbox.tasks.fireTrigger(self, userid=12345678)
'''
