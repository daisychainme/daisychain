from mock import patch
from django.contrib.auth.models import User
from django.test import TransactionTestCase
from core.models import Channel, Trigger, Action, Recipe
from channel_clock.tasks import beat


class TasksTest(TransactionTestCase):
    fixtures = ['channel_clock/fixtures/initial_data.json']

    @patch("core.core.Core.handle_trigger")
    def test_beat(self, mock_handle_trigger):

        maxmuster = User.objects.create_user('max')
        channel = Channel.objects.get(name="Clock")
        trigger = Trigger.objects.filter(channel=channel)[0]
        action = Action.objects.create(channel=channel,
                                       action_type=2,
                                       name="Test Action")

        Recipe.objects.create(trigger=trigger,
                              action=action,
                              user=maxmuster,
                              synopsis="Test synopsis")

        beat()

        mock_handle_trigger.assert_called_once_with(
                channel_name=channel.name,
                trigger_type=trigger.trigger_type,
                userid=maxmuster.id,
                payload=None)
