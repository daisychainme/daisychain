from datetime import datetime, timedelta, timezone
from enum import Enum
from django.contrib.humanize.templatetags.humanize import ordinal
from core.channel import (Channel, NotSupportedTrigger, NotSupportedAction,
                          ConditionNotMet, ChannelStateForUser)
from core.models import Trigger, TriggerInput
from core.utils import replace_text_mappings
from channel_clock.models import ClockUserSettings
from locale import (nl_langinfo,
                    DAY_1, DAY_2, DAY_3, DAY_4, DAY_5, DAY_6, DAY_7,
                    MON_1, MON_2, MON_3, MON_4, MON_5, MON_6,
                    MON_7, MON_8, MON_9, MON_10, MON_11, MON_12)


def mockable_now(tz=None):
    return datetime.now(tz=tz)


def weekday_name(weekday):

    weekday = int(weekday)

    if weekday == 0:
        return nl_langinfo(DAY_2)
    elif weekday == 1:
        return nl_langinfo(DAY_3)
    elif weekday == 2:
        return nl_langinfo(DAY_4)
    elif weekday == 3:
        return nl_langinfo(DAY_5)
    elif weekday == 4:
        return nl_langinfo(DAY_6)
    elif weekday == 5:
        return nl_langinfo(DAY_7)
    else: #if weekday == 6:
        return nl_langinfo(DAY_1)

def month_name(month):

    month = int(month)

    if month == 1:
        return nl_langinfo(MON_1)
    elif month == 2:
        return nl_langinfo(MON_2)
    elif month == 3:
        return nl_langinfo(MON_3)
    elif month == 4:
        return nl_langinfo(MON_4)
    elif month == 5:
        return nl_langinfo(MON_5)
    elif month == 6:
        return nl_langinfo(MON_6)
    elif month == 7:
        return nl_langinfo(MON_7)
    elif month == 8:
        return nl_langinfo(MON_8)
    elif month == 9:
        return nl_langinfo(MON_9)
    elif month == 10:
        return nl_langinfo(MON_10)
    elif month == 11:
        return nl_langinfo(MON_11)
    else: #if month == 12:
        return nl_langinfo(MON_12)


class TriggerType(Enum):
    every_day = 1
    every_hour = 2
    every_weekday = 3
    every_month = 4
    every_year = 5


class ClockChannel(Channel):

    @staticmethod
    def handle_action(action_type, userid, inputs):
        """The Clock channel does not support any actions

        Always Raises:
            NotSupportedAction
        """
        raise NotSupportedAction("The Clock channel does not support actions.")

    def fill_recipe_mappings(self, trigger_type, userid,
                             payload, conditions, mappings):

        offset = ClockUserSettings.objects.get(user__pk=userid).utcoffset
        user_timezone = timezone(timedelta(minutes=offset))
        current_datetime = mockable_now(tz=user_timezone)

        # check if trigger is valid
        try:
            trigger_type = TriggerType(trigger_type)
        except ValueError:
            raise NotSupportedTrigger

        # 0-7 => 0; 8-22 => 15; 23-37 => 30; 38-52 => 45; 53-59 => 0
        minutes = current_datetime.minute
        time_for_condition = "{}:{}".format(current_datetime.hour,
                                            str(minutes).rjust(2, '0'))

        # check for "Minutes" condition of TriggerType.every_hour
        if trigger_type is TriggerType.every_hour:
            if int(conditions["Minutes"]) != minutes:
                raise ConditionNotMet("minutes not met")

        # check for "Time" condition of all other TriggerTypes
        else:
            if conditions["Time"] != time_for_condition:
                raise ConditionNotMet("time not met")

            # no further check for TriggerType.every_day, but recognize it
            if trigger_type is TriggerType.every_day:
                pass

            # check for "Weekdays" condition of TriggerType.every_weekday
            elif trigger_type is TriggerType.every_weekday:
                weekday_list = conditions["Weekdays"].split(",")
                if str(current_datetime.weekday()) not in weekday_list:
                    raise ConditionNotMet("weekday not met")

            # check for "Day" condition of TriggerType.every_month
            elif trigger_type is TriggerType.every_month:
                if conditions["Day"] != str(current_datetime.day):
                    raise ConditionNotMet("day not met")

            # check for "Date" condition of TriggerType.every_year
            else: # if trigger_type is TriggerType.every_year
                if conditions["Date"] != current_datetime.strftime("%m-%d"):
                    raise ConditionNotMet("date not met")

        # Format TriggerOutput values
        current_date = current_datetime.strftime("%x")
        current_time = current_datetime.strftime("%X")

        # fill mappings (equal for all Triggers)
        mappings_filled = {}

        for key in mappings:
            val = mappings[key]
            if type(val) is str:
                if val.find("%date%") > -1:
                    val = val.replace("%date%", current_date)
                if val.find("%time%") > -1:
                    val = val.replace("%time%", current_time)
            mappings_filled[key] = val

        return mappings_filled

    def user_is_connected(self, user):
        if ClockUserSettings.objects.filter(user=user).count() > 0:
            return ChannelStateForUser.connected
        else:
            return ChannelStateForUser.initial

    def trigger_synopsis(self, trigger_id, conditions):
        """Create the If-part of the recipe synopsis"""

        # check if trigger is valid
        try:
            trigger = Trigger.objects.get(id=trigger_id)
            trigger_type = TriggerType(trigger.trigger_type)
        except (Trigger.DoesNotExist, ValueError):
            raise NotSupportedTrigger

        # get trigger condition(s)
        translated_conditions = {}
        for condition in conditions:
            trigger_input = TriggerInput.objects.get(id=condition["id"])
            translated_conditions[trigger_input.name] = condition["value"]

        conditions = translated_conditions

        # TriggerType.every_hour
        if trigger_type is TriggerType.every_hour:
            return "it is {} minutes after the full hour".format(
                    conditions["Minutes"])

        # all other TriggerTypes
        else:
            time = conditions["Time"]

            # TriggerType.every_day
            if trigger_type is TriggerType.every_day:
                return "it is {} on any day".format(time)

            # TriggerType.every_weekday
            elif trigger_type is TriggerType.every_weekday:
                wdays = [int(x) for x in conditions["Weekdays"].split(",")]
                weekdays = [weekday_name(i) for i in wdays]

                weekday_string = weekdays[-1]

                if len(weekdays) > 1:
                    weekday_string = "".join([
                            ", ".join(weekdays[:-1]),
                            " or ",
                            weekday_string])

                return "it is {} on {}".format(time, weekday_string)

            # TriggerType.every_month
            elif trigger_type is TriggerType.every_month:
                return "it is {} on the {} of the month".format(
                        time, ordinal(conditions["Day"]))

            # TriggerType.every_year
            else: #if trigger_type is TriggerType.every_year
                return "it is {} on {}".format(time, conditions["Date"])

