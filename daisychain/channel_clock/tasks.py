from datetime import datetime, timedelta, timezone
from celery import shared_task
from core.core import Core
from core.models import Recipe

@shared_task
def beat():

    clock_recipes = Recipe.objects.filter(trigger__channel__name="Clock")

    triggered_combinations = set()

    for recipe in clock_recipes:

        trigger_user_pair = (recipe.trigger.trigger_type, recipe.user.id)

        if trigger_user_pair in triggered_combinations:
            continue

        Core().handle_trigger(channel_name="Clock",
                              trigger_type=recipe.trigger.trigger_type,
                              userid=recipe.user.id,
                              payload=None)

        triggered_combinations.add(trigger_user_pair)
