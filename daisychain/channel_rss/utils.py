import feedparser

from core.models import RecipeCondition


def feed_updated(feed, last_updated):
    """
    Checks whether an rss feed has been updated since the last known
    modification.

    Args:
        feed: The url to the RSS feed or the newly fetched and parsed feed
            represented by a FeedParser object.
        last_updated: Last known update. Given as time_struct.

    Returns:
        True if the feed has been updated, false otherwise.
    """
    return get_latest_update(feed) > last_updated


def get_latest_update(feed):
    """
    Retrieves the date of the last update from an RSS feed.

    Args:
        feed: URL to the feed or FeedParser representing the parsed feed.

    Returns:
        The date of last update as a struct_time.
    """
    feed = _parse_feed_if_necessary(feed)
    update_dates = (e.get('updated_parsed') for e in feed.entries)
    return max(tuple(e for e in update_dates if e is not None))


def entries_since(feed, date):
    """
    Retrieves all entries of an RSS feed since a given date.

    Args:
        feed: URL to the feed or FeedParser representing the parsed feed.
        date: Date as time_struct.

    Returns:
        List of entries since the given date.
    """
    feed = _parse_feed_if_necessary(feed)
    entries = [e for e in feed.entries if e['updated_parsed'] is not None]
    return [e for e in entries if e['updated_parsed'] > date]


def build_string_from_entries(feed, *args, since=None):
    """
    Retrieves fields for every entry in the feed.

    Args:
        feed: URL to the feed or FeedParser representing the parsed feed.
        since: time_struct specifying the oldest date for which a feed entry
            should be considered. (optional)
        *args: Names of the fields to retrieve.

    Returns:
        All specified fields for every entry.
    """
    feed = _parse_feed_if_necessary(feed)
    if since:
        entries = entries_since(feed, since)
    else:
        entries = [e for e in feed.entries]
    result_string = ""
    for entry in entries:
        for field in args:
            result_string = "{}{}\n".format(result_string, entry[field])
        result_string = "{}\n".format(result_string)
    return result_string


def fetch_feed_if_updated(url, date):
    """
    Fetches an RSS feed if has been updated since a given date.

    Args:
        url: URL to the RSS feed
        date: Date as time_struct.

    Returns:
        FeedParser object representing the feed if the feed has been
        updated, None otherwise.
    """
    feed = feedparser.parse(url)
    if feed_updated(feed, date):
        return feed
    else:
        return None


def unique_feed_urls():
    """
    get unique feed urls that are saved as RecipeConditions.

    Returns:
        set of feed urls.
    """
    recipe_conditions = RecipeCondition.objects.filter(
        trigger_input__trigger__channel__name='RSS')
    return set(e.value for e in recipe_conditions)


def _parse_feed_if_necessary(feed):
    if type(feed) is str:
        feed = feedparser.parse(feed)
    return feed