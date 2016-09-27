from .models import HueAccount
from core.channel import Channel, NotSupportedAction, NotSupportedTrigger, ChannelStateForUser
from django.contrib.auth.models import User
import requests

import logging
logger = logging.getLogger('channel')

LIGHT = 100

class HueException(Exception):
    pass

class HueChannel(Channel):
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
        user = User.objects.get(pk=userid)
        # initiate action based on the given action type
        if action_type == LIGHT:
            self._turn_light(user=user, payload=inputs)
        else:
            raise NotSupportedAction("This action is not supported by the Hue channel.")

    def _turn_light(self, user, payload):
        """
        data:
            light_id (int): ID of the light to turn on or off
            state (bool): turn on if true, turn off if false

            enhancement:
            group, schedule, dim option
        """
        hue = HueAccount.objects.get(user=user)

        address = 'http://'+ hue.bridge_ip + '/api/' + hue.access_token\
                  + '/lights/' + payload['light_id'] + '/state'
        cmd = '{"on":'+payload['state']+'}'
        res = requests.put(address, cmd)
        error = res.json()[0]['error']
        if error is not None:
            raise HueException('Hue-Error occured!\nAddress:{}\nDescription: {}'\
                               .format(error['address'], error['description']))


    def fill_recipe_mappings(self, trigger_type, userid,
                             payload, conditions, mappings):
        # hue does not deliver any triggers yet
        raise NotSupportedTrigger(
                  "The Hue channel does not offer any triggers currently.")

    def user_is_connected(self, user):

        if HueAccount.objects.filter(user=user).count() > 0:
            return ChannelStateForUser.connected
        else:
            return ChannelStateForUser.initial
