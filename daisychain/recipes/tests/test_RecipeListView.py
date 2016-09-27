from django.core.urlresolvers import reverse
from core.models import Recipe
from .test_utils import TestDataProvider, RecipeTestCase


class RecipeListViewTest(RecipeTestCase):

    def setUp(self):
        TestDataProvider.create_channels()
        TestDataProvider.create_recipe()
        self.user = TestDataProvider.create_user()

    def test_get(self):

        self.client.force_login(self.user)

        expectedContext = {"recipe_list": []}

        for recipe in Recipe.objects.filter(user=self.user):
            expectedContext["recipe_list"].append(recipe)

        res = self.client.get(reverse("recipes:list"))

        self.assertListEqual(expectedContext['recipe_list'],
                             list(res.context['recipe_list']))

        self.assertTemplate("recipes/recipe_list.html", res)
