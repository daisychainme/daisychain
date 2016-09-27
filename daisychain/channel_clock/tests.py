from datetime import datetime
from mock import patch
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from core.channel import (ConditionNotMet, ChannelStateForUser,
                          NotSupportedTrigger, NotSupportedAction)
from core.models import Trigger, TriggerInput
from channel_clock.channel import ClockChannel, TriggerType
from channel_clock.models import ClockUserSettings

class ModelTest(TestCase):

    def test___str__(self):
        alice = User.objects.create_user('alice')
        alice_settings = ClockUserSettings(user=alice, utcoffset=120)
        expected = "Clock settings for user alice (id={})".format(alice.id)
        self.assertEqual(expected, str(alice_settings))

# Create your tests here.
class ChannelTest(TestCase):
    fixtures = ['channel_clock/fixtures/initial_data.json']

    def setUp(self):
        self.channel = ClockChannel()

        self.bob = User.objects.create_user('bob')
        ClockUserSettings(user=self.bob, utcoffset=120).save()

        self.mallory = User.objects.create_user('mallory')

        self.wednesday_1530 = datetime(2016, 9, 21, 15, 30)

        trigger = Trigger.objects.filter(channel__name__iexact="Clock")

        self.trigger = {
            "day": trigger.get(trigger_type=TriggerType.every_day.value),
            "hour": trigger.get(trigger_type=TriggerType.every_hour.value),
            "weekday": trigger.get(trigger_type=TriggerType.every_weekday.value),
            "month": trigger.get(trigger_type=TriggerType.every_month.value),
            "year": trigger.get(trigger_type=TriggerType.every_year.value)
        }

    def test_handle_action(self):
        with self.assertRaises(NotSupportedAction):
            self.channel.handle_action(42, 13, {})

    def test_fill_recipe_mappings__invalid_trigger(self):
        with self.assertRaises(NotSupportedTrigger):
            self.channel.fill_recipe_mappings(-99, self.bob.id, {}, {}, {})

    def test_fill_recipe_mappings__trigger_every_hour__not_met(self):
        conditions = {'Minutes': '45'}
        self._assert_condition_not_met(TriggerType.every_hour, conditions)

    def test_fill_recipe_mappings__trigger_every_hour__met(self):
        conditions = {'Minutes': '30'}
        self._assert_success(TriggerType.every_hour, conditions)

    def test_fill_recipe_mappings__trigger_every_day_not_met(self):
        conditions = {'Time': '14:30'}
        self._assert_condition_not_met(TriggerType.every_day, conditions)

    def test_fill_recipe_mappings__trigger_every_day_met(self):
        conditions = {'Time': '15:30'}
        self._assert_success(TriggerType.every_day, conditions)

    def test_fill_recipe_mappings__trigger_every_weekday_not_met(self):
        conditions = {'Time': '15:30', 'Weekdays': '1,3,5'}
        self._assert_condition_not_met(TriggerType.every_weekday, conditions)

    def test_fill_recipe_mappings__trigger_every_weekday_met(self):
        conditions = {'Time': '15:30', 'Weekdays': '1,2'}
        self._assert_success(TriggerType.every_weekday, conditions)

    def test_fill_recipe_mappings__trigger_every_month_not_met(self):
        conditions = {'Time': '15:30', 'Day': '13'}
        self._assert_condition_not_met(TriggerType.every_month, conditions)

    def test_fill_recipe_mappings__trigger_every_month_met(self):
        conditions = {'Time': '15:30', 'Day': '21'}
        self._assert_success(TriggerType.every_month, conditions)

    def test_fill_recipe_mappings__trigger_every_year_not_met(self):
        conditions = {'Time': '15:30', 'Date': '2016-09-01'}
        self._assert_condition_not_met(TriggerType.every_year, conditions)

    def test_fill_recipe_mappings__trigger_every_year_met(self):
        conditions = {'Time': '15:30', 'Date': '09-21'}
        self._assert_success(TriggerType.every_year, conditions)

    @patch("channel_clock.channel.mockable_now")
    def _assert_condition_not_met(self, trigger_type, conditions, mock_now):

        mock_now.return_value = self.wednesday_1530

        with self.assertRaises(ConditionNotMet):
            self.channel.fill_recipe_mappings(
                    trigger_type, self.bob.id, {}, conditions, {})

    @patch("channel_clock.channel.mockable_now")
    def _assert_success(self, trigger_type, conditions, mock_now):

        mock_now.return_value = self.wednesday_1530

        mappings = {"time": "%time%", "date": "%date%"}
        mappings_expected = {"time": "15:30:00", "date": "09/21/16"}
        mappings_filled = self.channel.fill_recipe_mappings(
                    trigger_type, self.bob.id, {}, conditions, mappings)
        self.assertEqual(mappings_expected, mappings_filled)

    def test_user_is_connected__initial(self):
        state = self.channel.user_is_connected(self.mallory)
        self.assertEqual(ChannelStateForUser.initial, state)

    def test_user_is_connected__connected(self):
        state = self.channel.user_is_connected(self.bob)
        self.assertEqual(ChannelStateForUser.connected, state)

    def test_trigger_synopsis__not_supported_trigger(self):
        with self.assertRaises(NotSupportedTrigger):
            self.channel.trigger_synopsis(-99, {})

    def test_trigger_synopsis__every_hour(self):
        condition = TriggerInput.objects.get(trigger=self.trigger["hour"])
        conditions = [{"id": condition.id, "value": "45"}]
        expected = "it is 45 minutes after the full hour"
        actual = self.channel.trigger_synopsis(self.trigger["hour"].id,
                                               conditions)
        self.assertEqual(expected, actual)

    def test_trigger_synopsis__every_day(self):
        condition = TriggerInput.objects.get(trigger=self.trigger["day"])
        conditions = [{"id": condition.id, "value": "15:45"}]
        expected = "it is 15:45 on any day"
        actual = self.channel.trigger_synopsis(self.trigger["day"].id,
                                               conditions)
        self.assertEqual(expected, actual)

    def test_trigger_synopsis__every_weekday(self):
        conditions = TriggerInput.objects.filter(trigger=self.trigger["weekday"])
        condition0 = conditions.get(name="Time")
        condition1 = conditions.get(name="Weekdays")
        conditions = [
            {"id": condition0.id, "value": "15:45"},
            {"id": condition1.id, "value": "0,1,5"}
        ]
        expected = "it is 15:45 on Monday, Tuesday or Saturday"
        actual = self.channel.trigger_synopsis(self.trigger["weekday"].id,
                                               conditions)
        self.assertEqual(expected, actual)

    def test_trigger_synopsis__every_month(self):
        conditions = TriggerInput.objects.filter(trigger=self.trigger["month"])
        condition0 = conditions.get(name="Time")
        condition1 = conditions.get(name="Day")
        conditions = [
            {"id": condition0.id, "value": "15:45"},
            {"id": condition1.id, "value": "25"}
        ]
        expected = "it is 15:45 on the 25th of the month"
        actual = self.channel.trigger_synopsis(self.trigger["month"].id,
                                               conditions)
        self.assertEqual(expected, actual)

    def test_trigger_synopsis__every_year(self):
        conditions = TriggerInput.objects.filter(trigger=self.trigger["year"])
        condition0 = conditions.get(name="Time")
        condition1 = conditions.get(name="Date")
        conditions = [
            {"id": condition0.id, "value": "15:45"},
            {"id": condition1.id, "value": "09/21/16"}
        ]
        expected = "it is 15:45 on 09/21/16"
        actual = self.channel.trigger_synopsis(self.trigger["year"].id,
                                               conditions)
        self.assertEqual(expected, actual)


class SetupViewTest(TestCase):

    def setUp(self):

        self.url = reverse("clock:connect")

        max_muster = User.objects.create_user("max_muster")
        self.client.force_login(max_muster)

    def test_get(self):

        getData = {
            "next": "/test-redirect-uri/"
        }
        res = self.client.get(self.url, getData)
        res = self.client.get(self.url)

    def test_post__error(self):

        postData = { "offset": 418230471203841723042 }
        res = self.client.post(self.url, postData)

    def test_post__success(self):

        postData = { "offset": 42 }
        res = self.client.post(self.url, postData)


class ResetViewTest(TestCase):

    def setUp(self):

        self.url = reverse("clock:disconnect")

        self.bob = User.objects.create_user('bob')
        ClockUserSettings(user=self.bob, utcoffset=120).save()

        self.mallory = User.objects.create_user('mallory')

    def test_get__valid_user(self):

        self.client.force_login(self.bob)
        res = self.client.get(self.url)

    def test_get__invalid_user(self):

        self.client.force_login(self.mallory)
        res = self.client.get(self.url)
