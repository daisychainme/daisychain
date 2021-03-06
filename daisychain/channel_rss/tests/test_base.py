from django.test import TestCase
from django.contrib.auth.models import User

from core.models import (RecipeCondition, Recipe, TriggerInput, Trigger, Action,
                         ActionInput, RecipeMapping, TriggerOutput, Channel)


class BaseTest(TestCase):

    def setUp(self):
        self.user = self.create_user('alice', 'foo@bar.com', 'hunter2')
        self.feeds = ['www.example.com/rss', 'www.foobar.net/rss']
        self.trigger_channel = self.create_channel('RSS', 43000)
        self.action_channel = self.create_channel('Twitter')
        self.trigger = self.create_trigger(channel=self.trigger_channel,
                                           trigger_type=200,
                                           name="New Entries")
        self.action = self.create_action(channel=self.action_channel,
                                         action_type=200,
                                         name="Post Status")
        self.trigger_output = 'summaries_and_links'
        self.trigger_input = self.create_trigger_input(trigger=self.trigger,
                                                       name="feed_url")
        self.action_input = self.create_action_input(self.action,
                                                     'status',
                                                     'text')
        self.recipe = self.create_recipe(self.trigger, self.action, self.user)
        self.create_recipe_mapping(
            self.recipe,
            self.trigger_output,
            self.action_input)
        # create recipe conditions corresponding to the two feeds
        self.create_recipe_condition(self.recipe,
                                     self.trigger_input,
                                     self.feeds[0])
        # second recipe
        self.recipe2 = self.create_recipe(self.trigger, self.action, self.user)
        self.create_recipe_mapping(
            self.recipe2,
            self.trigger_output,
            self.action_input)
        self.create_recipe_condition(self.recipe2,
                                     self.trigger_input,
                                     self.feeds[1])


    def create_channel(self, name, channel_id=None):
        channel = Channel(name=name)
        if channel_id:
            channel.id = channel_id
        channel.save()
        return channel

    def create_user(self, username, email, password):
        user = User.objects.create_user(username,
                                        email,
                                        password)
        user.save()
        return user

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