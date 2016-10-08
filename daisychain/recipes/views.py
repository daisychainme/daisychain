from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.urlresolvers import reverse, NoReverseMatch
from django.db import transaction, IntegrityError
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _
from django.views.generic import View

import importlib

from .util import Draft
from core.channel import ChannelStateForUser
from core.models import (Channel,
                         Trigger, TriggerInput, TriggerOutput,
                         Action, ActionInput,
                         Recipe, RecipeCondition, RecipeMapping)
from core.utils import get_channel_instance


class RecipeListView(LoginRequiredMixin, View):

    def get(self, request):

        user_recipes = Recipe.objects.filter(user=request.user)

        context = {
            "recipe_list": user_recipes
        }

        return render(request, 'recipes/recipe_list.html', context=context)


class RecipeCreateBaseView(LoginRequiredMixin, View):

    def _get_hook_url(self, draft, channel_type, hook_name):

        draft_field = "{}_done".format(hook_name)

        # hook has already been called
        if draft_field in draft and draft[draft_field]:

            return None

        # hook has not been called or is not finished
        else:

            channel_id = draft["{}_channel_id".format(channel_type)]

            channel = Channel.objects.get(id=channel_id)
            channel_name = channel.name.lower()

            try:
                hook_url = reverse("{}:{}".format(channel_name, hook_name))
            except NoReverseMatch:
                draft[draft_field] = True
                return None

            draft[draft_field] = False
            return hook_url


class RecipeCreateResetView(LoginRequiredMixin, View):

    @Draft.activate
    def dispatch(self, request, draft):
        draft.clear()
        return redirect("recipes:new_step1")


class RecipeCreateTriggerChannelSelectionView(RecipeCreateBaseView):

    @Draft.activate
    def post(self, request, draft):

        # get the channel id from the request
        channel_id = request.POST.get('trigger_channel_id')

        # try to get the channel
        try:
            channel = Channel.objects.get(id=channel_id)

        # redirect to this step (as GET) with error message
        except Channel.DoesNotExist:
            messages.error(request,
                           _("The selected channel does not exist"))
            return redirect("recipes:new_step1")

        # if the selected channel has no triggers redirect to this step
        # (as GET) with error message
        if Trigger.objects.filter(channel=channel).count() == 0:
            messages.error(request,
                           _("The selected channel has no triggers and"
                             "cannot be used as trigger channel"))
            return redirect("recipes:new_step1")

        # set the trigger_channel in the session draft
        draft['trigger_channel_id'] = channel.id

        # check if user is connected and redirect if not
        trigger_channel = get_channel_instance(channel.name)
        user_state = trigger_channel.user_is_connected(request.user)
        if user_state == ChannelStateForUser.connected:
            return redirect("recipes:new_step2")
        else:
            # send user to channel authentication. Should just pass through
            # if the user is already authenticated
            auth_url = reverse("{}:connect".format(channel.name.lower()))
            return redirect(auth_url + "?next=" + reverse("recipes:new_step1"))

    @Draft.activate
    def get(self, request, draft):

        # test for redirect from authentication
        q_status = request.GET.get("status", False)

        if q_status == "success":
            return redirect("recipes:new_step2")
        elif q_status == "error":
            channel_id = draft['trigger_channel_id']
            channel = Channel.objects.get(id=channel_id)
            messages.error(request,
                           _("Authentication at channel %s failed. Please "
                             "select another channel" % channel.name))

        # get all channels
        channels = Channel.objects.all().order_by('name')

        # only add the channels that have at least one trigger
        trigger_channels = []
        for channel in channels:
            if Trigger.objects.filter(channel=channel).count() > 0:
                trigger_channels.append(channel)

        # build context and render template
        context = {
            "trigger_channels": trigger_channels
        }
        return render(request,
                      'recipes/recipe_create.step1.html',
                      context=context)


