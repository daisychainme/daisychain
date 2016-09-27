from django.core.urlresolvers import reverse
from .test_utils import TestDataProvider, RecipeTestCase
from core.models import (Trigger, Action)


class RecipeCreateSaveViewTest(RecipeTestCase):

    def setUp(self):
        TestDataProvider.create_channels()
        self.user = TestDataProvider.create_user()
        self.client.force_login(self.user)

    def test_step7__post(self):

        sessionTrigger = Trigger.objects.get(channel__name="Instagram",
                                             trigger_type=100)

        testAction = Action.objects.get(channel__name="Twitter",
                                        action_type=101)

        self.set_recipe_draft({
            'trigger_id': sessionTrigger.id,
            'action_id': testAction.id,
            'recipe_mappings': [],
            'recipe_conditions': []
        })

        postData = {
            'synopsis': "Arbitrary text"
        }

        res = self.client.post(reverse("recipes:new_step7"),
                               data=postData,
                               follow=True)

        self.assertRedirect("recipes:list", res)
