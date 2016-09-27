from django.core.urlresolvers import reverse
from .test_utils import TestDataProvider, RecipeTestCase
from core.models import Recipe


class RecipeEditViewTest(RecipeTestCase):

    def setUp(self):
        TestDataProvider.create_channels()
        TestDataProvider.create_recipe()
        self.user = TestDataProvider.create_user()
        self.client.force_login(self.user)

    def test_get(self):

        recipe_id = Recipe.objects.all()[0].id

        res = self.client.get(reverse("recipes:edit", args=[recipe_id]))
        self.assertTemplate("recipes/recipe_edit.html", res)

    def test_post__correct(self):

        recipe_id = Recipe.objects.all()[0].id
        postData = {
            "synopsis": "dummy synopsis"
        }

        self.client.post(reverse("recipes:edit", args=[recipe_id]),
                         data=postData)

    def test_post__integrity_error(self):

        recipe_id = Recipe.objects.all()[0].id
        postData = {
        }

        self.client.post(reverse("recipes:edit", args=[recipe_id]),
                         data=postData)
