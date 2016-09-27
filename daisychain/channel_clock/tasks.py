from datetime import datetime, timedelta, timezone
from celery import shared_task
from core.models import Recipe

@shared_task
def beat():

    clock_recipes = Recipe.objects.filter(trigger__channel__name="Clock")

    for recipe in clock_recipes:

        Core().handle_trigger(channel_name="Clock",
                              trigger_type=recipe.trigger.trigger_type,
                              userid=recipe.user.id,
                              payload=None)
