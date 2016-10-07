from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _
from django.views.generic import View
from urllib.parse import urlsplit, parse_qs, urlencode, urlunsplit
from channel_clock.channel import (ClockChannel, weekday_name, month_name,
                                   TriggerType)
from channel_clock.models import ClockUserSettings
from channel_clock.timezones import timezones
from core.channel import ChannelStateForUser
from core.models import Trigger, TriggerInput
from recipes.util import Draft

DEFAULT_OAUTH_NEXT_URI = "/"
SESSKEY_OAUTH_NEXT_URI = "clock_oauth_next_uri"

HOURS = range(0, 24)
MINUTES = range(0, 60)
WEEKDAYS = [weekday_name(i) for i in range(0,7)]
DAYS = range(1, 29)
ALLDAYS = range(1, 32)
MONTHS = [month_name(i) for i in range(1, 13)]


class SetupView(LoginRequiredMixin, View):

    def fetch_next_uri(self, request):

        if SESSKEY_OAUTH_NEXT_URI in request.session:
            return

        # get ?next= parameter and store it in session, default to root
        q_next = request.GET.get('next', DEFAULT_OAUTH_NEXT_URI)
        request.session[SESSKEY_OAUTH_NEXT_URI] = q_next

    def get_next_uri(self, request):
        try:
            return request.session[SESSKEY_OAUTH_NEXT_URI]
        except KeyError:
            return DEFAULT_OAUTH_NEXT_URI

    def append_query_params(self, url, **kwargs):

        uri = urlsplit(url)
        query = parse_qs(uri.query)

        for key in kwargs:
            if key in query:
                query[key].append(kwargs[key])
            else:
                query[key] = kwargs[key]

        query_string = urlencode(query, doseq=True)

        uri_new = uri._replace(query=query_string)

        return urlunsplit(uri_new)

    def clear_session(self, request):

        try:
            del request.session[SESSKEY_OAUTH_NEXT_URI]
        except KeyError:
            pass

    def error(self, request, **kwargs):

        url = self.append_query_params(self.get_next_uri(request),
                                       status='error',
                                       **kwargs)

        self.clear_session(request)

        return redirect(url)

    def success(self, request, **kwargs):

        url = self.append_query_params(self.get_next_uri(request),
                                       status="success",
                                       **kwargs)

        self.clear_session(request)

        return redirect(url)

    def get(self, request):

        self.fetch_next_uri(request)

        user_state = ClockChannel().user_is_connected(request.user)
        if user_state is ChannelStateForUser.connected:
            return self.success(request)

        context = {'timezones': timezones}

        return render(request, 'channel_clock/setup.html', context=context)

    def post(self, request):

        offset = request.POST.get("offset", 0)

        try:
            ClockUserSettings(user=request.user, utcoffset=offset).save()
        except:
            return self.error(request, type="django.db")
        else:
            return self.success(request)


class ResetView(LoginRequiredMixin, View):

    def get(self, request):

        redirect_url = request.GET.get('next', '/')

        try:
            ClockUserSettings.objects.get(user=request.user).delete()
        except:
            return redirect(redirect_url + "?status=error")
        else:
            return redirect(redirect_url + "?status=success")


class ValidationException(Exception):
    pass


class RequiredInputMissing(ValidationException):
    pass


class InputInvalid(ValidationException):
    pass


class TriggerInputView(LoginRequiredMixin, View):
    template = 'channel_clock/trigger_input_view.html'
    inputs = []
    context = {
        'values': {},
        'hours': HOURS, 'minutes': MINUTES, 'weekdays': WEEKDAYS,
        'days': DAYS, 'alldays': ALLDAYS, 'months': MONTHS
    }

    def dispatch(self, request, draft):
        try:
            trigger = Trigger.objects.get(id=draft['trigger_id'])
        except Trigger.DoesNotExist:
            messages.error(request,
                           _("The selected trigger does not exist"))
            return redirect("recipes:new_step2")

        trigger_type = TriggerType(trigger.trigger_type)

        if trigger_type is TriggerType.every_hour:
            view = EveryHourTriggerInputView()
        elif trigger_type is TriggerType.every_day:
            view = EveryDayTriggerInputView()
        elif trigger_type is TriggerType.every_weekday:
            view = EveryWeekdayTriggerInputView()
        elif trigger_type is TriggerType.every_month:
            view = EveryMonthTriggerInputView()
        else: #if trigger_type is TriggerType.every_year
            view = EveryYearTriggerInputView()

        if request.method == "POST":
            return view.post(request, draft, trigger)
        else:
            return view.get(request)

    def get(self, request):
        return self._render(request)

    def _save_and_redirect(self, request, draft, trigger, inputs):

        trigger_inputs = TriggerInput.objects.filter(trigger=trigger)
        conditions = []
        for key in inputs:
            conditions.append({
                'id': trigger_inputs.get(name=key).id,
                'value': inputs[key]
            })

        draft["recipe_conditions"] = conditions
        return redirect("recipes:new_step4")

    def _validate_input(self, request, key, condition, message_invalid=None,
                        required=True, message_required=None):

        valuelist = request.POST.getlist(key)

        if len(valuelist) is 0:
            if required:
                if message_required is None:
                    message_required = _(
                            "Please select a {} value".format(key))
                messages.error(request, message_required)
                raise RequiredInputMissing()
            else:
                return None

        for value in valuelist:
            if not condition(value):
                if message_invalid is None:
                    message_str = ("Invalid selection. Please stay within "
                                   "the defined {} values").format(key)
                    message_invalid = _(message_str)
                messages.error(request, message_invalid)
                raise InputInvalid()

        if len(valuelist) is 1:
            return valuelist[0]
        else:
            return valuelist

    def _render(self, request):
        self.context["inputs"] = self.inputs
        return render(request, self.template, context=self.context)

