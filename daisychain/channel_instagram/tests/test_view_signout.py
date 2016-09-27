from django.core.urlresolvers import reverse
from django.test import TransactionTestCase
from channel_instagram.views import SESSKEY_OAUTH_NEXT_URI, SESSKEY_OAUTH_VERIFY_TOKEN
from channel_instagram.models import InstagramAccount
from django.contrib.auth.models import User
import json
import responses
from urllib.parse import urlsplit, parse_qs


class SignoutViewTest(TransactionTestCase):

    def setUp(self):
        self.max_muster = User.objects.create_user("max_muster")
        self.client.force_login(self.max_muster)
        self.url = reverse("instagram:disconnect")

    def test_get__correct(self):

        InstagramAccount(user=self.max_muster).save()

        res = self.client.get(self.url)

        users = InstagramAccount.objects.filter(user=self.max_muster).count()
        self.assertEqual(users, 0)

    def test_get__incorrect(self):

        res = self.client.get(self.url)

        users = InstagramAccount.objects.filter(user=self.max_muster).count()
        self.assertEqual(users, 0)
