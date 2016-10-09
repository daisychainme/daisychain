import logging

from core.channel import (Channel, NotSupportedTrigger, NotSupportedAction,
                          ConditionNotMet, ChannelStateForUser)
from core.utils import replace_text_mappings
from core.models import (RecipeCondition, Recipe, TriggerInput)
from core.core import Core
from channel_rss.config import (TRIGGER_TYPE, CHANNEL_NAME, TO_REPLACE)
from channel_rss.utils import (entries_since, filter_entries_by_keyword,
                               build_string_from_entry_list)


class RssChannel(Channel):

    def handle_action(self, action_type, userid, inputs):
        """
        The RSS channel does not support any actions at the moment.

        Raises:
            NotSupportedAction
        """
        raise NotSupportedAction("The RSS channel does not support actions.")

    def fill_recipe_mappings(self, trigger_type, userid,
                             payload, conditions, mappings):
        if payload['feed_url'] != conditions['feed_url']:
            raise ConditionNotMet('Feed urls do not match.')
        # check for trigger type and replace mappings accordingly
        if trigger_type == TRIGGER_TYPE['new_entries']:
            to_replace = ['summaries', 'summaries_and_links']
            return replace_text_mappings(mappings=mappings,
                                         to_replace=to_replace,
                                         payload=payload)
        else:
            raise NotSupportedTrigger('trigger_type {} not supported'.format(
                trigger_type))

    def user_is_connected(self, user):
        """
        Always returns unnecessary.
        """
        return ChannelStateForUser.unnecessary

    def fetch_entries_by_keyword(self, feed, since):
        """

        Args:
            feed:
            since:

        Returns:

        """

        '''
        get all recipe conditions of a recipe that have the feed url as a
        recipe condition and that correspond to the trigger input keyword.
        These recipe conditions are the keywords that condition if a
        certain recipe is triggered and executed.
        '''
        trigger_type = TRIGGER_TYPE['entries_keyword']
        url_input = TriggerInput.objects.get(trigger__channel__name='RSS',
                                             trigger__trigger_type=trigger_type,
                                             name='feed_url')
        keyword_input = TriggerInput.objects.get(
                trigger__channel__name='RSS',
                trigger__trigger_type=trigger_type,
                name='keyword')
        # get all conditions of the feeds url
        url_conditions = RecipeCondition.objects.filter(value=feed.url,
                                                        trigger_input=url_input)
        # fetch rss feed
        entries = entries_since(feed.url, since)

        for condition in url_conditions:
            # for each condition get the keyword via the corresponding recipe
            keyword_cond = RecipeCondition.objects.get(
                    recipe=condition.recipe,
                    trigger_input=keyword_input)
            keyword = keyword_cond.value
            # check for occurence / get the entries
            filtered_entries = filter_entries_by_keyword(entries,
                                                         keyword)
            # build strings, fill payoad
            summaries = build_string_from_entry_list(filtered_entries,
                                                     'summary')
            summaries_and_links = build_string_from_entry_list(filtered_entries,
                                                               'summary',
                                                               'link')
            payload = {
                'summaries_and_links': summaries_and_links,
                'summaries': summaries,
                'keyword': keyword,
                'feed_url': feed.url
            }

            Core().handle_trigger(channel_name=CHANNEL_NAME,
                                  trigger_type=TRIGGER_TYPE['entries_keyword'],
                                  userid=condition.recipe.user,
                                  payload=payload)