class EveryHourTriggerInputView(TriggerInputView):
    inputs = ["minute"]

    def post(self, request, draft, trigger):

        try:
            minute = self._validate_input(request,
                                          'minute',
                                          lambda x: int(x) in MINUTES)
        except ValidationException:
            return self._render(request)
        else:
            return self._save_and_redirect(request,
                                           draft,
                                           trigger,
                                           { "Minutes": minute })


class EveryDayTriggerInputView(TriggerInputView):
    inputs = ["hour", "minute"]

    def post(self, request, draft, trigger):

        try:
            hour = self._validate_input(request,
                                        'hour',
                                        lambda x: int(x) in HOURS)
            minute = self._validate_input(request,
                                          'minute',
                                          lambda x: int(x) in MINUTES)
        except ValidationException:
            return self._render(request)
        else:
            inputs = { "Time": "{}:{}".format(hour, minute) }
            return self._save_and_redirect(request, draft, trigger, inputs)


class EveryWeekdayTriggerInputView(TriggerInputView):
    inputs = ["hour", "minute", "weekday"]

    def post(self, request, draft, trigger):

        try:
            hour = self._validate_input(request,
                                        'hour',
                                        lambda x: int(x) in HOURS)
            minute = self._validate_input(request,
                                          'minute',
                                          lambda x: int(x) in MINUTES)
            message_required = _("Please select at least one weekday")
            weekdays = self._validate_input(request,
                                            'weekday',
                                            lambda x: 0 <= int(x) <= 6,
                                            message_required=message_required)
        except ValidationException:
            return self._render(request)
        else:
            inputs = {
                "Time": "{}:{}".format(int(hour), minute),
                "Weekdays": ",".join(weekdays)
            }
            return self._save_and_redirect(request, draft, trigger, inputs)


class EveryMonthTriggerInputView(TriggerInputView):
    inputs = ["hour", "minute", "day"]

    def post(self, request, draft, trigger):

        try:
            hour = self._validate_input(request,
                                        'hour',
                                        lambda x: int(x) in HOURS)
            minute = self._validate_input(request,
                                          'minute',
                                          lambda x: int(x) in MINUTES)
            day = self._validate_input(request,
                                       'day',
                                       lambda x: int(x) in DAYS)
        except ValidationException:
            return self._render(request)
        else:
            inputs = { "Time": "{}:{}".format(int(hour), minute),
                       "Day": int(day) }
            return self._save_and_redirect(request, draft, trigger, inputs)

class EveryYearTriggerInputView(TriggerInputView):
    inputs = ["hour", "minute", "day", "month"]

    def post(self, request, draft, trigger):

        try:
            hour = self._validate_input(request,
                                        'hour',
                                        lambda x: int(x) in HOURS)
            minute = self._validate_input(request,
                                          'minute',
                                          lambda x: int(x) in MINUTES)
            day = self._validate_input(request,
                                       'day',
                                       lambda x: int(x) in ALLDAYS)
            month = self._validate_input(request,
                                         'month',
                                         lambda x: 1 <= int(x) <= 12)
            leapyear = self._validate_input(request,
                                            'leapyear',
                                            lambda x: True,
                                            required=False)
        except ValidationException:
            return self._render(request)
        else:

            if month == "2" and day == "29" and leapyear != "confirmed":
                self.inputs.append("leapyear")
                self.context["values"] = {
                    "day": int(day),
                    "month": int(month),
                    "hour": int(hour),
                    "minute": minute
                }
                messages.warning(request,
                                 "You selected the leap day. Please "
                                 "confirm your choice.")
                return self._render(request)

            elif ((month == "2" and int(day) > 29) or
                  (month in ['4', '6', '9', '11'] and int(day) > 30)):
                messages.warning(request,
                                 "Invalid selection. This date does not exist")
                self.context["values"] = {
                    "day": int(day),
                    "month": int(month),
                    "hour": int(hour),
                    "minute": minute
                }
                return self._render(request)

            inputs = {
                "Time": "{}:{}".format(int(hour), minute),
                "Date": "{}-{}".format(int(month), int(day))
            }
            return self._save_and_redirect(request, draft, trigger, inputs)