class RecipeCreateTriggerSelectionView(RecipeCreateBaseView):

    @Draft.activate
    def dispatch(self, request, draft):
        """Selection of trigger"""

        # make sure, previous step was executed
        if 'trigger_channel_id' not in draft:
            return redirect("recipes:new_step1")

        # test if channel is existent, should never go wrong because of
        # other tests
        try:
            channel = Channel.objects.get(id=draft['trigger_channel_id'])
        except Channel.DoesNotExist:
            messages.error(request,
                           _("The selected channel does not exist"))
            return redirect("recipes:new_step1")

        # lower channel name for future use
        channel_name = channel.name.lower()

        # redirect to pre-trigger-selection-hook
        hook_url = self._get_hook_url(draft, 'trigger',
                                      'pre_trigger_selection_hook')
        if hook_url is not None:
            return redirect(hook_url)

        # load module of selected channel and look for custom view
        try:
            module_name = "channel_{}.views".format(channel_name)
            channel_module = importlib.import_module(module_name)

            custom_view = getattr(channel_module, 'TriggerSelectionView')()
            return custom_view.dispatch(request, draft)

        # ImportError => channel- or views-module does not exist
        # AttributeError => There is no custom view defined
        except (ImportError, AttributeError):
            if request.method == "POST":
                return self.post(request, draft, channel)
            else:
                return self.get(request, draft, channel)

    def post(self, request, draft, channel):

        # get the trigger id from the request
        trigger_id = request.POST.get('trigger_id')

        # try to get the trigger
        try:
            trigger = Trigger.objects.get(id=trigger_id, channel=channel)
        # redirect to this step with error message
        except Trigger.DoesNotExist:
            messages.error(request,
                           _("The selected trigger does not exist"))
            return redirect("recipes:new_step2")

        # save trigger to session draft
        draft['trigger_id'] = trigger.id

        # redirect to post-trigger-selection-hook
        hook_url = self._get_hook_url(draft, 'trigger',
                                      'post_trigger_selection_hook')
        if hook_url is not None:
            return redirect(hook_url)

        # if trigger has inputs, send to next step
        if TriggerInput.objects.filter(trigger=trigger).count() > 0:
            return redirect("recipes:new_step3")

        # if not, skip the TriggerInput step and go to step4
        else:
            return redirect("recipes:new_step4")

    def get(self, request, draft, channel):

        # if the selected channel has no triggers redirect to this step
        # (as GET) with error message
        if Trigger.objects.filter(channel=channel).count() == 0:
            messages.error(request,
                           _("The selected channel has no triggers and"
                             "cannot be used as trigger channel"))
            return redirect("recipes:new_step1")

        # build context and render template
        context = {
            "triggers": Trigger.objects.filter(channel=channel).values()
        }
        return render(request,
                      'recipes/recipe_create.step2.html',
                      context=context)


class RecipeCreateTriggerInputView(RecipeCreateBaseView):

    @Draft.activate
    def dispatch(self, request, draft):
        """Optional selection of trigger inputs"""

        # make sure, previous step was executed
        if 'trigger_id' not in draft:
            return redirect("recipes:new_step2")

        # else load the trigger's inputs
        try:
            trigger = Trigger.objects.get(id=draft['trigger_id'])
        except Trigger.DoesNotExist:
            messages.error(request,
                           _("The selected trigger does not exist"))
            return redirect("recipes:new_step2")

        # redirect to pre-trigger-input-hook
        hook_url = self._get_hook_url(draft, 'trigger',
                                      'pre_trigger_input_hook')
        if hook_url is not None:
            return redirect(hook_url)

        trigger_inputs = TriggerInput.objects.filter(trigger=trigger)

        # if there are not TriggerInputs send the user to the next step
        if trigger_inputs.count() == 0:
            return redirect("recipes:new_step4")

        # load module of selected channel and look for custom view
        try:
            module_name = "channel_{}.views".format(trigger.channel.name)
            channel_module = importlib.import_module(module_name.lower())

            custom_view = getattr(channel_module, 'TriggerInputView')()
            return custom_view.dispatch(request, draft)

        # ImportError => channel- or views-module does not exist
        # AttributeError => There is no custom view defined
        except (ImportError, AttributeError):
            if request.method == "POST":
                return self.post(request, draft, trigger_inputs)
            else:
                return self.get(request, draft, trigger_inputs)

    def post(self, request, draft, trigger_inputs):

        recipe_conditions = []

        for trigger_input in trigger_inputs:

            postValue = request.POST.get('input_%s' % trigger_input.id, '')

            recipe_conditions.append({
                'id': trigger_input.id,
                'value': postValue
            })

        draft['recipe_conditions'] = recipe_conditions

        # redirect to post-trigger-input-hook
        hook_url = self._get_hook_url(draft, 'trigger',
                                      'post_trigger_input_hook')
        if hook_url is not None:
            return redirect(hook_url)

        return redirect("recipes:new_step4")

    def get(self, request, draft, trigger_inputs):

        context = {
            'trigger_inputs': trigger_inputs.values()
        }
        return render(request,
                      'recipes/recipe_create.step3.html',
                      context=context)


