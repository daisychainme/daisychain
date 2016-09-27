from django.core.urlresolvers import reverse
from core.models import Recipe
from .test_utils import TestDataProvider, RecipeTestCase


class RecipeDeleteViewTest(RecipeTestCase):

    def setUp(self):
        TestDataProvider.create_channels()
        TestDataProvider.create_recipe()
        self.user = TestDataProvider.create_user()
        self.client.force_login(self.user)

    def test_get(self):

        testRecipe = Recipe.objects.first()
        res = self.client.get(reverse("recipes:delete", args=(testRecipe.id,)))
        self.assertTemplate("recipes/recipe_delete.html", res)
        self.assertEqual(testRecipe, res.context['recipe'])

    def test_post__keep(self):

        recipeCountBefore = Recipe.objects.all().count()
        testRecipe = Recipe.objects.first()

        postData = {"action": "keep"}
        res = self.client.post(reverse("recipes:delete",
                               args=(testRecipe.id,)),
                               data=postData,
                               follow=True)

        recipeCountAfter = Recipe.objects.all().count()
        self.assertEqual(recipeCountBefore, recipeCountAfter)

        allRecipes = Recipe.objects.all()
        self.assertIn(testRecipe, allRecipes)

    def test_post__delete(self):

        recipeCountBefore = Recipe.objects.all().count()
        testRecipe = Recipe.objects.first()

        postData = {"action": "delete"}
        res = self.client.post(reverse("recipes:delete",
                               args=(testRecipe.id,)),
                               data=postData,
                               follow=True)

        expectedCount = recipeCountBefore - 1
        recipeCountAfter = Recipe.objects.all().count()
        self.assertEqual(expectedCount, recipeCountAfter)

        allRecipes = Recipe.objects.all()
        self.assertNotIn(testRecipe, allRecipes)
