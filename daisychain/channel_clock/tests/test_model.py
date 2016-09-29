from django.contrib.auth.models import User
from django.test import TestCase
from channel_clock.models import ClockUserSettings


class ModelTest(TestCase):

    def test___str__(self):
        alice = User.objects.create_user('alice')
        alice_settings = ClockUserSettings(user=alice, utcoffset=120)
        expected = "Clock settings for user alice (id={})".format(alice.id)
        self.assertEqual(expected, str(alice_settings))