class RecipeCreateActionChannelSelectionView(RecipeCreateBaseView):

    @Draft.activate
    def dispatch(self, request, draft):
        """Selection of action channel"""

        # make sure, previous step was executed
        if 'trigger_id' not in draft:
            return redirect("recipes:new_step2")

        try:
            trigger = Trigger.objects.get(id=draft['trigger_id'])
        except Trigger.DoesNotExist:
            messages.error(request,
                           _("The selected trigger does not exist"))
            return redirect("recipes:new_step2")

        if request.method == "POST":
            return self.post(request, draft)
        else:
            return self.get(request, draft, trigger)

    def post(self, request, draft):
        channel_id = request.POST.get('action_channel_id')

        try:
            channel = Channel.objects.get(id=channel_id)

        except Channel.DoesNotExist:
            messages.error(request,
                           _("The selected channel does not exist"))
            return redirect("recipes:new_step4")

        # if the selected channel has no actions redirect to this step
        # (as GET) with error message
        if Action.objects.filter(channel=channel).count() == 0:
            messages.error(request,
                           _("The selected channel has no actions and"
                             "cannot be used as action channel"))
            return redirect("recipes:new_step4")

        # set the action_channel in the session draft
        draft['action_channel_id'] = channel.id

        # check if user is connected and redirect if not
        action_channel = get_channel_instance(channel.name)
        user_state = action_channel.user_is_connected(request.user)
        if user_state == ChannelStateForUser.connected:
            return redirect("recipes:new_step5")
        else:
            # send user to channel authentication. Should just pass through
            # if the user is already authenticated
            auth_url = reverse("{}:connect".format(channel.name.lower()))
            return redirect(auth_url + "?next=" + reverse("recipes:new_step5"))

    def get(self, request, draft, trigger):
        q_status = request.GET.get("status", False)
        if q_status == "success":
            return redirect("recipes:new_step5")
        elif q_status == "error":
            channel_id = draft['action_channel_id']
            channel = Channel.objects.get(id=channel_id)
            messages.error(request,
                           _("Authentication at channel %s failed. Please "
                             "select another channel" % channel.name))

        trigger_outputs = TriggerOutput.objects.filter(trigger=trigger)
        trigger_mimes = {x.mime_type for x in trigger_outputs}

        action_inputs = ActionInput.objects.all()
        applicable_action_inputs = filter(
            lambda a: a.mime_type in trigger_mimes,
            action_inputs
        )
        applicable_action_channels = sorted({
            x.action.channel
            for x
            in applicable_action_inputs
        }, key=lambda c: c.name)

        context = {
            "action_channels": applicable_action_channels
        }

        return render(request,
                      'recipes/recipe_create.step4.html',
                      context=context)


