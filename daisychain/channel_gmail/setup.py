from . import channel
from core.models import Channel, Trigger, TriggerInput, TriggerOutput, \
                        Action, ActionInput


def setup():

    # Create Channel
    c = Channel(name="gmail")
    c.save()

    # Create Trigger
    trigger1 = Trigger(channel=c,
                       name="New Mail for you",
                       trigger_type=100)
    trigger1.save()
