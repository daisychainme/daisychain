from django.core.urlresolvers import NoReverseMatch
from mock import MagicMock, patch
from recipes.views import RecipeCreateBaseView
from .test_utils import TestDataProvider, RecipeTestCase


class RecipeCreateBaseViewTest(RecipeTestCase):

    def setUp(self):
        TestDataProvider.create_channels()
        TestDataProvider.create_recipe()
        self.user = TestDataProvider.create_user()

    def test__get_hook_url__hook_finished(self):

        view = RecipeCreateBaseView()

        hook_url = view._get_hook_url({"hook42_done": True}, "", "hook42")

        self.assertIsNone(hook_url)

    def test__get_hook_url__invalid_channel_type(self):

        view = RecipeCreateBaseView()

        # won't find a "channeltype_channel_id"
        with self.assertRaises(KeyError):
            hook_url = view._get_hook_url({}, "channeltype", "")

    @patch("recipes.views.reverse")
    @patch("core.models.Channel.objects.get")
    def test__get_hook_url__no_hook(self, mock_channel_get, mock_reverse):

        view = RecipeCreateBaseView()
        draft = {"trigger_channel_id": 42}
        channel_type = "trigger"
        hook_name = "the_hook"

        mock_channel_get.return_value = MagicMock()
        mock_channel_get.return_value.name = "Channel"
        mock_reverse.side_effect = NoReverseMatch()

        hook_url = view._get_hook_url(draft, channel_type, hook_name)

        mock_channel_get.assert_called_with(id=42)
        mock_reverse.assert_called_with("channel:the_hook")
        self.assertTrue(draft['the_hook_done'])
        self.assertIsNone(hook_url)

    @patch("recipes.views.reverse")
    @patch("core.models.Channel.objects.get")
    def test__get_hook_url__hook(self, mock_channel_get, mock_reverse):

        view = RecipeCreateBaseView()
        draft = {"trigger_channel_id": 42}
        channel_type = "trigger"
        hook_name = "the_hook"

        mock_channel_get.return_value = MagicMock()
        mock_channel_get.return_value.name = "Channel"
        mock_reverse.return_value = "returned_hook_url"

        hook_url = view._get_hook_url(draft, channel_type, hook_name)

        mock_channel_get.assert_called_with(id=42)
        mock_reverse.assert_called_with("channel:the_hook")
        self.assertFalse(draft['the_hook_done'])
        self.assertEqual(hook_url, "returned_hook_url")
