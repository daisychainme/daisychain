from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from channel_clock.views import SetupView
from channel_clock.models import ClockUserSettings


class SetupViewTest(TestCase):

    def setUp(self):

        self.url = reverse("clock:connect")

        self.max_muster = User.objects.create_user("max_muster")
        self.client.force_login(self.max_muster)

    def test_append_query_params(self):

        url = "http://example.com/?a=1&a=5&b=4"

        new_url = SetupView().append_query_params(url, a=3)

        self.assertIn('a=1', new_url)
        self.assertIn('a=3', new_url)
        self.assertIn('a=5', new_url)
        self.assertIn('b=4', new_url)

    def test_get__disconnected_user(self):

        getData = {
            "next": "/test-redirect-uri/"
        }
        res = self.client.get(self.url, getData)
        res = self.client.get(self.url)

    def test_get__connected_user(self):

        ClockUserSettings.objects.create(user=self.max_muster, utcoffset=0)
        res = self.client.get(self.url)

    def test_post__error(self):

        postData = { "offset": 418230471203841723042 }
        res = self.client.post(self.url, postData)

    def test_post__success(self):

        postData = { "offset": 42 }
        res = self.client.post(self.url, postData)
