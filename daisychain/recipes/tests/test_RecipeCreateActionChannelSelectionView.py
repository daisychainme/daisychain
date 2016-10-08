from django.core.urlresolvers import reverse
from channel_dropbox.models import DropboxAccount
from core.models import (Channel, Trigger, Action)
from .test_utils import TestDataProvider, RecipeTestCase


class RecipeCreateActionChannelSelectionViewTest(RecipeTestCase):

    def setUp(self):
        TestDataProvider.create_channels()
        self.user = TestDataProvider.create_user()
        self.client.force_login(self.user)

    def test_step4_get(self):

        expectedChannels = [
            Channel.objects.get(name="Dropbox"),
            Channel.objects.get(name="Twitter")
        ]

        sessionTrigger = Trigger.objects.get(channel__name="Instagram",
                                             trigger_type=100)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id
        })

        res = self.client.get(reverse("recipes:new_step4"))

        self.assertListEqual(expectedChannels, res.context['action_channels'])

        self.assertTemplate("recipes/recipe_create.step4.html", res)

    def test_step4__post_valid_channelid(self):

        expectedChannel = Channel.objects.get(name="Dropbox")

        DropboxAccount.objects.create(user=self.user)

        sessionTrigger = Trigger.objects.get(channel__name="Instagram",
                                             trigger_type=100)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id
        })

        postData = {'action_channel_id': expectedChannel.id}
        res = self.client.post(reverse("recipes:new_step4"),
                               data=postData)

        self.assertEqual(302, res.status_code)
        self.assertTrue(
                res["Location"].startswith(reverse("recipes:new_step5")))

        self.assertEqual(
            expectedChannel.id,
            self.client.session['recipe_draft']['action_channel_id']
        )

    def test_step4__post_channelid_without_actions(self):

        expectedChannel = Channel.objects.get(name="Instagram")

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id
        })

        postData = {'action_channel_id': expectedChannel.id}
        res = self.client.post(reverse("recipes:new_step4"),
                               data=postData,
                               follow=True)

        self.assertRedirect("recipes:new_step4", res)

    def test_step4__post_invalid_channelid(self):

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id
        })
        postData = {'trigger_channel_id': 99}   # hopefully non existent id
        res = self.client.post(reverse("recipes:new_step4"),
                               data=postData,
                               follow=True)

        self.assertRedirect("recipes:new_step4", res)

    def test_step4__post_invalid_session_no_trigger(self):

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
        })
        postData = {'trigger_channel_id': 99}
        res = self.client.post(reverse("recipes:new_step4"),
                               data=postData,
                               follow=True)

        self.assertRedirect("recipes:new_step2", res)

    def test_step4__get_invalid_session_invalid_trigger(self):

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': 99
        })
        res = self.client.get(reverse("recipes:new_step4"),
                              follow=True)

        self.assertRedirect("recipes:new_step2", res)

    def test_step4__get_auth_redirect_success(self):

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        sessionAction = Action.objects.get(channel__name="Twitter",
                                           action_type=100)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id,
            'action_channel_id': sessionAction.channel.id
        })
        getData = {
            "status": "success"
        }
        res = self.client.get(reverse("recipes:new_step4"),
                              data=getData,
                              follow=True)

        self.assertRedirect("recipes:new_step5", res)

    def test_step4__get_auth_redirect_error(self):

        expectedChannel = Channel.objects.get(name="Twitter")

        sessionTrigger = Trigger.objects.get(channel__name="Dropbox",
                                             trigger_type=100)

        self.set_recipe_draft({
            'trigger_channel_id': sessionTrigger.channel.id,
            'trigger_id': sessionTrigger.id,
            'action_channel_id': expectedChannel.id
        })
        getData = {
            "status": "error"
        }
        res = self.client.get(reverse("recipes:new_step4"),
                              data=getData)
