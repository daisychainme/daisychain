from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TransactionTestCase
from core.models import Channel
from channel_twitter.models import TwitterAccount


class ViewTest(TransactionTestCase):

    def setUp(self):

        Channel(name="Dropbox",
                image="/static/channels/dropbox.png",
                color="#007ee5",
                font_color="#ffffff").save()
        Channel(name="Twitter",
                image="/static/channels/twitter.png",
                color="#55acee",
                font_color="#ffffff").save()

        test_user = User.objects.create_user("testuser", password="testtest")

        TwitterAccount(user=test_user).save()

        self.client.force_login(test_user)

    def test_get(self):

        res = self.client.get(reverse("channels:list"))


class DetailViewTest(TransactionTestCase):

    def setUp(self):
        Channel(name="Dropbox",
                image="/static/channels/dropbox.png",
                color="#007ee5",
                font_color="#ffffff").save()
        Channel(name="Twitter",
                image="/static/channels/twitter.png",
                color="#55acee",
                font_color="#ffffff").save()

        test_user = User.objects.create_user("testuser", password="testtest")

        TwitterAccount(user=test_user).save()

        self.client.force_login(test_user)

    def test_get__correct(self):

        res = self.client.get(reverse("channels:detail", args=['twitter']))

    def test_get__not_existent_channel(self):

        res = self.client.get(reverse("channels:detail", args=['notexist']))
