from __future__ import absolute_import
from django.contrib.auth.models import User
from celery.utils.log import get_task_logger
from core.models import Channel, Recipe, RecipeMapping, RecipeCondition
from core.channel import (NotSupportedTrigger, NotSupportedAction,
                          ConditionNotMet)
from core.utils import get_channel_instance
from celery import shared_task


log = get_task_logger('channel')


@shared_task
def handle_trigger(channel_name, trigger_type, user_id, payload):
    """
        Handle incoming triggers via celery.
    """
    log.debug("handle trigger called")
    # retrieve the user object from db
    try:
        triggered_user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        log.error("Triggered user does not exist")
        return

    # retrieve the channel from db
    try:
        channel = Channel.objects.get(name__iexact=channel_name)
    except Channel.DoesNotExist:
        log.error("Triggered channel does not exist")
        return

    # instanciate channel
    triggered_channel_inst = get_channel_instance(channel.name)

    # get the recipes
    recipes = list(Recipe.objects.filter(user=triggered_user,
                                         trigger__channel=channel,
                                         trigger__trigger_type=trigger_type))
    log.debug("recipes found: {}".format(recipes))

    for recipe in recipes:
        # create dict for recipe mapping and fill it.
        inputs = {}
        recipe_mappings = RecipeMapping.objects.filter(recipe=recipe)
        for mapping in recipe_mappings:
            inputs[mapping.action_input.name] = mapping.trigger_output

        # create dictionary for recipe conditions and fill it.
        conditions = {}
        recipe_conditions = RecipeCondition.objects.filter(recipe=recipe)
        for c in recipe_conditions:
            conditions[c.trigger_input.name] = c.value
        # the triggered channel has to fill the mapping dictionary
        try:
            log.debug("Trying to get mappings from trigger channel")
            mappings = triggered_channel_inst.fill_recipe_mappings(
                                                  trigger_type=trigger_type,
                                                  userid=user_id,
                                                  payload=payload,
                                                  conditions=conditions,
                                                  mappings=inputs)
        except NotSupportedTrigger:
            log.debug("NotSupportedTrigger {}".format(trigger_type))
            return
        except ConditionNotMet as e:
            log.debug(e)
            continue
        except Exception as e:
            log.error("Unexpected error in task.handle_trigger "
                      "while trying to get mappings from trigger channel")
            log.error(e)
            return

        # get the action channel
        action_channel = get_channel_instance(recipe.action.channel.name)
        # initiate action

        try:
            log.debug("task: handle action")
            action_channel.handle_action(action_type=recipe.action.action_type,
                                         userid=user_id,
                                         inputs=mappings)
        except NotSupportedAction:
            log.debug("NotSupportedAction {}".format(recipe.action))
            return
        except Exception as e:
            log.error("Unexpected error in task.handle_trigger "
                      "while trying to action. handle_action")
            log.error(e)
            return
