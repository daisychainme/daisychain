from django.test import TestCase
from django.utils import timezone
from django.test.client import Client
from django.contrib.auth.models import User

from channel_facebook.channel import FacebookChannel
from channel_facebook.models import FacebookAccount

from core import models

class FacebookBaseTestCase(TestCase):
    fixtures = ['core/fixtures/initial_data.json','channel_facebook/fixtures/initial_data.json']

    class MockResponse:
        def __init__(self, json_data, status_code, ok):
            self.json_data = json_data
            self.status_code = status_code
            self.ok = ok

        def json(self):
            return self.json_data

    def setUp(self):
        self.time = timezone.now()
        self.user = self.create_user()
        self.facebook_account = self.create_facebook_account(self.user)
        self.channel = FacebookChannel()
        self.channel_name = models.Channel.objects.get(name="Facebook").name
        self.channel_id = models.Channel.objects.get(name="Facebook").id
        self.client = Client()
        self.conditions = {'hashtag': '#me'}
        self.fields = 'message,actions,full_picture,picture,from,created_time,link,permalink_url,type,description'
        self.webhook_data = {
            "time": self.time,
            "id": "101915710270588",
            "changed_fields": ["statuses"],
            "uid": "101915710270588"
        }

    def create_user(self):
        user = User.objects.create_user('Superuser',
                                        'superuser@super.com',
                                        'Password')
        user.save()
        return user

    def create_facebook_account(self, user):
        facebook_account = FacebookAccount(user=user,
                                           username='101915710270588',
                                           access_token='test token',
                                           last_post_time=timezone.now()
                                           )
        facebook_account.save()
        return facebook_account