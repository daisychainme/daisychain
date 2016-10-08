from django.core.urlresolvers import reverse
from channel_dropbox.models import DropboxAccount
from core.models import Channel
from .test_utils import TestDataProvider, RecipeTestCase


class RecipeCreateTriggerChannelSelectionViewTest(RecipeTestCase):

    def setUp(self):
        TestDataProvider.create_channels()
        self.user = TestDataProvider.create_user()
        self.client.force_login(self.user)

    def test_step1_get(self):

        expectedChannels = [
            Channel.objects.get(name="Dropbox"),
            Channel.objects.get(name="Instagram")
        ]

        res = self.client.get(reverse("recipes:new_step1"))

        self.assertListEqual(expectedChannels, res.context['trigger_channels'])

        self.assertTemplate("recipes/recipe_create.step1.html", res)

    def test_step1__successful_redirect_from_authentication(self):

        res = self.client.get(reverse("recipes:new_step1") + "?status=success")

        self.assertEqual(302, res.status_code)
        self.assertEqual(res["Location"], reverse("recipes:new_step2"))

    def test_step1__failed_redirect_from_authentication(self):

        testChannel = Channel.objects.get(name="Dropbox")

        self.set_recipe_draft({
            'trigger_channel_id': testChannel.id
        })

        res = self.client.get(reverse("recipes:new_step1") + "?status=error")

    def test_step1__post_valid_channelid(self):

        expectedChannel = Channel.objects.get(name="Dropbox")

        DropboxAccount.objects.create(user=self.user)

        postData = {'trigger_channel_id': expectedChannel.id}
        res = self.client.post(reverse("recipes:new_step1"),
                               data=postData)

        self.assertEqual(
            expectedChannel.id,
            self.client.session['recipe_draft']['trigger_channel_id']
        )
        self.assertEqual(302, res.status_code)
        self.assertTrue(
                res["Location"].startswith(reverse("recipes:new_step2")))

    def test_step1__post_channelid_without_triggers(self):

        expectedChannel = Channel.objects.get(name="Twitter")

        postData = {'trigger_channel_id': expectedChannel.id}
        res = self.client.post(reverse("recipes:new_step1"),
                               data=postData,
                               follow=True)

        self.assertRedirect("recipes:new_step1", res)

    def test_step1__post_invalid_channelid(self):

        postData = {'trigger_channel_id': 99}   # hopefully non existent id
        res = self.client.post(reverse("recipes:new_step1"),
                               data=postData,
                               follow=True)

        self.assertRedirect("recipes:new_step1", res)
