from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpRequest
from mock import MagicMock, patch
from unittest import skip
from channel_clock.views import (TriggerInputView, RequiredInputMissing,
                                 InputInvalid, TriggerInputView)
from core.models import Channel, Trigger, TriggerInput
from recipes.tests.test_utils import RecipeTestCase


class BaseViewTestCase(RecipeTestCase):
    fixtures = ['channel_clock/fixtures/initial_data.json']

    def setUp(self):

        self.url = reverse("recipes:new_step3")
        self.channel = Channel.objects.get(name="Clock")

        self.max_muster = User.objects.create_user("max_muster")
        self.client.force_login(self.max_muster)

    def assertMessage(self, response, message):
        for msg in response.context['messages']:
            if message == str(msg):
                return

        raise AssertionError("Message not found: '{}'".format(message))


class TriggerInputViewTest(BaseViewTestCase):

    @patch("channel_clock.views.redirect")
    @patch("django.contrib.messages.error")
    def test_dispatch__trigger_does_not_exist(self, mock_error, mock_redirect):

        request = "test_request_not_used"
        draft = { 'trigger_id': -99 }

        TriggerInputView().dispatch(request, draft)

        mock_error.assert_called_once_with(
                request,
                "The selected trigger does not exist")

        mock_redirect.assert_called_once_with("recipes:new_step2")


    def test_dispatch__valid_trigger_types(self):

        for trigger_type in range(1,6):
            trigger = Trigger.objects.get(channel=self.channel,
                                          trigger_type=trigger_type)

            self.set_recipe_draft({
                'trigger_channel_id': self.channel.id,
                'trigger_id': trigger.id
            })

            self.client.get(self.url)
            self.client.post(self.url)

    def test__save_and_redirect(self):

        draft = {}
        # every year trigger
        trigger = Trigger.objects.get(channel=self.channel, trigger_type=5)
        inputs = { "Time": "15:30", "Date": "10-04" }

        draft_expected = { 'recipe_conditions': [] }

        trigger_input1 = TriggerInput.objects.get(trigger=trigger, name="Date")
        trigger_input2 = TriggerInput.objects.get(trigger=trigger, name="Time")
        draft_expected['recipe_conditions'] = [{
            'id': trigger_input1.id,
            'value': "10-04"
        }, {
            'id': trigger_input2.id,
            'value': "15:30"
        }]

        TriggerInputView()._save_and_redirect(None, draft, trigger, inputs)

        condition_sorter = lambda x: x['id']
        draft['recipe_conditions'].sort(key=condition_sorter)
        draft_expected['recipe_conditions'].sort(key=condition_sorter)

        self.assertEqual(draft, draft_expected)

    @patch("django.contrib.messages.error")
    def test__validate_input__missing_required(self, mock_error):

        request = MagicMock()
        request.POST = MagicMock()
        request.POST.getlist = MagicMock(return_value=[])
        message_expected = "Please select a test_key value"

        with self.assertRaises(RequiredInputMissing):
            TriggerInputView()._validate_input(request, 'test_key', None)

        request.POST.getlist.assert_called_once_with('test_key')
        mock_error.assert_called_once_with(request, message_expected)

    @patch("django.contrib.messages.error")
    def test__validate_input__missing_required_custom_msg(self, mock_error):

        request = MagicMock()
        request.POST = MagicMock()
        request.POST.getlist = MagicMock(return_value=[])
        message = "test_message"

        with self.assertRaises(RequiredInputMissing):
            TriggerInputView()._validate_input(request, 'test_key', None,
                                               message_required=message)

        request.POST.getlist.assert_called_once_with('test_key')
        mock_error.assert_called_once_with(request, message)

    @patch("django.contrib.messages.error")
    def test__validate_input__missing_not_required(self, mock_error):

        request = MagicMock()
        request.POST = MagicMock()
        request.POST.getlist = MagicMock(return_value=[])

        result = TriggerInputView()._validate_input(request, 'test_key', None,
                                                    required=False)

        self.assertIsNone(result)
        request.POST.getlist.assert_called_once_with('test_key')
        mock_error.assert_not_called()

    def test__validate_input__return_single_value(self):

        request = MagicMock()
        request.POST = MagicMock()
        request.POST.getlist = MagicMock(return_value=['post_val_1'])

        condition = MagicMock(return_value=True)

        result = TriggerInputView()._validate_input(request, 'test_key',
                                                    condition)

        self.assertEqual(result, 'post_val_1')
        request.POST.getlist.assert_called_once_with('test_key')

    def test__validate_input__return_list(self):

        result_expected = ["value_1", "value_2", "value_3"]

        request = MagicMock()
        request.POST = MagicMock()
        request.POST.getlist = MagicMock(return_value=result_expected)

        condition = MagicMock(return_value=True)

        result = TriggerInputView()._validate_input(request, 'test_key',
                                                    condition)

        self.assertEqual(result, result_expected)
        request.POST.getlist.assert_called_once_with('test_key')

    @patch("django.contrib.messages.error")
    def test__validate_input__condition_false(self, mock_error):

        result_expected = ["value_1"]

        request = MagicMock()
        request.POST = MagicMock()
        request.POST.getlist = MagicMock(return_value=result_expected)
        message_expected = ("Invalid selection. Please stay within the defined"
                            " test_key values")

        condition = MagicMock(return_value=False)

        with self.assertRaises(InputInvalid):
            TriggerInputView()._validate_input(request, 'test_key',
                                               condition)

        request.POST.getlist.assert_called_once_with('test_key')
        mock_error.assert_called_once_with(request, message_expected)

