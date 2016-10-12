import feedparser
from django.contrib.auth.models import User
from celery.utils.log import get_task_logger
from celery import shared_task

from core.models import RecipeCondition
from core.core import Core
from datetime import datetime
from channel_rss.models import RssFeed
from channel_rss.utils import (unique_feed_urls, get_latest_update,
                               build_string_from_feed)
from channel_rss.config import CHANNEL_NAME
from channel_rss.channel import RssChannel

log = get_task_logger(__name__)


@shared_task()
def fetch_rss_feeds():
    """
    Fetch RSS feeds periodically and fire trigger if changes are detected.
    """
    log.debug('fetch rss feeds!')
    uniques = unique_feed_urls()
    # create RssFeed object for every unique feed if it does not exist yet.
    for feed_url in uniques:
        try:
            RssFeed.objects.get(feed_url=feed_url)
        except RssFeed.DoesNotExist:
            RssFeed(feed_url=feed_url).save()

    # if a known rss feed has been updated fire triggers.
    for feed in RssFeed.objects.all():
        parsed_feed = feedparser.parse(feed.feed_url)
        # check if feed is available via http status code
        if parsed_feed.status != 200:
            continue

        latest_update_struct = get_latest_update(parsed_feed)
        latest_update = datetime(*latest_update_struct[:6])

        # if the last modified date is not known the feed object has to be
        # instantiated first. No trigger is fired in this case.
        if not feed.last_modified:
            feed.last_modified = latest_update
            feed.save()
            continue

        # feed has modification date; update it,
        # save time of previous update as time_struct for later use.
        previous_update = feed.last_modified.timetuple()
        # check if feed has been updated.
        if previous_update >= latest_update_struct:
            # there are no new entries. Do not fire any trigger.
            continue

        print("NEW ENTRIES")
        feed.last_modified = latest_update
        feed.save()

        # parse feeds and fire triggers if necessary.
        rss_channel = RssChannel()
        rss_channel.fetch_entries_by_keyword(feed, previous_update)

        # build output strings, build payload.
        summaries_links = build_string_from_feed(feed.feed_url,
                                                 'summary',
                                                 'link',
                                                 since=previous_update)
        summaries = build_string_from_feed(feed.feed_url,
                                           'summary',
                                           since=previous_update)
        # payload consisting of trigger outputs and feed url
        # feed url is used in RssChannel.fill_recipe_mappings
        payload = {
            'summaries_and_links': summaries_links,
            'summaries': summaries,
            'feed_url': feed.feed_url,
        }

        # get recipe conditions, corresponding user, and trigger_types
        # then pass the data to the core and let it handle the trigger
        conditions = RecipeCondition.objects.filter(value=feed.feed_url)
        for condition in conditions:
            user_id = condition.recipe.user.id
            trigger_type = condition.recipe.trigger.trigger_type
            Core().handle_trigger(channel_name=CHANNEL_NAME,
                                  trigger_type=trigger_type,
                                  userid=user_id,
                                  payload=payload)
