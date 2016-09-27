from django.contrib.auth.models import User
from django.test import TransactionTestCase
from django.core.urlresolvers import reverse
from django.db.utils import IntegrityError
from core.models import (Channel, Trigger, TriggerInput, TriggerOutput,
                         Action, ActionInput, Recipe, RecipeCondition,
                         RecipeMapping)


class TestDataProvider():

    def create_dropbox_channel():
        try:
            c = Channel(name="Dropbox",
                        image="/static/channels/dropbox.png",
                        color="#007ee5",
                        font_color="#ffffff")
            c.save()
        except IntegrityError:
            return

        t = Trigger(channel=c,
                    trigger_type=100,
                    name="New Photo on Dropbox")
        t.save()
        TriggerOutput(trigger=t, name="file", mime_type="image").save()
        TriggerOutput(trigger=t, name="publicUrl", mime_type="text").save()

        t = Trigger(channel=c,
                    trigger_type=101,
                    name="New Video on Dropbox in specific folder")
        t.save()
        TriggerInput(trigger=t, name="Folder").save()
        TriggerOutput(trigger=t, name="file", mime_type="video").save()
        TriggerOutput(trigger=t, name="publicUrl", mime_type="text").save()

        a = Action(channel=c, action_type=500, name="Save Photo to Dropbox")
        a.save()
        ActionInput(action=a, name="Folder", mime_type="text").save()
        ActionInput(action=a, name="Photo", mime_type="photo").save()

        a = Action(channel=c, action_type=501, name="Save Video to Dropbox")
        a.save()
        ActionInput(action=a, name="Folder", mime_type="text").save()
        ActionInput(action=a, name="Video", mime_type="video").save()

    def create_instagram_channel():
        try:
            c = Channel(name="Instagram",
                        image="/static/channels/instagram.png",
                        color="#ffffff",
                        font_color="#000000")
            c.save()
        except IntegrityError:
            return

        t = Trigger(channel=c,
                    trigger_type=100,
                    name="New Photo on Instagram")
        t.save()
        TriggerOutput(trigger=t, name="caption", mime_type="text").save()
        TriggerOutput(trigger=t,
                      name="image_standard",
                      mime_type="image").save()
        TriggerOutput(trigger=t, name="image_low", mime_type="image").save()
        TriggerOutput(trigger=t, name="thumbnail", mime_type="image").save()

        t = Trigger(channel=c,
                    trigger_type=101,
                    name="New Photo on Instagram with specific hashtag")
        t.save()
        TriggerInput(trigger=t, name="Hashtag").save()
        TriggerOutput(trigger=t, name="caption", mime_type="text").save()
        TriggerOutput(trigger=t,
                      name="image_standard",
                      mime_type="image").save()
        TriggerOutput(trigger=t, name="image_low", mime_type="image").save()
        TriggerOutput(trigger=t, name="thumbnail", mime_type="image").save()

    def create_twitter_channel():

        try:
            c = Channel(name="Twitter",
                        image="/static/channels/twitter.png",
                        color="#55acee",
                        font_color="#ffffff")
            c.save()
        except IntegrityError:
            return

        a = Action(channel=c,
                   action_type=100,
                   name="Post new status on Twitter")
        a.save()
        ActionInput(action=a, name="Status", mime_type="text").save()

        a = Action(channel=c,
                   action_type=101,
                   name="Post new photo on Twitter")
        a.save()
        ActionInput(action=a, name="Status", mime_type="text").save()
        ActionInput(action=a, name="Photo", mime_type="image").save()

        Action(channel=c, action_type=404, name="I dont have inputs").save()

    def create_channels():
        TestDataProvider.create_dropbox_channel()
        TestDataProvider.create_instagram_channel()
        TestDataProvider.create_twitter_channel()

    def create_recipe():
        TestDataProvider.create_channels()
        user = TestDataProvider.create_user()

        tc = Channel.objects.get(name="Instagram")
        t = Trigger.objects.get(channel=tc, trigger_type=101)

        ac = Channel.objects.get(name="Twitter")
        a = Action.objects.get(channel=ac, action_type=101)

        r = Recipe(trigger=t, action=a, user=user)
        r.save()

        ti = TriggerInput.objects.get(trigger=t, name="Hashtag")

        rc = RecipeCondition(recipe=r, trigger_input=ti, value="foodstagram")
        rc.save()

        ai_1 = ActionInput.objects.get(action=a, name="Status")
        RecipeMapping(recipe=r,
                      action_input=ai_1,
                      trigger_output="%caption%").save()

        ai_2 = ActionInput.objects.get(action=a, name="Photo")
        RecipeMapping(recipe=r,
                      action_input=ai_2,
                      trigger_output="%caption%").save()

    def create_user():
        try:
            return User.objects.create_user("testuser", password="testtest")
        except IntegrityError:
            return User.objects.get(username="testuser")


class RecipeTestCase(TransactionTestCase):

    def assertTemplate(self, expected, response):
        templateFound = False
        for template in response.templates:
            if template.name == expected:
                templateFound = True
                break
        self.assertTrue(templateFound)

    def set_recipe_draft(self, draft):
        session = self.client.session
        session['recipe_draft'] = draft
        session.save()

    def assertRedirect(self, target, response):
        self.assertRedirects(response, reverse(target))
