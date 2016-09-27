from django.test import TestCase
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from mock import Mock, patch
import json

from channel_github.models import GithubAccount
from channel_github.channel import GithubChannel
from channel_github.forms import TriggerInputForm
from core.models import Trigger, Channel, TriggerInput

github_url = 'https://api.github.com{}'

class BaseTestCase(TestCase):

    class MockResponse:
        def __init__(self, ok, content=None):
            self.ok = ok
            self.content = content


    def setUp(self):
        self.user = self.create_user()
        self.channel = GithubChannel()

    def create_user(self):
        user = User.objects.create_user('Superuser',
            'superuser@super.com',
            'Password')
        user.save()
        return user

    def create_github_account(self, user):
        github_account = GithubAccount(user=user,
                                       username='paul',
                                       access_token='test token')
        github_account.save()
        return github_account

    def create_draft_object(self, id=5000):
        session = self.client.session
        session['recipe_draft'] = {'trigger_id': id}
        session.save()

    def create_draft_object_without_trigger_id(self):
        session = self.client.session
        session['recipe_draft'] = {}
        session.save()


class TestTriggerInputForm(TestCase):

    def test_form_valid(self):
        form_data = {'repository_name': 'Repo'}
        form = TriggerInputForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_form_invalid_empty_repo(self):
        form_data = {'repository_name': ''}
        form = TriggerInputForm(data=form_data)
        self.assertFalse(form.is_valid())


class TestTriggerInputView(BaseTestCase):

    def test_trigger_input(self):
        self.client.force_login(self.user)
        self.create_draft_object()
        response = self.client.get(reverse('github:trigger_input'))
        auth_url = '{}?next={}'.format(reverse('github:connect'),
                                   reverse('github:get_trigger_inputs'))
        self.assertRedirects(response,
                             auth_url,
                             status_code=302,
                             target_status_code=302)

    def test_trigger_input_without_trigger_id_in_draft(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('github:trigger_input'))
        self.assertRedirects(response,
                             reverse('recipes:new_step2'),
                             status_code=302,
                             target_status_code=302)

class TestCreateTriggerInputView(BaseTestCase):

    def test_get_trigger_inputs_without_draft(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('github:get_trigger_inputs'))
        self.assertRedirects(response,
                             reverse('recipes:new_step2'),
                             status_code=302,
                             target_status_code=302)

    def test_get_trigger_inputs_without_authorization(self):
        self.client.force_login(self.user)
        self.create_draft_object()
        response = self.client.get(reverse('github:get_trigger_inputs'))
        auth_url = '{}?next={}'.format(reverse('github:connect'),
                                   reverse('github:get_trigger_inputs'))
        self.assertRedirects(response,
                             auth_url,
                             status_code=302,
                             target_status_code=302)

    def test_get_trigger_inputs_get_request(self):
        self.create_draft_object()
        self.client.force_login(self.user)
        self.create_github_account(self.user)
        response = self.client.get(reverse('github:get_trigger_inputs'))
        self.assertEquals(response.status_code, 200)

    @patch('channel_github.channel.GithubChannel.create_webhook')
    @patch('channel_github.channel.GithubChannel.repo_exists')
    def test_get_trigger_inputs_valid_post_request(self,
                                                   mock_repo_exists,
                                                   mock_create_webhook):
        self.client.force_login(self.user)
        self.create_github_account(self.user)
        mock_repo_exists.return_value = True

        # mock the trigger:
        c = Channel(name="Github", color = "#FFFFFF", image="test",
                    font_color="test")
        c.save()
        t = Trigger()
        t.trigger_type = 100
        t.channel= c
        t.name = "push"
        t.save()
        ti = TriggerInput(trigger=t, name='test')
        ti.save()
        self.create_draft_object(id=t.pk)
        # mock the data that is passed into the form
        post_data = {'repository_name': 'repo',
                     'repository_owner': 'username'}

        mock_create_webhook.return_value = 'username/repo'
        response = self.client.post(reverse('github:get_trigger_inputs'),
                         post_data)
        self.assertEquals(response.url, reverse('recipes:new_step4'))
        draft = self.client.session['recipe_draft']
        self.assertEquals(draft['recipe_conditions'][0]['id'], ti.id)
        self.assertEquals(draft['recipe_conditions'][0]['value'],
                          'username/repo')

    @patch('channel_github.channel.GithubChannel.create_webhook')
    @patch('channel_github.channel.GithubChannel.repo_exists')
    def test_get_trigger_inputs_invalid_post_request(self,
                                                     mock_repo_exists,
                                                     mock_create_webhook):
        self.client.force_login(self.user)
        self.create_github_account(self.user)
        mock_repo_exists.return_value = True

        # mock the trigger:
        c = Channel(name="Github", color = "#FFFFFF", image="test",
                    font_color="test")
        c.save()
        t = Trigger()
        t.trigger_type = 100
        t.channel= c
        t.name = "push"
        t.save()
        ti = TriggerInput(trigger=t, name='test')
        ti.save()
        self.create_draft_object(id=t.pk)
        # mock the data that is passed into the form
        post_data = {'repository_name': 'repo',
                     'repository_owner': 'username'}

        mock_create_webhook.return_value = None
        response = self.client.post(reverse('github:get_trigger_inputs'),
                         post_data)
        self.assertEquals(response.url, reverse('github:trigger_input'))
        draft = self.client.session['recipe_draft']
        self.assertTrue('recipe_conditions' not in draft)

    def test_post_without_trigger_id_in_draft(self):
        self.client.force_login(self.user)
        self.create_draft_object_without_trigger_id()
        resp = self.client.post(reverse('github:get_trigger_inputs'))
        self.assertRedirects(resp,
                             reverse('recipes:new_step2'),
                             status_code=302,
                             target_status_code=302)

    def test_post_without_github_account(self):
        self.client.force_login(self.user)
        self.create_draft_object()
        resp = self.client.post(reverse('github:get_trigger_inputs'))
        expected = '{}?next={}'.format(reverse('github:connect'),
                                       reverse('github:get_trigger_inputs'))
        self.assertRedirects(resp,
                             expected,
                             status_code=302,
                             target_status_code=302)



class TestWebhookView(BaseTestCase):

    @patch('json.loads')
    @patch('channel_github.channel.GithubChannel.fire_trigger')
    def test_webhook_post(self, mock_fire_trigger, mock_loads):
        mock_payload = {'test_key': 'test_val'}
        mock_loads.return_value = mock_payload
        self.client.post(reverse('github:hooks'))
        mock_fire_trigger.assert_called_once_with(mock_payload)
