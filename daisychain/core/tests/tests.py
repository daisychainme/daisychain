from django.test import TestCase, RequestFactory
from django.contrib.sites.models import Site
from django.core.urlresolvers import resolve, reverse
from django.http import HttpRequest

from django.test.client import Client
from django.contrib.auth.models import User
from mock import Mock, patch

from core import tasks
from core.channel import (NotSupportedTrigger, NotSupportedAction,
                          ConditionNotMet)
from core.models import (Action, ActionInput, Channel, Recipe,
                         RecipeMapping, RecipeCondition,
                         Trigger, TriggerInput, TriggerOutput)
from core.utils import get_local_url, replace_text_mappings


class BaseTestCase(TestCase):

    fixtures = ['core/fixtures/initial_data.json']

    def create_user(self):
        user = User.objects.create_user('Superuser',
                                        'superuser@super.com',
                                        'Password')
        user.save()
        return user

    def setUp(self):
        self.client = Client()
        self.user = self.create_user()
        self.user.save()
        self.trigger_channel = self.create_channel("Twitter")
        self.action_channel = self.trigger_channel
        self.trigger = self.create_trigger(channel=self.trigger_channel,
                                           trigger_type=200,
                                           name="New Image")
        self.action = self.create_action(channel=self.action_channel,
                                         action_type=200,
                                         name="Post Image")
        self.trigger_output = "image_data"
        self.trigger_input = self.create_trigger_input(trigger=self.trigger,
                                                       name="test input")
        self.action_input = self.create_action_input(self.action,
                                                     "image_data",
                                                     "image")
        self.recipe = self.create_recipe(self.trigger, self.action, self.user)
        self.recipe_mapping = self.create_recipe_mapping(
                self.recipe,
                self.trigger_output,
                self.action_input)
        self.recipe_condition = self.create_recipe_condition(
                self.recipe,
                self.trigger_input,
                "test value")
        self.payload = {"foo": "bar"}

        self.conditions_dict = {"test input": "test value"}


