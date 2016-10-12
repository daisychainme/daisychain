from django.test import TestCase
from django.contrib.auth.models import User

from mock import patch, mock
from datetime import datetime, timedelta

from channel_rss.tasks import fetch_rss_feeds
from channel_rss.models import RssFeed
from channel_rss.config import CHANNEL_NAME
from channel_rss.tests.test_base import BaseTest


class TaskTest(BaseTest):

    def setUp(self):
        super().setUp()

    class MockFeedParserDict:
        def __init__(self, entries, status):
            self.entries = entries
            self.status = status

    @patch('feedparser.parse')
    @patch('core.core.Core.handle_trigger')
    @patch('channel_rss.channel.RssChannel.fetch_entries_by_keyword')
    def test_with_one_feed_known_one_unknown(self,
                                             mock_fetch_keyword,
                                             mock_handle_trigger,
                                             mock_parse):
        # one feed is already known
        last_update = datetime.now()
        RssFeed(feed_url=self.feeds[1], last_modified=last_update).save()
        # the other is not
        with self.assertRaises(RssFeed.DoesNotExist):
            RssFeed.objects.get(feed_url=self.feeds[0])
        self.assertIsNotNone(RssFeed.objects.get(feed_url=self.feeds[1]))

        new_update = (last_update + timedelta(1, 1)).timetuple()
        entries = [{'updated_parsed': new_update, 'summary': 'TEST_SUMMARY',
                    'link': 'TEST_LINK'}]
        fd = self.MockFeedParserDict(entries, 200)

        mock_parse.return_value = fd

        with patch('config.celery.CELERY_ALWAYS_EAGER', True, create=True):
            fetch_rss_feeds.apply().get()

        expected_payload = {
            'summaries': 'TEST_SUMMARY\n\n',
            'summaries_and_links': 'TEST_SUMMARY\nTEST_LINK\n\n',
            'feed_url': self.feeds[1]
        }
        # assertions
        mock_handle_trigger.assert_called_once_with(channel_name=CHANNEL_NAME,
                                                    userid=self.user.id,
                                                    trigger_type=200,
                                                    payload=expected_payload)
        self.assertIsNotNone(RssFeed.objects.get(feed_url=self.feeds[0]))
        self.assertIsNotNone(RssFeed.objects.get(feed_url=self.feeds[1]))

    @patch('feedparser.parse')
    @patch('channel_rss.utils.build_string_from_feed')
    @patch('channel_rss.utils.get_latest_update')
    @patch('core.core.Core.handle_trigger')
    def test_fetch_rss_feeds_feed_unavailable(self,
                                              mock_handle_trigger,
                                              mock_get_latest_update,
                                              mock_build_string_from_entries,
                                              mock_parse):
        mock_parse.return_value = self.MockFeedParserDict([], 404)
        fetch_rss_feeds.apply().get()
        mock_get_latest_update.assert_not_called()
        mock_build_string_from_entries.assert_not_called()
        mock_handle_trigger.assert_not_called()

    @patch('feedparser.parse')
    @patch('channel_rss.utils.build_string_from_feed')
    @patch('channel_rss.utils.get_latest_update')
    @patch('core.core.Core.handle_trigger')
    def test_fetch_rss_feed_no_new_entries(self,
                                           mock_handle_trigger,
                                           mock_get_latest_update,
                                           mock_build_string_from_entries,
                                           mock_parse):
        # one feed is already known
        last_update = datetime.now()
        RssFeed(feed_url=self.feeds[1], last_modified=last_update).save()
        # the other is not
        with self.assertRaises(RssFeed.DoesNotExist):
            RssFeed.objects.get(feed_url=self.feeds[0])
        self.assertIsNotNone(RssFeed.objects.get(feed_url=self.feeds[1]))
        # no new feeds. Edge case: last_modified == updated_parsed
        new_update = last_update.timetuple()
        entries = [{'updated_parsed': new_update, 'summary': 'TEST_SUMMARY',
                    'link': 'TEST_LINK'}]
        fd = self.MockFeedParserDict(entries, 200)

        mock_parse.return_value = fd
        fetch_rss_feeds.apply().get()
        # no trigger should be fired
        mock_get_latest_update.assert_not_called()
        mock_build_string_from_entries.assert_not_called()
        mock_handle_trigger.assert_not_called()
