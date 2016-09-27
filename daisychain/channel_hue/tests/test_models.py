from django.contrib.auth.models import User
from django.test import TestCase
from channel_hue.models import HueAccount

class TestModelsHueAccount(TestCase):

    def test_account_str_len(self):
        user = User.objects.create_user('John')
        hue_account = HueAccount(
            user = user,
            bridge_ip = 'test_access_token',
            access_token = '131321'
        )
        hue_account.save()
        string = str(hue_account)
        self.assertEqual(string,
            "Phillips HUE got User {}".format(
                user))
        self.assertEqual(len(HueAccount.objects.all()), 1)
