from django.test import TestCase
from .models import DropboxAccount, DropboxUser
from django.contrib.auth.models import User
from django.http import HttpResponse
from unittest.mock import patch, Mock
import dropbox
from dropbox.files import FileMetadata
from channel_dropbox.channel import DropboxChannel
import datetime
from core.channel import NotSupportedAction, NotSupportedTrigger, \
    ConditionNotMet

class FakeDropbox():
    def files_download(self, path):
        f = open(path,'r')
        data = f.seek(0)
        res = HttpResponse()
        res.content = data
        ret = ['md_test', res]
        return ret

    def files_download_to_file(self, path_from, path_to):
        f = open(path_from,'r')
        data = f.seek(0)
        res = HttpResponse()
        res.content = data
        ret = ['md_test', res]
        return ret

    def files_upload(self, data, path, mode,
        client_modified,
        mute=True):
        md = FakeFileMetadata()
        return md

class FakeFileMetadata(FileMetadata):
    name='dropbox2.png'
    path_lower='/dropbox2.png'
    path_display='/dropbox2.png'
    id='id:9WIsDrgOt_AAAAAAAAAAAQ'
    client_modified=datetime.datetime(2016, 6, 26, 0, 54, 10)
    server_modified=datetime.datetime(2016, 6, 26, 0, 54, 10)
    rev='984a141728'
    size=131
    parent_shared_folder_id=None
    media_info=None
    sharing_info=None
    property_groups=None
    has_explicit_shared_members=None

class BaseTestCase(TestCase):

    def create_dropbox(self):
        user = User.objects.create_user('John')
        self.dbx_account = DropboxAccount(
            user = user,
            access_token = '_test_access_token',
            cursor = '',
        )
        self.dbx_account.save()
        self.assertEqual(len(DropboxAccount.objects.all()), 1)
        return self.dbx_account

    def create_dbx_user(self):
        dbx_account = self.create_dropbox()
        self.dbx_user = DropboxUser(
            dropbox_account = dbx_account,
            dropbox_userid = 4211,
            display_name = "John As Doe",
            email = "john.doe.as@test.org",
            profile_photo_url = "url.to/athe_profile_photo",
            disk_used = 434.234,
            disk_allocated = 1245678.4444
        )
        self.dbx_user.save()
        self.assertEqual(len(DropboxAccount.objects.all()), 1)
        return self.dbx_user


