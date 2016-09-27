from django.db import transaction
from core.models import (Trigger, TriggerInput,
                         Action, ActionInput,
                         Recipe, RecipeCondition, RecipeMapping)


class Draft(dict):

    def __init__(self, request):
        self.request = request
        if 'recipe_draft' not in request.session:
            dict.__init__(self, {})
        else:
            dict.__init__(self, request.session['recipe_draft'])

    def createRecipe(self):

        with transaction.atomic():
            recipe = Recipe(trigger=Trigger.objects.get(id=self['trigger_id']),
                            action=Action.objects.get(id=self['action_id']),
                            synopsis=self['synopsis'],
                            user=self.request.user)
            recipe.save()

            if 'recipe_conditions' in self:
                for condition in self['recipe_conditions']:
                    trigger_input = TriggerInput.objects.get(
                            id=condition['id'])
                    RecipeCondition(recipe=recipe,
                                    trigger_input=trigger_input,
                                    value=condition['value']).save()

            for mapping in self['recipe_mappings']:
                action_input = ActionInput.objects.get(id=mapping['id'])
                RecipeMapping(recipe=recipe,
                              trigger_output=mapping['value'],
                              action_input=action_input).save()

    def activate(func):

        def func_wrapper(*args, **kwargs):

            # expect last positional argument to be the request parameter
            request = args[-1]

            draft = Draft(request)

            args_with_draft = args + (draft,)

            return_val = func(*args_with_draft, **kwargs)

            request.session['recipe_draft'] = dict(draft)
            request.session.modified = True
            return return_val

        return func_wrapper