class EveryDayTriggerInputViewTest(BaseViewTestCase):

    def test_post__valid_values(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=1)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "13",
            "minute": "30"
        }

        res = self.client.post(self.url, data=data)
        self.assertRedirect('recipes:new_step4', res)

    def test_post__invalid_hour(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=1)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "24",
            "minute": "30"
        }

        res = self.client.post(self.url, data=data)

        self.assertMessage(res, ('Invalid selection. Please stay within the '
                                 'defined hour values'))

    def test_post__invalid_minute(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=1)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "13",
            "minute": "60"
        }

        res = self.client.post(self.url, data=data)

        self.assertMessage(res, ('Invalid selection. Please stay within the '
                                 'defined minute values'))

class EveryHourTriggerInputViewTest(BaseViewTestCase):

    def test_post__valid_minute(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=2)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = { "minute": "30" }

        res = self.client.post(self.url, data=data)
        self.assertRedirect("recipes:new_step4", res)

    def test_post__invalid_minute(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=2)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = { "minute": "60" }

        res = self.client.post(self.url, data=data)

        self.assertMessage(res, ('Invalid selection. Please stay within the '
                                 'defined minute values'))

class EveryWeekdayTriggerInputViewTest(BaseViewTestCase):

    def test_post__valid_data(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=3)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "15",
            "minute": "30",
            "weekday": ("1", "3", "5")
        }

        res = self.client.post(self.url, data=data)
        self.assertRedirect("recipes:new_step4", res)

    def test_post__invalid_hour(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=3)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "25",
            "minute": "30",
            "weekday": ("1", "3", "5")
        }

        res = self.client.post(self.url, data=data)

        self.assertMessage(res, ('Invalid selection. Please stay within the '
                                 'defined hour values'))

    def test_post__invalid_minute(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=3)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "15",
            "minute": "60",
            "weekday": ("1", "3", "5")
        }

        res = self.client.post(self.url, data=data)

        self.assertMessage(res, ('Invalid selection. Please stay within the '
                                 'defined minute values'))

    def test_post__invalid_weekday(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=3)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "15",
            "minute": "30",
            "weekday": "9"
        }

        res = self.client.post(self.url, data=data)

        self.assertMessage(res, ('Invalid selection. Please stay within the '
                                 'defined weekday values'))

class EveryMonthTriggerInputViewTest(BaseViewTestCase):

    def test_post__valid_data(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=4)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "15",
            "minute": "30",
            "day": "20"
        }

        res = self.client.post(self.url, data=data)
        self.assertRedirect("recipes:new_step4", res)

    def test_post__invalid_hour(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=4)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "25",
            "minute": "30",
            "day": "28"
        }

        res = self.client.post(self.url, data=data)

        self.assertMessage(res, ('Invalid selection. Please stay within the '
                                 'defined hour values'))

    def test_post__invalid_minute(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=4)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "15",
            "minute": "60",
            "day": "28"
        }

        res = self.client.post(self.url, data=data)

        self.assertMessage(res, ('Invalid selection. Please stay within the '
                                 'defined minute values'))

    def test_post__invalid_day(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=4)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "15",
            "minute": "30",
            "day": "29"
        }

        res = self.client.post(self.url, data=data)

        self.assertMessage(res, ('Invalid selection. Please stay within the '
                                 'defined day values'))


class EveryYearTriggerInputViewTest(BaseViewTestCase):

    def test_post__valid_data(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=5)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "15",
            "minute": "30",
            "day": "28",
            "month": "7"
        }

        res = self.client.post(self.url, data=data)
        self.assertRedirect("recipes:new_step4", res)

    def test_post__invalid_hour(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=5)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "25",
            "minute": "30",
            "day": "28",
            "month": "7"
        }

        res = self.client.post(self.url, data=data)
        self.assertMessage(res, ('Invalid selection. Please stay within the '
                                 'defined hour values'))

    def test_post__invalid_minute(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=5)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "15",
            "minute": "60",
            "day": "28",
            "month": "7"
        }

        res = self.client.post(self.url, data=data)
        self.assertMessage(res, ('Invalid selection. Please stay within the '
                                 'defined minute values'))

    def test_post__invalid_day(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=5)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "15",
            "minute": "30",
            "day": "32",
            "month": "7"
        }

        res = self.client.post(self.url, data=data)
        self.assertMessage(res, ('Invalid selection. Please stay within the '
                                 'defined day values'))

    def test_post__invalid_month(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=5)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "15",
            "minute": "30",
            "day": "28",
            "month": "13"
        }

        res = self.client.post(self.url, data=data)
        self.assertMessage(res, ('Invalid selection. Please stay within the '
                                 'defined month values'))

    def test_post__leapday(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=5)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "15",
            "minute": "30",
            "day": "29",
            "month": "2"
        }

        res = self.client.post(self.url, data=data)
        self.assertMessage(res, ('You selected the leap day. Please confirm '
                                 'your choice.'))

    def test_post__invalid_day_month_combination(self):

        trigger = Trigger.objects.get(channel=self.channel, trigger_type=5)

        self.set_recipe_draft({
            'trigger_channel_id': self.channel.id,
            'trigger_id': trigger.id
        })
        data = {
            "hour": "15",
            "minute": "30",
            "day": "31",
            "month": "4"
        }

        res = self.client.post(self.url, data=data)
        self.assertMessage(res, 'Invalid selection. This date does not exist')
