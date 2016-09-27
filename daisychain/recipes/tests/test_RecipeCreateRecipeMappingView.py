from django.core.urlresolvers import reverse
from core.models import (Trigger, TriggerInput, TriggerOutput,
                         Action, ActionInput)
from .test_utils import TestDataProvider, RecipeTestCase


class RecipeCreateRecipeMappingViewTest(RecipeTestCase):

    def setUp(self):
        TestDataProvider.create_channels()
        self.user = TestDataProvider.create_user()
        self.client.force_login(self.user)

    def test_step6__get_invalid_session_no_trigger(self):

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        testAction = Action.objects.get(channel__name="Twitter",
                                        action_type=101)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'action_id': testAction.id,
            'action_channel_id': testAction.channel.id
        })
        res = self.client.get(reverse("recipes:new_step6"), follow=True)

        self.assertRedirect("recipes:new_step2", res)

    def test_step6__get_invalid_session_invalid_trigger(self):

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        testAction = Action.objects.get(channel__name="Twitter",
                                        action_type=101)

        self.client.session.clear()
        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': -100,
            'action_id': testAction.id,
            'action_channel_id': testAction.channel.id
        })
        res = self.client.get(reverse("recipes:new_step6"), follow=True)

        self.assertRedirect("recipes:new_step2", res)

    def test_step6__get_invalid_session_no_action(self):

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        testAction = Action.objects.get(channel__name="Twitter",
                                        action_type=101)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id,
            'action_channel_id': testAction.channel.id
        })
        res = self.client.get(reverse("recipes:new_step6"), follow=True)

        self.assertRedirect("recipes:new_step5", res)

    def test_step6__get_invalid_session_invalid_action(self):

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        testAction = Action.objects.get(channel__name="Twitter",
                                        action_type=101)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id,
            'action_id': 99,
            'action_channel_id': testAction.channel.id
        })
        res = self.client.get(reverse("recipes:new_step6"), follow=True)

        self.assertRedirect("recipes:new_step5", res)

    def test_step6__get_for_action_without_inputs(self):

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        testAction = Action.objects.get(channel__name="Twitter",
                                        action_type=404)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id,
            'action_id': testAction.id,
            'action_channel_id': testAction.channel.id
        })
        res = self.client.get(reverse("recipes:new_step6"), follow=True)

        self.assertRedirect("recipes:new_step7", res)

    def test_step6__post_valid_data(self):

        sessionTrigger = Trigger.objects.get(channel__name="Instagram",
                                             trigger_type=101)
        sessionTriggerInput = TriggerInput.objects.get(trigger=sessionTrigger)

        testAction = Action.objects.get(channel__name="Twitter",
                                        action_type=101)

        triggerOutputCaption = TriggerOutput.objects.get(
                trigger=sessionTrigger,
                name="caption")
        triggerOutputThumbnail = TriggerOutput.objects.get(
                trigger=sessionTrigger,
                name="thumbnail")
        actionInputStatus = ActionInput.objects.get(
                action=testAction,
                name="Status")
        actionInputPhoto = ActionInput.objects.get(
                action=testAction,
                name="Photo")

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id,
            'recipe_conditions': [{
                'id': sessionTriggerInput.id,
                'value': 'foodstagram'
            }],
            'action_id': testAction.id,
            'action_channel_id': testAction.channel.id
        })

        postData = {
            'input_%s' % actionInputStatus.id: triggerOutputCaption.name,
            'input+%s' % actionInputPhoto.id: triggerOutputThumbnail.name}

        res = self.client.post(reverse("recipes:new_step6"),
                               data=postData,
                               follow=True)

        self.assertRedirect("recipes:new_step7", res)
