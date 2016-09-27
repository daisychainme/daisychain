from django.core.urlresolvers import reverse
from .test_utils import TestDataProvider, RecipeTestCase


class RecipeCreateResetViewTest(RecipeTestCase):

    def setUp(self):
        TestDataProvider.create_channels()
        self.user = TestDataProvider.create_user()
        self.client.force_login(self.user)

    def test_reset(self):

        self.client.session['recipe_draft'] = "a draft object that should \
                be deleted on the following GET request"

        res = self.client.get(reverse("recipes:new"), follow=True)

        # assert that the client has been redirected correctly
        self.assertRedirect("recipes:new_step1", res)

        # recipe_draft should be removed from session
        if 'recipe_draft' in self.client.session:
            self.assertEqual({}, self.client.session['recipe_draft'])
