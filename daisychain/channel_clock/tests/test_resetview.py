from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from channel_clock.models import ClockUserSettings


class ResetViewTest(TestCase):

    def setUp(self):

        self.url = reverse("clock:disconnect")

        self.bob = User.objects.create_user('bob')
        ClockUserSettings(user=self.bob, utcoffset=120).save()

        self.mallory = User.objects.create_user('mallory')

    def test_get__valid_user(self):

        self.client.force_login(self.bob)
        res = self.client.get(self.url)

    def test_get__invalid_user(self):

        self.client.force_login(self.mallory)
        res = self.client.get(self.url)
