from . import channel
from core.models import Channel, Trigger, TriggerInput, TriggerOutput, \
                        Action, ActionInput


def setup():

    # Create Channel
    c = Channel(name="instagram")
    c.save()

    # Create Trigger
    trigger1 = Trigger(channel=c,
                       name="New Photo by you",
                       trigger_type=100)
    trigger1.save()
    trigger2 = Trigger(channel=c,
                       name="New Photo by you with specific hashtag",
                       trigger_type=101)
    trigger2.save()
    trigger3 = Trigger(channel=c,
                       name="New Video by you",
                       trigger_type=200)
    trigger3.save()
    trigger4 = Trigger(channel=c,
                       name="New Video by you with specific hashtag",
                       trigger_type=201)
    trigger4.save()

    TriggerOutput(trigger=trigger1,
                  name="caption",
                  mime_type="text/plain").save()
    TriggerOutput(trigger=trigger1,
                  name="url",
                  mime_type="text/plain").save()
    TriggerOutput(trigger=trigger1,
                  name="image_standard",
                  mime_type="image/jpg").save()
    TriggerOutput(trigger=trigger1,
                  name="image_low",
                  mime_type="image/jpg").save()
    TriggerOutput(trigger=trigger1,
                  name="thumbnail",
                  mime_type="image/jpg").save()

    TriggerOutput(trigger=trigger2,
                  name="caption",
                  mime_type="text/plain").save()
    TriggerOutput(trigger=trigger2,
                  name="url",
                  mime_type="text/plain").save()
    TriggerOutput(trigger=trigger2,
                  name="image_standard",
                  mime_type="image/jpg").save()
    TriggerOutput(trigger=trigger2,
                  name="image_low",
                  mime_type="image/jpg").save()
    TriggerOutput(trigger=trigger2,
                  name="thumbnail",
                  mime_type="image/jpg").save()
    TriggerOutput(trigger=trigger2,
                  name="caption_without_hashtags",
                  mime_type="text/plain").save()

    TriggerOutput(trigger=trigger3,
                  name="text/plain",
                  mime_type="text").save()
    TriggerOutput(trigger=trigger3,
                  name="url",
                  mime_type="text/plain").save()
    TriggerOutput(trigger=trigger3,
                  name="video_standard",
                  mime_type="video/mp4").save()
    TriggerOutput(trigger=trigger3,
                  name="video_low",
                  mime_type="video/mp4").save()
    TriggerOutput(trigger=trigger3,
                  name="video_low_bandwidth",
                  mime_type="video/mp4").save()
    TriggerOutput(trigger=trigger3,
                  name="cover_image_standard",
                  mime_type="video/mp4").save()
    TriggerOutput(trigger=trigger3,
                  name="cover_image_low",
                  mime_type="video/mp4").save()
    TriggerOutput(trigger=trigger3,
                  name="cover_image_thumbnail",
                  mime_type="video/mp4").save()

    TriggerOutput(trigger=trigger4,
                  name="text/plain",
                  mime_type="text").save()
    TriggerOutput(trigger=trigger4,
                  name="url",
                  mime_type="text/plain").save()
    TriggerOutput(trigger=trigger4,
                  name="video_standard",
                  mime_type="video/mp4").save()
    TriggerOutput(trigger=trigger4,
                  name="video_low",
                  mime_type="video/mp4").save()
    TriggerOutput(trigger=trigger4,
                  name="video_low_bandwidth",
                  mime_type="video/mp4").save()
    TriggerOutput(trigger=trigger4,
                  name="cover_image_standard",
                  mime_type="video/mp4").save()
    TriggerOutput(trigger=trigger4,
                  name="cover_image_low",
                  mime_type="video/mp4").save()
    TriggerOutput(trigger=trigger4,
                  name="cover_image_thumbnail",
                  mime_type="video/mp4").save()
