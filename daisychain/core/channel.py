from abc import ABC, abstractmethod
from enum import Enum
from core.models import Trigger, Action


class NotSupportedAction(Exception):
    """the requested action is not supported by this channel"""
    pass


class NotSupportedTrigger(Exception):
    """The requested trigger is not supported by this channel"""
    pass


class ConditionNotMet(Exception):
    """The recipe should not be executed because of the recipe condition"""
    pass


class ChannelStateForUser(Enum):
    """If the user can use the channel or not"""
    unnecessary = 0
    initial = 1
    connected = 2
    expired = 3


class Channel(ABC):

    @abstractmethod
    def fill_recipe_mappings(self, trigger_type, userid,
                             payload, conditions, mappings):
        """Replace all placeholders in the mappings dictionary and return
        the modified mappings.

        This method is called by worker threads when they process a trigger
        that was queued by the Channel via core.handle_trigger() and is needed
        to get the data from the trigger that shall be handed over to the
        action

        Args:
            trigger_type (int): as defined in the model field
                Trigger.trigger_type
            userid (int): the user to whom the trigger belongs
            payload (dict): the payload that was passed by the channel when
                queueing this trigger
            conditions (dict): the conditions that have to be satisfied. For
                each recipe condition there is a key equal to the "name"
                attribute of the corresponding TriggerInput
            mappings (dict): the values that shall be passed from trigger to
                action. The keys in this dictionary may be ignored since they
                are only relevant to the action channel. The values contain
                placeholders in string.format() format, i.e. ``{<key>}`` with
                <key> being known by the trigger channel.

        Returns:
            dict: the ``mappings`` dictionary with replaced placeholders

        Raises:
            NotSupportedTrigger: If a trigger of trigger_type is not supported.
            NotSupportedAction: If an action of action_type is not supported.
            ConditionNotMet: If the Conditions of the Recipe are not met,
                i.e. no action should be taken.

        """
        pass

    @abstractmethod
    def handle_action(self, action_type, userid, inputs):
        """Execute the action specified in action_type using userid and inputs.

        This method is called by worker threads when they process a trigger
        and any action of this channel is requested.

        Args:
            action_type (int): as defined in model Action.action_type
            userid (int): the user to whom the action belongs
            inputs (dict): the values that have been filled in another
                channel's get_trigger_inputs() and shall be used in this
                action

        Returns:
            void
        """
        pass

    @abstractmethod
    def user_is_connected(self, user):
        """Is the user connected to this channel?

        This method can be used to determine if an user is able to use this
        channel (returns True) or not (returns False)

        Args:
            user (obj): an instance of django.contrib.auth.models.User

        Returns:
            Enum value of ChannelStateForUser
        """
        pass

    def trigger_synopsis(self, trigger_id, conditions):
        """Create the If-part of the recipe synopsis"""

        trigger = Trigger.objects.get(id=trigger_id)

        return "{} on {}".format(trigger.name, trigger.channel.name)

    def action_synopsis(self, action_id, inputs):
        """Create the Then-part of the recipe synopsis"""

        action = Action.objects.get(id=action_id)

        return "{} on {}".format(action.name, action.channel.name)
