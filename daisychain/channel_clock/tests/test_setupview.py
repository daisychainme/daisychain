from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase


class SetupViewTest(TestCase):

    def setUp(self):

        self.url = reverse("clock:connect")

        max_muster = User.objects.create_user("max_muster")
        self.client.force_login(max_muster)

    def test_get(self):

        getData = {
            "next": "/test-redirect-uri/"
        }
        res = self.client.get(self.url, getData)
        res = self.client.get(self.url)

    def test_post__error(self):

        postData = { "offset": 418230471203841723042 }
        res = self.client.post(self.url, postData)

    def test_post__success(self):

        postData = { "offset": 42 }
        res = self.client.post(self.url, postData)
