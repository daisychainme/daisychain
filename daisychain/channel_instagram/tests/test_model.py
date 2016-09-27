from django.test import TestCase
from channel_instagram.models import InstagramAccount
from django.contrib.auth.models import User


class ModelTest(TestCase):

    def test__str__(self):
        user = User.objects.create_user("abc")
        instagram_user = InstagramAccount(
                user=user,
                instagram_id="42",
                access_token="123")
        instagram_user.save()

        string = str(instagram_user)
        self.assertEqual(
                string,
                "Instagram Account #42 belongs to user {}".format(user))
