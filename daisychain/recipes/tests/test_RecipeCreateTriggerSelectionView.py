from django.core.urlresolvers import reverse
from core.models import (Channel, Trigger)
from .test_utils import TestDataProvider, RecipeTestCase
from mock import MagicMock, patch


class RecipeCreateViewTest(RecipeTestCase):

    def setUp(self):
        TestDataProvider.create_channels()
        self.user = TestDataProvider.create_user()
        self.client.force_login(self.user)

    def test_step2_get(self):

        testChannel = Channel.objects.get(name="Dropbox")

        expectedTriggers = Trigger.objects.filter(channel=testChannel).values()

        self.set_recipe_draft({
            'trigger_channel_id': testChannel.id
        })

        res = self.client.get(reverse("recipes:new_step2"))

        self.assertListEqual(list(expectedTriggers),
                             list(res.context['triggers']))

        self.assertTemplate("recipes/recipe_create.step2.html", res)

    def test_step2_get_invalid_session_no_channel(self):

        res = self.client.get(reverse("recipes:new_step2"), follow=True)

        self.assertRedirect("recipes:new_step1", res)

    def test_step2_get_invalid_session_invalid_channel(self):

        self.set_recipe_draft({
            'trigger_channel_id': 99
        })

        res = self.client.get(reverse("recipes:new_step2"), follow=True)

        self.assertRedirect("recipes:new_step1", res)

    def test_step2__get_invalid_session_invalid_channel(self):

        wrongChannel = Channel.objects.get(name="Twitter")

        self.set_recipe_draft({
            'trigger_channel_id': wrongChannel.id
        })

        res = self.client.get(reverse("recipes:new_step2"), follow=True)

        self.assertRedirect("recipes:new_step1", res)

    def test_step2__post_trigger_with_inputs(self):

        testChannel = Channel.objects.get(name="Dropbox")

        expectedTrigger = Trigger.objects.get(channel=testChannel,
                                              trigger_type=101)

        self.set_recipe_draft({
            'trigger_channel_id': testChannel.id
        })

        postData = {'trigger_id': expectedTrigger.id}
        res = self.client.post(reverse("recipes:new_step2"),
                               data=postData,
                               follow=True)

        self.assertEqual(
            expectedTrigger.id,
            self.client.session['recipe_draft']['trigger_id']
        )
        self.assertRedirect("recipes:new_step3", res)

    def test_step2__post_trigger_without_inputs(self):

        testChannel = Channel.objects.get(name="Dropbox")

        expectedTrigger = Trigger.objects.get(channel=testChannel,
                                              trigger_type=100)

        self.set_recipe_draft({
            'trigger_channel_id': testChannel.id
        })

        postData = {'trigger_id': expectedTrigger.id}
        res = self.client.post(reverse("recipes:new_step2"),
                               data=postData,
                               follow=True)

        self.assertEqual(
            expectedTrigger.id,
            self.client.session['recipe_draft']['trigger_id']
        )
        self.assertRedirect("recipes:new_step4", res)

    def test_step2__post_trigger_for_wrong_channel(self):

        testChannel = Channel.objects.get(name="Dropbox")

        wrongChannel = Channel.objects.get(name="Instagram")
        wrongTrigger = Trigger.objects.get(channel=wrongChannel,
                                           trigger_type=101)

        self.set_recipe_draft({
            'trigger_channel_id': testChannel.id
        })

        postData = {'trigger_id': wrongTrigger.id}
        res = self.client.post(reverse("recipes:new_step2"),
                               data=postData,
                               follow=True)

        self.assertRedirect("recipes:new_step2", res)

    def test_step2__post_trigger_non_existent_id(self):

        testChannel = Channel.objects.get(name="Dropbox")

        self.set_recipe_draft({
            'trigger_channel_id': testChannel.id
        })

        postData = {'trigger_id': 99}
        res = self.client.post(reverse("recipes:new_step2"),
                               data=postData,
                               follow=True)

        self.assertRedirect("recipes:new_step2", res)
