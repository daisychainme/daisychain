from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone


class ChannelManager(models.Manager):
    def get_by_natural_key(self, name):
        return self.get(name__iexact=name)


class Channel(models.Model):

    objects = ChannelManager()

    name = models.CharField(_("Name"), max_length=64, unique=True)
    color = models.CharField(_("Channel color"), max_length=7)
    image = models.CharField(_("Channel image"), max_length=128)
    font_color = models.CharField(_("Channel Font"), max_length=7)

    def natural_key(self):
        return (self.name,)

    class Meta:
        verbose_name = _('Channel')
        verbose_name_plural = _('Channels')

    def __str__(self):
        return 'Channel {}'.format(self.name)


class TriggerManager(models.Manager):
    def get_by_natural_key(self, channel_name, trigger_type):
        return self.get(channel__name__iexact=channel_name,
                        trigger_type=trigger_type)


class Trigger(models.Model):
    """A trigger that is offered by a specific channel."""

    objects = TriggerManager()

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    trigger_type = models.IntegerField(_("Type"))
    name = models.CharField(_("Name"), max_length=128)

    def natural_key(self):
        return (self.channel.name, self.trigger_type)

    class Meta:
        verbose_name = _('Trigger')
        verbose_name_plural = _('Triggers')
        unique_together = ('channel', 'trigger_type')

    def __str__(self):
        return 'Trigger {} (type: {}, {})'.format(self.name,
                                                  self.trigger_type,
                                                  self.channel)


class TriggerInputManager(models.Manager):
    def get_by_natural_key(self, channel_name, trigger_type, name):
        return self.get(trigger__channel__name__iexact=channel_name,
                        trigger__trigger_type=trigger_type,
                        name=name)


class TriggerInput(models.Model):

    objects = TriggerInputManager()

    trigger = models.ForeignKey(Trigger, on_delete=models.CASCADE)
    name = models.CharField(_("Name"), max_length=128)

    def natural_key(self):
        return (self.trigger.channel.name,
                self.trigger.trigger_type,
                self.name)

    class Meta:
        verbose_name = _('Trigger Input')
        verbose_name_plural = _('Trigger Inputs')
        unique_together = ('trigger', 'name')

    def __str__(self):
        return 'Trigger Input {} ({})'.format(self.name, self.trigger)


class TriggerOutputManager(models.Manager):
    def get_by_natural_key(self, channel_name, trigger_type, name):
        return self.get(trigger__channel__name__iexact=channel_name,
                        trigger__trigger_type=trigger_type,
                        name=name)


class TriggerOutput(models.Model):
    """Any trigger can have 1-* outputs of different mime types."""

    objects = TriggerOutputManager()

    trigger = models.ForeignKey(Trigger, on_delete=models.CASCADE)
    name = models.CharField(_("Name"), max_length=128)
    mime_type = models.CharField(_("Mime type"), max_length=255)
    example_value = models.CharField(_("Output example"), max_length=1024)

    def natural_key(self):
        return (self.trigger.channel.name,
                self.trigger.trigger_type,
                self.name)

    class Meta:
        verbose_name = _('Trigger Output')
        verbose_name_plural = _('Trigger Outputs')
        unique_together = ('trigger', 'name')

    def __str__(self):
        'Trigger Output: {}, (mime: {}, {})'.format(self.trigger.name,
                                                    self.mime_type,
                                                    self.trigger)


class ActionManager(models.Manager):
    def get_by_natural_key(self, channel_name, action_type):
        return self.get(channel__name__iexact=channel_name,
                        action_type=action_type)


class Action(models.Model):
    """An action that is offered by a specific channel."""

    objects = ActionManager()

    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    action_type = models.IntegerField(_("Type"))
    name = models.CharField(_("Name"), max_length=128)

    def natural_key(self):
        return (self.channel.name, self.action_type)

    class Meta:
        verbose_name = _('Action')
        verbose_name_plural = _('Actions')
        unique_together = ('channel', 'action_type')

    def __str__(self):
        return 'Action: {}, (type: {}, {})'.format(self.name,
                                                   self.action_type,
                                                   self.channel)


class ActionInputManager(models.Manager):
    def get_by_natural_key(self, channel_name, action_type, name):
        return self.get(action__channel__name__iexact=channel_name,
                        action__action_type=action_type,
                        name=name)


class ActionInput(models.Model):
    """Any action can have 1-* inputs of different mime types"""

    objects = ActionInputManager()

    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    name = models.CharField(_("Name"), max_length=128)
    mime_type = models.CharField(_("Mime type"), max_length=255)

    def natural_key(self):
        return (self.action.channel.name, self.action.action_type, self.name)

    class Meta:
        verbose_name = _('Action Input')
        verbose_name_plural = _('Action Inputs')
        unique_together = ('action', 'name')

    def __str__(self):
        return 'Action input: {}, (mime: {}, {})'.format(self.action.name,
                                                         self.mime_type,
                                                         self.action)


class Recipe(models.Model):
    """A recipe that is created by exactly one user."""

    trigger = models.ForeignKey(Trigger, on_delete=models.CASCADE)
    action = models.ForeignKey(Action, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    synopsis = models.CharField(_("Synopsis"), max_length=140, default='')
    creation_date = models.DateTimeField(_("Creation Date"),
                                         default=timezone.now)

    class Meta:
        verbose_name = _('Recipe')
        verbose_name_plural = _('Recipes')

    def __str__(self):
        return 'Recipe: user: {}, {}, {}'.format(self.user,
                                                 self.trigger,
                                                 self.action)


class RecipeMapping(models.Model):
    """Mapping of trigger outputs to action inputs for a specific recipe."""

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    trigger_output = models.TextField(_("Trigger Input text"))
    action_input = models.ForeignKey(ActionInput, on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Recipe Mapping')
        verbose_name_plural = _('Recipe Mappings')
        unique_together = ('recipe', 'action_input')

    def __str__(self):
        return 'Recipe mapping: {}, Trigger Output: {}, {}'.format(
                                                        self.recipe,
                                                        self.trigger_output,
                                                        self.action_input)


class RecipeCondition(models.Model):
    """ Conditions that have to hold for a trigger to fire """

    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    trigger_input = models.ForeignKey(TriggerInput, on_delete=models.CASCADE)
    value = models.CharField(_("Condition Value"), max_length=1024)

    class Meta:
        verbose_name = _('Recipe Condition')
        verbose_name_plural = _('Recipe Conditions')
        unique_together = ('recipe', 'trigger_input')
