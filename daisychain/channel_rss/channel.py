import logging

from core.channel import (Channel, NotSupportedTrigger, NotSupportedAction,
                          ConditionNotMet, ChannelStateForUser)
from core.utils import replace_text_mappings
from channel_rss.config import TRIGGER_TYPE


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
