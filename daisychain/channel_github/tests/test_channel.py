from django.contrib.auth.models import User
from django.test import TestCase
from mock import patch

from channel_github.channel import GithubChannel
from channel_github.config import (CHANNEL_NAME, TRIGGER_TYPE)
from channel_github.models import GithubAccount
from core.channel import (NotSupportedTrigger, NotSupportedAction,
                          ConditionNotMet)

github_url = 'https://api.github.com{}'


class BaseTestCase(TestCase):
    fixtures = ['core/fixtures/initial_data.json']
    class MockResponse:
        def __init__(self, ok, content=None):
            self.ok = ok
            self.content = content

    def setUp(self):
        self.user = self.create_user()
        self.github_account = self.create_github_account(self.user)
        self.channel = GithubChannel()
        self.payload = {
            'repository_name': 'test_repo',
            'repository_url': 'https://github.com/paul/test_repo',
            'head_commit_message': 'test message',
            'head_commit_author': 'paul',
            'repository_full_name': 'paul/test_repo'
        }
        self.to_replace = ['repository_name',
                           'repository_url',
                           'head_commit_message',
                           'head_commit_author']
        self.conditions = {'repository_name': 'paul/test_repo'}

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

    @patch('requests.post')
    @patch('channel_github.channel.GithubChannel._check_for_webhook')
    def test_create_webhook_response_ok(self,
                                        mock_check_for_webhook,
                                        mock_post):
        mock_check_for_webhook.return_value = False
        mock_post.return_value = self.MockResponse(True)
        ret = self.channel.create_webhook(github_account=self.github_account,
                                          repository='test_repo',
                                          events=['push'],
                                          owner='Franz_K')
        expected = '/'.join(['Franz_K', 'test_repo'])
        self.assertEquals(ret, expected)

    @patch('requests.post')
    @patch('channel_github.channel.GithubChannel._check_for_webhook')
    def test_create_webhook_response_invalid(self,
                                             mock_check_for_webhook,
                                             mock_post):
        mock_check_for_webhook.return_value = False
        mock_post.return_value = self.MockResponse(False)
        ret = self.channel.create_webhook(github_account=self.github_account,
                                          repository='test_repo',
                                          events=['push'],
                                          owner='www.example.com')
        self.assertEquals(ret, None)

    @patch('requests.post')
    @patch('channel_github.channel.GithubChannel._check_for_webhook')
    def test_create_webhook_without_owner(self,
                                          mock_check_for_webhook,
                                          mock_post):
        mock_check_for_webhook.return_value = False
        mock_post.return_value = self.MockResponse(True)
        ret = self.channel.create_webhook(github_account=self.github_account,
                                          repository='repo',
                                          events=['push'])
        mock_post.assert_called_once()
        self.assertEquals(ret, '/'.join([self.github_account.username,
                                         'repo']))

    @patch('channel_github.channel.GithubChannel._fire_push_trigger')
    def test_fire_trigger_push(self, mock_fire_push_trigger):
        data = {'commits': 'test', 'pusher': 'test'}
        self.channel.fire_trigger(data)
        mock_fire_push_trigger.assert_called_once_with(data=data)

    @patch('channel_github.channel.GithubChannel._fire_issue_trigger')
    def test_fire_trigger_issue(self, mock_fire_issue_trigger):
        data = {'issue': 'test'}
        self.channel.fire_trigger(data)
        mock_fire_issue_trigger.assert_called_once_with(data=data)

    @patch('core.core.Core.handle_trigger')
    def test_fire_push_trigger(self, mock_handle_trigger):
        data = {
            'repository': {
                'owner': {'name': 'paul'},
                'name': 'test_repo',
                'url': 'https://github.com/paul/test_repo',
                'full_name': 'paul/test_repo'
            },
            'head_commit': {
                'message': 'test message',
                'author': {
                    'name': 'paul'
                }
            }
        }
        self.channel._fire_push_trigger(data=data)
        push_type = TRIGGER_TYPE['push']
        mock_handle_trigger.assert_called_once_with(channel_name=CHANNEL_NAME,
                                                    trigger_type=push_type,
                                                    userid=self.user.id,
                                                    payload=self.payload)

    @patch('channel_github.channel.GithubChannel._replace_mappings')
    def test_fill_recipe_mappings_with_push_trigger(self,
                                                    mock_replace_mappings):
        self.channel.fill_recipe_mappings(trigger_type=TRIGGER_TYPE['push'],
                                          userid=self.user.id,
                                          payload=self.payload,
                                          conditions=self.conditions,
                                          mappings={})

        mock_replace_mappings.assert_called_once_with(mappings={},
                                                      payload=self.payload,
                                                      to_replace=self.to_replace)

    @patch('channel_github.channel.GithubChannel._replace_mappings')
    def test_fill_recipe_mappings_with_ínvalid_trigger(self,
                                                       mock_replace_mappings):
        with self.assertRaises(NotSupportedTrigger):
            self.channel.fill_recipe_mappings(trigger_type=-42,
                                              userid=self.user.id,
                                              payload=self.payload,
                                              conditions=self.conditions,
                                              mappings={})
        self.assertFalse(mock_replace_mappings.called)

    def test_replace_mappings(self):
        mappings = {
            'input1': 'check out %repository_name%',
            'input2': 'last changes by %head_commit_author%'
        }
        res = self.channel._replace_mappings(mappings,
                                             self.to_replace,
                                             self.payload)
        expected = {
            'input1': 'check out test_repo',
            'input2': 'last changes by paul'
        }
        self.assertEquals(res, expected)

    def test_handle_action_raises_exception(self):
        with self.assertRaises(NotSupportedAction):
            self.channel.handle_action(TRIGGER_TYPE['push'],
                                       self.user.id,
                                       {})

    @patch('requests.get')
    def test_check_for_webhook(self, mock_get):
        test_content = b'[{"config": {"url": "https://example.com/github/hooks"}}]'
        mock_get.return_value = self.MockResponse(True,
                                                  content=test_content)
        self.assertTrue(self.channel._check_for_webhook('test',
                                                        'header'))

    @patch('channel_github.channel.GithubChannel._check_for_webhook')
    def test_create_webhook_alrready_exists(self, mock_check_for_webhook):
        # mock already existing webhook!
        mock_check_for_webhook.return_value = True
        res = self.channel.create_webhook(github_account=self.github_account,
                                          repository='test_repo',
                                          events=['push'])
        expected = '/'.join([self.github_account.username, 'test_repo'])
        self.assertEquals(expected, res)

    def test_fill_recipe_mapping_with_not_matching_repository_name(self):
        conditions = {'repository_name': 'paul/different_repo'}
        with self.assertRaises(ConditionNotMet):
            self.channel.fill_recipe_mappings(trigger_type=TRIGGER_TYPE['push'],
                                              userid=self.user.id,
                                              payload=self.payload,
                                              conditions=conditions,
                                              mappings={})
