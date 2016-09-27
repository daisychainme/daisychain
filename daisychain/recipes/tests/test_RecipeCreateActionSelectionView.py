from django.core.urlresolvers import reverse
from core.models import (Channel, Trigger, Action)
from .test_utils import TestDataProvider, RecipeTestCase


class RecipeCreateActionSelectionViewTest(RecipeTestCase):

    def setUp(self):
        TestDataProvider.create_channels()
        self.user = TestDataProvider.create_user()
        self.client.force_login(self.user)

    def test_step5__get_invalid_session_channel_without_actions(self):

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)
        wrongChannel = Channel.objects.get(name="Instagram")

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id,
            'action_channel_id': wrongChannel.id
        })
        res = self.client.get(reverse("recipes:new_step5"), follow=True)

        self.assertRedirect("recipes:new_step4", res)

    def test_step5__get_invalid_session_no_trigger(self):

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id
        })
        res = self.client.get(reverse("recipes:new_step5"), follow=True)

        self.assertRedirect("recipes:new_step4", res)

    def test_step5__get_invalid_session_invalid_action_channel(self):

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id,
            'action_channel_id': 99
        })
        res = self.client.get(reverse("recipes:new_step5"), follow=True)

        self.assertRedirect("recipes:new_step4", res)

    def test_step5__post_valid_data(self):

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        testAction = Action.objects.get(channel__name="Twitter",
                                        action_type=101)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id,
            'action_channel_id': testAction.channel.id
        })
        postData = {'action_id': testAction.id}
        res = self.client.post(reverse("recipes:new_step5"),
                               data=postData,
                               follow=True)

        self.assertRedirect("recipes:new_step6", res)

    def test_step5__post_invalid_data(self):

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        testAction = Action.objects.get(channel__name="Twitter",
                                        action_type=101)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id,
            'action_channel_id': testAction.channel.id
        })
        postData = {'action_id': 99}
        res = self.client.post(reverse("recipes:new_step5"),
                               data=postData,
                               follow=True)

        self.assertRedirect("recipes:new_step4", res)
