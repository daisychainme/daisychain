from django.test import TestCase
from mock import patch

from core.channel import (NotSupportedAction, NotSupportedTrigger,
                          ChannelStateForUser, ConditionNotMet)
from channel_rss.channel import RssChannel
from channel_rss.config import TRIGGER_TYPE


class ChannelTest(TestCase):

    def setUp(self):
        self.channel = RssChannel()

    def test_handle_action_raises_not_supported_action(self):
        with self.assertRaises(NotSupportedAction):
            self.channel.handle_action(100, 42, {})

    @patch('core.utils.replace_text_mappings')
    def test_fill_recipe_mappings_with_valid_trigger_type(self,
                                                          mock_replace_text_mappings):
        conditions = {'feed_url': 'test.com/rss'}
        mappings = {'text_action_input': 'new entries: %summaries_and_links%'}
        payload = {
            'summaries_and_links': 'TEST_SUMMARIES_AND_LINKS',
            'summaries': 'TEST_SUMMARIES',
            'feed_url': 'test.com/rss',
        }
        trigger_type = TRIGGER_TYPE['new_entries']

        ret = self.channel.fill_recipe_mappings(trigger_type=trigger_type,
                                                userid=1,
                                                conditions=conditions,
                                                mappings=mappings,
                                                payload=payload)
        # assert that the replacement in mappings was successful.
        exp = {'text_action_input': 'new entries: TEST_SUMMARIES_AND_LINKS'}
        self.assertEquals(exp, ret)

    def test_fill_recipe_mappings_invalid_trigger_type(self):
        conditions = {'feed_url': 'test.com/rss'}
        mappings = {'text_action_input': 'new entries: %summaries_and_links%'}
        payload = {
            'summaries_and_links': 'TEST_SUMMARIES_AND_LINKS',
            'summaries': 'TEST_SUMMARIES',
            'feed_url': 'test.com/rss',
        }
        with self.assertRaises(NotSupportedTrigger):
            self.channel.fill_recipe_mappings(trigger_type=-42,
                                              userid=9000,
                                              conditions=conditions,
                                              mappings=mappings,
                                              payload=payload)

    def test_fill_mappings_feed_urls_do_not_match(self):
        conditions = {'feed_url': 'test.com/rss'}
        mappings = {'text_action_input': 'new entries: %summaries_and_links%'}
        payload = {
            'summaries_and_links': 'TEST_SUMMARIES_AND_LINKS',
            'summaries': 'TEST_SUMMARIES',
            'feed_url': 'foobar.com/rss',
        }
        with self.assertRaises(ConditionNotMet):
            self.channel.fill_recipe_mappings(trigger_type=-42,
                                              userid=9000,
                                              conditions=conditions,
                                              mappings=mappings,
                                              payload=payload)


    def test_is_connected(self):
        self.assertEquals(self.channel.user_is_connected(None),
                          ChannelStateForUser.unnecessary)
