from django.contrib.auth.models import User
from django.test import TestCase
from .models import DropboxAccount, DropboxUser

class TestModelsDropboxAccount(TestCase):

    def test_account_str_len(self):
        user = User.objects.create_user('John')
        dbx_account = DropboxAccount(
            user = user,
            access_token = 'test_access_token',
            cursor = ''
        )
        dbx_account.save()
        string = str(dbx_account)
        self.assertEqual(string,
            "DropboxAccount belongs to user {}".format(
                user))
        self.assertEqual(len(DropboxAccount.objects.all()), 1)

class TestModelsDropboxUser(TestCase):

    def test_user_str_len(self):
        user = User.objects.create_user('John')
        dbx_account = DropboxAccount(
            user = user,
            access_token = '_test_access_token',
            cursor = '',
        )
        dbx_account.save()
        dbx_user = DropboxUser(
            dropbox_account = dbx_account,
            dropbox_userid = 4211,
            display_name = "John Doe",
            email = "john.doe@test.org",
            profile_photo_url = "url.to/the_profile_photo",
            disk_used = 4234.234,
            disk_allocated = 12345678.4444
        )
        dbx_user.save()
        string = str(dbx_user)
        self.assertEqual(string, "Dropbox User #4211 belongs to DropboxAccount {}".format(
            dbx_account))
        self.assertEqual(len(User.objects.all()), 1)
