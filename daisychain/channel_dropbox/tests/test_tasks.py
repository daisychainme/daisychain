from django.test import TestCase
from .models import DropboxAccount, DropboxUser
from django.contrib.auth.models import User
from unittest.mock import patch, Mock
from channel_dropbox.tasks import fireTrigger
import dropbox
from dropbox.files import ListFolderResult, FileMetadata, GetTemporaryLinkResult
from dropbox.users import Account, Name, SpaceUsage,\
    SpaceAllocation, IndividualSpaceAllocation

class FakeDropbox():
    def files_list_folder(self, path, recursive,
                include_media_info, include_deleted):
        result = ListFolderResult()
        result.cursor = "foo"
        result.entries = [FakeFileMetadata()]
        result.has_more = False
        return result

    def files_list_folder_continue(self, cursor):
        result = ListFolderResult(cursor=cursor)
        result.entries = [FakeFileMetadata()]
        result.has_more = False
        return result

    def users_get_current_account(self):
        account = Account(
            name = Name(display_name="John Doe"),
            email = "john.doe@test.org",
            profile_photo_url  = "url.to/the_profile_photo"
        )
        return account
    def users_get_space_usage(self):
        indi = self.get_individual()
        disk = SpaceUsage(
            used = 4234234000,
            allocation = SpaceAllocation.individual(indi)
        )
        return disk
    def get_individual(self):
        individual = IndividualSpaceAllocation(allocated=12345678444400)
        return individual

    def files_get_temporary_link(self, path):
        result = GetTemporaryLinkResult()
        result.link = "www.nice-link.me/enjoy"
        return result

class FakeFileMetadata(FileMetadata):
    path_lower = ''
    name = "entry_name.jpg"
    path_display = "/entry_name.jpg"
    server_modified = "13-4-2016"
    size = 112312

class BaseTestCase(TestCase):

    def create_dropbox_cursor(self):
        user = User.objects.create_user('John')
        self.dbx_account = DropboxAccount(
            user = user,
            access_token = '_test_access_token',
            cursor = 'foobar',
        )
        self.dbx_account.save()
        self.assertEqual(len(DropboxAccount.objects.all()), 1)
        return self.dbx_account

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

    def create_dbx_user_changed(self):
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

    def create_dbx_user_unchanged(self):
        dbx_account = self.create_dropbox_cursor()
        self.dbx_user = DropboxUser(
            dropbox_account = dbx_account,
            dropbox_userid = 4211,
            display_name = "John Doe",
            email = "john.doe@test.org",
            profile_photo_url = "url.to/the_profile_photo",
            disk_used = 4234.2340,
            disk_allocated = 12345678.4444
        )
        self.dbx_user.save()
        self.assertEqual(len(DropboxAccount.objects.all()), 1)
        return self.dbx_user

class TestFireTrigger(BaseTestCase):

    @patch('core.core.Core.handle_trigger')
    @patch('dropbox.Dropbox')
    def test_change_data(self, mock_dbx, mock_core):
        #self.create_dropbox()
        self.create_dbx_user_changed()
        fbx = FakeDropbox()
        mock_dbx.return_value = fbx
        #test if user updated
        fireTrigger(4211)
        user = DropboxUser.objects.get(dropbox_userid=4211)
        self.assertEqual(user.display_name, "John Doe")
        self.assertEqual(user.email, "john.doe@test.org")
        self.assertEqual(user.profile_photo_url, "url.to/the_profile_photo")
        self.assertEqual(float(user.disk_used), 434.2340)
        self.assertEqual(float(user.disk_allocated), 12345678.4444)

        user_info = {'email': 'john.doe@test.org',
            'disk_allocated': 12345678444400, 'profile_photo_url':
            'url.to/the_profile_photo', 'display_name': 'John Doe'}

        payload = {'url': 'www.nice-link.me/enjoy', 'size': 0.112312,
                    'filename': 'entry_name.jpg', 'path': '/entry_name.jpg',
                    'file_extension': 'jpg'}

        mock_core.assert_called_with(channel_id=770, trigger_type=1, userid=1,
            payload=payload)
        mock_core.assert_any_call(channel_id=770, trigger_type=5, userid=1,
            payload=user_info)
        mock_core.assert_any_call(channel_id=770, trigger_type=2, userid=1, payload=payload)


    @patch('core.core.Core.handle_trigger')
    @patch('dropbox.Dropbox')
    def test_unchanged(self, mock_dbx, mock_core):
        #self.create_dropbox()
        self.create_dbx_user_unchanged()
        fbx = FakeDropbox()
        mock_dbx.return_value = fbx
        fireTrigger(4211)

        payload = {'url': 'www.nice-link.me/enjoy', 'size': 0.112312,
                    'filename': 'entry_name.jpg', 'path': '/entry_name.jpg',
                    'file_extension': 'jpg'}
        self.assertEqual(True, mock_core.called)#_with(channel_id=770, trigger_type=2, userid=1, payload=payload)
        self.assertEqual(mock_core.call_count, 2)