class RecipeCreateActionSelectionView(RecipeCreateBaseView):

    @Draft.activate
    def dispatch(self, request, draft):

        # make sure, previous step was executed
        if 'action_channel_id' not in draft:
            return redirect("recipes:new_step4")

        # test if channel is existent, should never go wrong because of
        # other tests
        try:
            channel = Channel.objects.get(id=draft['action_channel_id'])
        except Channel.DoesNotExist:
            messages.error(request,
                           _("The selected channel does not exist"))
            return redirect("recipes:new_step4")

        # redirect to pre-action-selection-hook
        hook_url = self._get_hook_url(draft, 'action',
                                      'pre_action_selection_hook')
        if hook_url is not None:
            return redirect(hook_url)

        # load module of selected channel and look for custom view
        try:
            module_name = "channel_{}.views".format(channel.name.lower())
            channel_module = importlib.import_module(module_name)

            custom_view = getattr(channel_module, 'ActionSelectionView')()
            return custom_view.dispatch(request, draft)

        # ImportError => channel- or views-module does not exist
        # AttributeError => There is no custom view defined
        except (ImportError, AttributeError):
            if request.method == "POST":
                return self.post(request, draft, channel)
            else:
                return self.get(request, draft, channel)

    def post(self, request, draft, channel):

        # get the action id from the request
        action_id = request.POST.get('action_id')

        # try to get the action
        try:
            action = Action.objects.get(id=action_id, channel=channel)
        # redirect to this step with error message
        except Action.DoesNotExist:
            messages.error(request,
                           _("The selected action does not exist"))
            return redirect("recipes:new_step4")

        # save trigger to session draft
        draft['action_id'] = action.id

        # redirect to post-action-selection-hook
        hook_url = self._get_hook_url(draft, 'action',
                                      'post_action_selection_hook')
        if hook_url is not None:
            return redirect(hook_url)

        return redirect("recipes:new_step6")

    def get(self, request, draft, channel):

        # if the selected channel has no actions redirect to this step
        # (as GET) with error message
        if Action.objects.filter(channel=channel).count() == 0:
            messages.error(request,
                           _("The selected channel has no actions and"
                             "cannot be used as action channel"))
            return redirect("recipes:new_step4")

        # build context and render template
        context = {
            "actions": Action.objects.filter(channel=channel).values()
        }

        return render(request,
                      'recipes/recipe_create.step5.html',
                      context=context)


class RecipeCreateRecipeMappingView(RecipeCreateBaseView):

    @Draft.activate
    def dispatch(self, request, draft):

        # make sure, previous step was executed
        if 'action_id' not in draft:
            return redirect("recipes:new_step5")

        # else load the action's inputs
        try:
            action = Action.objects.get(id=draft['action_id'])
        except Action.DoesNotExist:
            messages.error(request,
                           _("The selected action does not exist"))
            return redirect("recipes:new_step5")

        # redirect to pre-recipe-mappings-trigger-hook
        hook_url = self._get_hook_url(draft, 'trigger',
                                      'pre_recipe_mappings_trigger_hook')
        if hook_url is not None:
            return redirect(hook_url)

        # redirect to pre-recipe-mappings-action-hook
        hook_url = self._get_hook_url(draft, 'action',
                                      'pre_recipe_mappings_action_hook')
        if hook_url is not None:
            return redirect(hook_url)

        action_inputs = ActionInput.objects.filter(action=action)

        # if there are not TriggerInputs send the user to the next step
        if action_inputs.count() == 0:
            return redirect("recipes:new_step7")

        if request.method == "POST":
            return self.post(request, draft, action_inputs)
        else:
            return self.get(request, draft, action_inputs)

    def post(self, request, draft, action_inputs):

        recipe_mappings = []

        for action_input in action_inputs:

            postValue = request.POST.get('input_%s' % action_input.id, '')

            recipe_mappings.append({
                'id': action_input.id,
                'value': postValue
            })

        draft['recipe_mappings'] = recipe_mappings

        # redirect to post-recipe-mappings-trigger-hook
        hook_url = self._get_hook_url(draft, 'trigger',
                                      'post_recipe_mappings_trigger_hook')
        if hook_url is not None:
            return redirect(hook_url)

        # redirect to post-recipe-mappings-action-hook
        hook_url = self._get_hook_url(draft, 'action',
                                      'post_recipe_mappings_action_hook')
        if hook_url is not None:
            return redirect(hook_url)

        return redirect("recipes:new_step7")

    def get(self, request, draft, action_inputs):

        if 'trigger_id' not in draft:
            return redirect("recipes:new_step2")

        try:
            trigger = Trigger.objects.get(id=draft['trigger_id'])
        except Trigger.DoesNotExist:
            messages.error(request,
                           _("The selected trigger does not exist"))
            return redirect("recipes:new_step2")

        trigger_outputs = TriggerOutput.objects.filter(trigger=trigger)
        context = {
            "trigger_outputs": trigger_outputs.values(),
            "action_inputs": action_inputs.values()
        }
        return render(request,
                      'recipes/recipe_create.step6.html',
                      context=context)


