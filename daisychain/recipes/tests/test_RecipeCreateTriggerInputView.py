from django.core.urlresolvers import reverse
from core.models import (Channel, Trigger, TriggerInput)
from .test_utils import TestDataProvider, RecipeTestCase


class RecipeCreateTriggerInputViewTest(RecipeTestCase):

    def setUp(self):
        TestDataProvider.create_channels()
        self.user = TestDataProvider.create_user()
        self.client.force_login(self.user)

    def test_step3__get_invalid_session_no_trigger(self):

        testTrigger = Trigger.objects.get(channel__name="Dropbox",
                                          trigger_type=101)

        self.set_recipe_draft({
            'trigger_channel_id': testTrigger.channel.id,
        })

        res = self.client.get(reverse("recipes:new_step3"), follow=True)

        self.assertRedirect("recipes:new_step2", res)

    def test_step3__get_invalid_session_invalid_trigger_id(self):

        testTrigger = Trigger.objects.get(channel__name="Dropbox",
                                          trigger_type=101)

        self.set_recipe_draft({
            'trigger_channel_id': testTrigger.channel.id,
            'trigger_id': 99
        })

        res = self.client.get(reverse("recipes:new_step3"), follow=True)

        self.assertRedirect("recipes:new_step2", res)

    def test_step3__get_for_trigger_with_inputs(self):

        testChannel = Channel.objects.get(name="Dropbox")
        testTrigger = Trigger.objects.get(channel=testChannel,
                                          trigger_type=101)

        expectedTriggerInputs = TriggerInput.objects.filter(
                trigger=testTrigger).values()

        self.set_recipe_draft({
            'trigger_channel_id': testChannel.id,
            'trigger_id': testTrigger.id
        })

        res = self.client.get(reverse("recipes:new_step3"))

        self.assertListEqual(list(expectedTriggerInputs),
                             list(res.context['trigger_inputs']))

        self.assertTemplate("recipes/recipe_create.step3.html", res)

    def test_step3__get_for_trigger_without_inputs(self):

        testChannel = Channel.objects.get(name="Dropbox")
        testTrigger = Trigger.objects.get(channel=testChannel,
                                          trigger_type=100)

        self.set_recipe_draft({
            'trigger_channel_id': testChannel.id,
            'trigger_id': testTrigger.id
        })

        res = self.client.get(reverse("recipes:new_step3"), follow=True)

        self.assertRedirect("recipes:new_step4", res)

    def test_step3__post_with_valid_data(self):

        testTrigger = Trigger.objects.get(channel__name="Dropbox",
                                          trigger_type=101)

        testTriggerInputs = TriggerInput.objects.filter(trigger=testTrigger)

        self.set_recipe_draft({
            'trigger_channel_id': testTrigger.channel.id,
            'trigger_id': testTrigger.id
        })

        postData = {}
        expectedRecipeConditions = []
        for input in testTriggerInputs:
            postData['input_%s' % input.id] = 'some_text'
            expectedRecipeConditions.append({
                'id': input.id,
                'value': 'some_text'
            })

        res = self.client.post(reverse("recipes:new_step3"),
                               data=postData,
                               follow=True)

        self.assertEqual(
            expectedRecipeConditions,
            self.client.session['recipe_draft']['recipe_conditions']
        )
        self.assertRedirect("recipes:new_step4", res)