class TaskTest(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.inputs_mock = {self.action_input.name: self.trigger_output}
        self.inputs_filled = {'test': 'test_data'}

    def create_channel(self, name):
        channel = Channel(name=name)
        channel.save()
        return channel

    def create_trigger(self, channel, trigger_type, name):
        t = Trigger(channel=channel, trigger_type=trigger_type, name=name)
        t.save()
        return t

    def create_trigger_input(self, trigger, name):
        trigger_input = TriggerInput(trigger=trigger, name=name)
        trigger_input.save()
        return trigger_input

    def create_trigger_output(self, trigger, name, mime_type):
        trigger_output = TriggerOutput(trigger=trigger,
                                       name=name,
                                       mime_type=mime_type)
        trigger_output.save()
        return trigger_output

    def create_action(self, channel, action_type, name):
        action = Action(channel=channel, action_type=action_type, name=name)
        action.save()
        return action

    def create_action_input(self, action, name, mime_type):
        action_input = ActionInput(action=action,
                                   name=name,
                                   mime_type=mime_type)
        action_input.save()
        return action_input

    def create_recipe(self, trigger, action, user):
        recipe = Recipe(trigger=trigger, action=action, user=user)
        recipe.save()
        return recipe

    def create_recipe_mapping(self, recipe, trigger_output, action_input):
        mapping = RecipeMapping(recipe=recipe,
                                trigger_output=trigger_output,
                                action_input=action_input)
        mapping.save()
        return mapping

    def create_recipe_condition(self, recipe, trigger_input, value):
        cond = RecipeCondition(recipe=recipe, trigger_input=trigger_input,
                               value=value)
        cond.save()
        return cond

    @patch('channel_twitter.channel.TwitterChannel.fill_recipe_mappings')
    @patch('channel_twitter.channel.TwitterChannel.handle_action')
    def test_task_with_registered_user(self,
                                       mock_handle_action,
                                       mock_fill_recipe_mappings):
        mock_fill_recipe_mappings.return_value = self.inputs_filled

        tasks.handle_trigger(self.trigger_channel.name,
                             self.trigger.trigger_type,
                             self.user.pk,
                             self.payload)

        mock_handle_action.assert_called_once_with(
                                        action_type=self.action.action_type,
                                        userid=self.user.id,
                                        inputs=self.inputs_filled)

        mock_fill_recipe_mappings.assert_called_once_with(
                                        trigger_type=self.trigger.trigger_type,
                                        userid=self.user.id,
                                        payload=self.payload,
                                        conditions=self.conditions_dict,
                                        mappings=self.inputs_mock)

    @patch('channel_twitter.channel.TwitterChannel.handle_action')
    @patch('channel_twitter.channel.TwitterChannel.fill_recipe_mappings')
    def test_task_with_invalid_user_id(self,
                                       mock_fill_recipe_mappings,
                                       mock_handle_action):
        tasks.handle_trigger(channel_name=self.trigger_channel.name,
                             trigger_type=self.trigger.trigger_type,
                             user_id=-42,
                             payload=self.payload)
        mock_handle_action.assert_not_called()
        mock_fill_recipe_mappings.assert_not_called()

    @patch('channel_twitter.channel.TwitterChannel.handle_action')
    @patch('channel_twitter.channel.TwitterChannel.fill_recipe_mappings')
    def test_task_with_invalid_channel_id(self,
                                          mock_fill_recipe_mappings,
                                          mock_handle_action):
        tasks.handle_trigger(channel_name="NotExistentChannel",
                             trigger_type=self.trigger.trigger_type,
                             user_id=self.user.id,
                             payload=self.payload)
        mock_handle_action.assert_not_called()
        mock_fill_recipe_mappings.assert_not_called()

    def test_get_current_url(self):
        domain = 'https://' + Site.objects.get_current().domain
        self.assertEquals(get_local_url(), domain)

    def test_replace_mappings(self):
        mappings = {
            'input1': 'check out %repository_name%',
            'input2': 'last changes by %head_commit_author%'
        }
        to_replace = ['repository_name',
                      'repository_url',
                      'head_commit_message',
                      'head_commit_author']
        payload = {
            'repository_name': 'test_repo',
            'repository_url': 'https://github.com/paul/test_repo',
            'head_commit_message': 'test message',
            'head_commit_author': 'paul',
            'repository_full_name': 'paul/test_repo'
        }
        res = replace_text_mappings(mappings,
                                    to_replace,
                                    payload)
        expected = {
            'input1': 'check out test_repo',
            'input2': 'last changes by paul'
        }
        self.assertEquals(res, expected)

    @patch('channel_twitter.channel.TwitterChannel.handle_action')
    @patch('channel_twitter.channel.TwitterChannel.fill_recipe_mappings')
    def test_task_not_supported_trigger(self,
                                        mock_fill_recipe_mappings,
                                        mock_handle_action):
        mock_fill_recipe_mappings.side_effect = NotSupportedTrigger
        tasks.handle_trigger(self.trigger_channel.name,
                             self.trigger.trigger_type,
                             self.user.pk,
                             self.payload)
        mock_fill_recipe_mappings.assert_called_once()
        mock_handle_action.assert_not_called()

    @patch('channel_twitter.channel.TwitterChannel.handle_action')
    @patch('channel_twitter.channel.TwitterChannel.fill_recipe_mappings')
    def test_task_condition_not_met(self,
                                    mock_fill_recipe_mappings,
                                    mock_handle_action):
        mock_fill_recipe_mappings.side_effect = ConditionNotMet
        tasks.handle_trigger(self.trigger_channel.name,
                             self.trigger.trigger_type,
                             self.user.pk,
                             self.payload)
        mock_fill_recipe_mappings.assert_called_once()
        mock_handle_action.assert_not_called()

    @patch('channel_twitter.channel.TwitterChannel.handle_action')
    @patch('channel_twitter.channel.TwitterChannel.fill_recipe_mappings')
    def test_task_fill_recipe_mappings_raises_unspecified_exception(
            self, mock_fill_recipe_mappings, mock_handle_action):

        mock_fill_recipe_mappings.side_effect = Exception
        tasks.handle_trigger(self.trigger_channel.name,
                             self.trigger.trigger_type,
                             self.user.pk,
                             self.payload)
        mock_fill_recipe_mappings.assert_called_once()
        mock_handle_action.assert_not_called()

    @patch('channel_twitter.channel.TwitterChannel.handle_action')
    @patch('channel_twitter.channel.TwitterChannel.fill_recipe_mappings')
    def test_task_handle_action_not_supported_action(self,
                                                     mock_fill_recipe_mappings,
                                                     mock_handle_action):
        mock_handle_action.side_effect = NotSupportedAction
        tasks.handle_trigger(self.trigger_channel.name,
                             self.trigger.trigger_type,
                             self.user.pk,
                             self.payload)
        mock_fill_recipe_mappings.assert_called_once()
        mock_handle_action.assert_called_once()

    @patch('channel_twitter.channel.TwitterChannel.handle_action')
    @patch('channel_twitter.channel.TwitterChannel.fill_recipe_mappings')
    def test_task_handle_action_unspecified_exception(
            self, mock_fill_recipe_mappings, mock_handle_action):

        mock_handle_action.side_effect = Exception
        tasks.handle_trigger(self.trigger_channel.name,
                             self.trigger.trigger_type,
                             self.user.pk,
                             self.payload)
        mock_fill_recipe_mappings.assert_called_once()
        mock_handle_action.assert_called_once()