class RecipeCreateSaveView(RecipeCreateBaseView):

    @Draft.activate
    def post(self, request, draft):

        draft['synopsis'] = request.POST.get('synopsis', '')
        draft.createRecipe()

        return redirect("recipes:list")

    @Draft.activate
    def get(self, request, draft):

        try:
            trigger = Trigger.objects.get(id=draft['trigger_id'])
        except Trigger.DoesNotExist:
            return redirect("recipes:new_step2")

        try:
            trigger_channel = get_channel_instance(trigger.channel.name)

            if 'recipe_conditions' in draft:
                recipe_conditions = draft['recipe_conditions']
            else:
                recipe_conditions = []

            trigger_synopsis = trigger_channel.trigger_synopsis(
                    trigger.id, recipe_conditions)
        except AttributeError:
            messages.error(
                    request,
                    _("Internal Server Error: Invalid Channel implementation"))
            trigger_synopsis = ""

        try:
            action = Action.objects.get(id=draft['action_id'])
        except Action.DoesNotExist:
            return redirect("recipes:new_step5")

        try:
            action_channel = get_channel_instance(action.channel.name)

            if 'recipe_mappings' in draft:
                recipe_mappings = draft['recipe_mappings']
            else:
                recipe_mappings = []

            action_synopsis = action_channel.action_synopsis(
                    action.id, recipe_mappings)
        except AttributeError:
            messages.error(
                    request,
                    _("Internal Server Error: Invalid Channel implementation"))
            action_synopsis = ""

        synopsis = "If {}, {}".format(trigger_synopsis, action_synopsis)

        ctx = {
            'synopsis': synopsis,
            'trigger': trigger,
            'action': action
        }

        return render(request, 'recipes/recipe_create.step7.html', context=ctx)


class RecipeEditView(LoginRequiredMixin, View):

    def post(self, request, id):

        try:
            with transaction.atomic():
                recipe = Recipe.objects.get(id=id)
                recipe.synopsis = request.POST.get('synopsis', '')[:140]
                recipe.save()

                conditions = RecipeCondition.objects.filter(recipe=recipe)
                for condition in conditions:
                    post_key = 'condition_{}'.format(condition.id)
                    post_value = request.POST.get(post_key, '')
                    condition.value = post_value
                    condition.save()

                mappings = RecipeMapping.objects.filter(recipe=recipe)
                for mapping in mappings:
                    post_key = 'mapping_{}'.format(mapping.id)
                    post_value = request.POST.get(post_key, '')
                    mapping.trigger_output = post_value
                    mapping.save()

        except IntegrityError:
            messages.error(request, _("Your changes could not be saved. "
                                      "Please try again later."))
        else:
            messages.success(request, _("Your changes have been saved."))

        return redirect('recipes:list')

    def get(self, request, id):

        recipe = Recipe.objects.get(id=id)
        conditions = RecipeCondition.objects.filter(recipe=recipe)
        mappings = RecipeMapping.objects.filter(recipe=recipe)
        trigger_outputs = TriggerOutput.objects.filter(trigger=recipe.trigger)

        ctx = {
            "recipe": recipe,
            "conditions": conditions,
            "mappings": mappings,
            "trigger_outputs": trigger_outputs
        }

        return render(request, 'recipes/recipe_edit.html', context=ctx)


class RecipeDeleteView(LoginRequiredMixin, View):

    def post(self, request, id):

        action = request.POST.get('action', 'keep')

        if action == 'delete':
            Recipe.objects.get(id=id).delete()

        return redirect("recipes:list")

    def get(self, request, id):

        recipe = Recipe.objects.get(id=id)

        return render(request,
                      'recipes/recipe_delete.html',
                      context={'recipe': recipe})