class TestDropBoxChannel(BaseTestCase):

    @patch('dropbox.Dropbox')
    def test_fill_receipe(self, mock_dbx):
        dbx_user = self.create_dbx_user()
        test_user_id = dbx_user.dropbox_account.user.id
        payload = {'file_extension': 'jpg', 'size': 0.112312,
            'url': 'www.nice-link.me/enjoy',
            'path': 'channel_dropbox/testdata/dropbox2.png',
            'filename': 'entry_name', 'modified': '13-4-2016'}
        conditions = {'filename':'entry_name'}
        mappings = {'test_data':'test/blah[]%data%',
            'test_url':'%url% asdasdasd %not_implemented%',
            'test_email':'a%&/&(%/$%$$%& %email%)',
            'test_jpg':'%jpg%'}
        fbx = FakeDropbox()
        mock_dbx.return_value = fbx
        dbc = DropboxChannel()
        dbc.fill_recipe_mappings(trigger_type=1, userid=test_user_id,
            payload=payload, conditions=conditions, mappings=mappings)

    @patch('dropbox.Dropbox')
    def test_fill_receipe_without_conditions(self, mock_dbx):
        dbx_user = self.create_dbx_user()
        test_user_id = dbx_user.dropbox_account.user.id
        payload = {'file_extension': 'jpg', 'size': 0.112312,
            'url': 'www.nice-link.me/enjoy',
            'path': 'channel_dropbox/testdata/dropbox2.png',
            'filename': 'entry_name', 'modified': '13-4-2016'}
        mappings = {'test_data':'test/blah[]%data%',
            'test_url':'%url% asdasdasd %not_implemented%',
            'test_email':'a%&/&(%/$%$$%& %email%)',
            'test_jpg':'%jpg%'}
        fbx = FakeDropbox()
        mock_dbx.return_value = fbx
        dbc = DropboxChannel()
        dbc.fill_recipe_mappings(trigger_type=1, userid=test_user_id,
            payload=payload, conditions=None, mappings=mappings)

    @patch('dropbox.Dropbox')
    def test_handle_upload_overwrite_true(self, mock_dbx):
        dbx_user = self.create_dbx_user()
        test_user_id = dbx_user.dropbox_account.user.id
        fbx = FakeDropbox()
        mock_dbx.return_value = fbx
        f = open('channel_dropbox/testdata/dropbox2.png','r')
        data = f.seek(0)
        inputs = {'data':data,'path':'channel_dropbox/testdata/dropbox2.png',
            'overwrite':True}
        dbc = DropboxChannel()
        dbc.handle_action(1, test_user_id, inputs)

    @patch('dropbox.Dropbox')
    def test_handle_upload_overwrite_false(self, mock_dbx):
        dbx_user = self.create_dbx_user()
        test_user_id = dbx_user.dropbox_account.user.id
        fbx = FakeDropbox()
        mock_dbx.return_value = fbx
        f = open('channel_dropbox/testdata/dropbox2.png','r')
        data = f.seek(0)
        inputs = {'data':data,'path':'channel_dropbox/testdata/dropbox2.png',
            'overwrite':False}
        dbc = DropboxChannel()
        dbc.handle_action(1, test_user_id, inputs)

    @patch('dropbox.Dropbox')
    def test_handle_download(self, mock_dbx):
        dbx_user = self.create_dbx_user()
        test_user_id = dbx_user.dropbox_account.user.id
        fbx = FakeDropbox()
        mock_dbx.return_value = fbx
        inputs = {'path':'channel_dropbox/testdata/dropbox2.png',
            'overwrite':False}
        dbc = DropboxChannel()
        dbc.handle_action(2, test_user_id, inputs)

    @patch('dropbox.Dropbox')
    def test_handle_download_to_destination(self, mock_dbx):
        dbx_user = self.create_dbx_user()
        test_user_id = dbx_user.dropbox_account.user.id
        fbx = FakeDropbox()
        mock_dbx.return_value = fbx
        inputs = {'path_from':'channel_dropbox/testdata/dropbox2.png',
            'path_to':'/upload1.png'}
        dbc = DropboxChannel()
        dbc.handle_action(3, test_user_id, inputs)

    '''
    @patch('channel_dropbox.channel.DropboxChannel.fill_recipe_mappings')
    @patch('dropbox.Dropbox')
    def test_exceptions_fill_mappings(self, mock_dbx, mock_fill_recipe_mapping):
        dbx_user = self.create_dbx_user()
        test_user_id = dbx_user.dropbox_account.user.id
        payload = {'file_extension': 'jpg', 'size': 0.112312,
            'url': 'www.nice-link.me/enjoy',
            'path': '/entry_name.jpg', 'filename': 'entry_name',
            'modified': '13-4-2016'}
        conditions = {'filename':'entry_name'}
        mappings = {'test_data':'test/blah[]%data%',
            'test_url':'%url% asdasdasd %not_implemented%',
            'test_email':'a%&/&(%/$%$$%& %email%)',
            'test_jpg':'%jpg%'}
        fbx = FakeDropbox()
        mock_dbx.return_value = fbx
        dbc = DropboxChannel()
        mock_fill_recipe_mapping.side_effect = \
            ConditionNotMet()
        dbc.fill_recipe_mappings(trigger_type=1, userid=test_user_id,
            payload=payload, conditions=conditions, mappings=mappings)
        self.assertRaises(ConditionNotMet)
        dbc._fill_mappings.assert_not_called()

    @patch('dropbox.dropbox.Dropbox.files_upload')
    @patch('dropbox.dropbox.Dropbox.files_download_to_file')
    @patch('dropbox.dropbox.Dropbox.files_download')
    @patch('channel_dropbox.channel.DropboxChannel.stopwatch')
    @patch('channel_dropbox.channel.DropboxChannel._dbx_upload')
    @patch('channel_dropbox.channel.DropboxChannel._dbx_download_to_destination')
    @patch('channel_dropbox.channel.DropboxChannel._dbx_download')
    @patch('channel_dropbox.channel.DropboxChannel.handle_action')
    @patch('channel_dropbox.channel.DropboxChannel._fill_data')
    @patch('channel_dropbox.channel.DropboxChannel._fill_mappings')
    @patch('channel_dropbox.channel.DropboxChannel.fill_recipe_mappings')
    @patch('dropbox.Dropbox')
    def test_exceptions(self, mock_dbx, mock_fill_recipe_mapping, mock_fill_mappings,
        mock_fill_data, mock_handle_action, mock_dbx_download,
        mock_download_to_destination, mock_upload, mock_drop_down,
        mock_drop_to, mock_drop_up, mock_stopwatch):


        mock_fill_mappings.side_effect = \
            NotSupportedTrigger
        dbc._fill_data.assert_not_called()

        mock_fill_data.side_effect = \
            ConditionNotMet
        mock_drop_down.assert_not_called()

        mock_fill_data.reset_mock()
        mock_fill_data.side_effect = \
            NotSupportedTrigger
        mock_stopwatch.assert_not_called()

        mock_handle_action.side_effect = \
            NotSupportedAction
        dbc._dbx_upload.assert_not_called()
        dbc._dbx_download.assert_not_called()
        dbc._dbx_download_to_destination.assert_not_called()

        mock_dbx_download.side_effect = \
            dropbox.exceptions.ApiError
        self.assertRaises(ConditionNotMet)
        mock_drop_down.files_download.assert_not_called()

        mock_download_to_destination.side_effect = \
            dropbox.exceptions.ApiError
        self.assertRaises(ConditionNotMet)
        mock_drop_to.assert_not_called()

        mock_upload.side_effect = \
            dropbox.exceptions.ApiError
        self.assertRaises(ConditionNotMet)
        mock_drop_up.assert_not_called()
    '''
