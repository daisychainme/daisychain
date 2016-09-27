from django.contrib.auth.models import User
from django.test import TestCase

from channel_facebook.models import FacebookAccount


class ModelTest(TestCase):
    fixtures = ['initial_data.json']

    def test__str__(self):
        user = User.objects.create_user("daisychain")
        facebook_user = FacebookAccount(
            user=user,
            username="42",
            access_token="123"
        )
        facebook_user.save()

        string = str(facebook_user)
        self.assertEqual(
            string,
            "Facebook Account of User: {}".format(user))
