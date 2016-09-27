from django.core.urlresolvers import reverse

from enum import IntEnum
from hashlib import sha256
from hmac import new as hmac_new
from time import time
from tempfile import TemporaryFile
import logging
import re
import requests

from core import models
from core.core import Core
from core.channel import (Channel, NotSupportedTrigger, NotSupportedAction,
                          ConditionNotMet, ChannelStateForUser)
from .models import InstagramAccount
from .conf import Config

log = logging.getLogger("channel")


class TriggerType(IntEnum):
    new_photo = 100
    new_photo_with_tags = 101


class ApiException(Exception):
    def __init__(self, type, code, message):
        self.type = type
        self.code = code
        self.message = message

    def __str__(self):
        return "{} [Code: {}] \"{}\"".format(self.type,
                                             self.code,
                                             self.message)


class InstagramChannel(Channel):

    hashtag_pattern = r'(^##$|\s##\b|##\b\s)'

    def fill_recipe_mappings(self, trigger_type, userid,
                             payload, conditions, mappings):
        """Implementing abstract class core.Channel"""
        log.debug(("Called fill_recipe_mappings with type {}, userid {}, "
                   "payload {}, conditions {}, mappings {}").format(
                          trigger_type, userid, payload, conditions, mappings))

        if trigger_type == TriggerType.new_photo:
            return self._fill_mappings_for_photo(payload, mappings)

        elif trigger_type == TriggerType.new_photo_with_tags:
            return self._fill_mappings_for_photo_with_tags(
                    payload, conditions, mappings)

        else:
            raise NotSupportedTrigger()

    def handle_action(self, action_type, userid, inputs):
        """Implementing abstract class core.Channel"""
        # this channel has no actions
        log.warning("Called handle_action on Instagram")
        raise NotSupportedAction()

    def trigger_synopsis(self, trigger_id, conditions):
        """Overriding abstract class core.Channel"""

        trigger_type = models.Trigger.objects.get(id=trigger_id).trigger_type

        if trigger_type == TriggerType.new_photo:
            return "new photo by you on Instagram"
        elif trigger_type == TriggerType.new_photo_with_tags:
            hashtag = conditions[0]['value']
            return ('new photo by you with hashtag "{}" '
                    'on Instagram').format(hashtag)

    def user_is_connected(self, user):
        """check if the given user is authenticated for this channel."""

        # look for corresponding InstagramAccount model
        try:
            instagram_user = InstagramAccount.objects.get(user=user)

        # We have no InstagramAccount object for the given user
        except InstagramAccount.DoesNotExist:
            return ChannelStateForUser.initial

        # We have a InstagramAccount object, check if the access_token is valid
        url = Config.get("API_USER_SELF_ENDPOINT") \
            + "?access_token=" + instagram_user.access_token
        r = requests.get(url)

        # request was successful
        if r.ok:
            try:
                response = r.json()["data"]
            except (ValueError, KeyError):
                log.error("Error while fetch user metadata from instagram: "
                          "response json contained no 'data'")
                return ChannelStateForUser.expired

            # everything okay, the user authentication is valid!
            return ChannelStateForUser.connected

        # likely invalid access_token
        else:
            instagram_user.delete()
            return ChannelStateForUser.expired

    def _fill_mappings_for_photo(self, payload, inputs):

        payload["caption_without_hashtags"] = payload['caption']
        inputs_with_photos = self._replace_image_inputs(payload, inputs)
        return self._replace_text_inputs(payload, inputs_with_photos)

    def _fill_mappings_for_photo_with_tags(self, payload, conditions, inputs):

        if 'hashtag' not in conditions:
            log.error("fill_recipe_mappings has been called but there was "
                      "no 'hashtag' field in the conditions")
            raise ConditionNotMet()   # TODO semantically correct exception

        hashtag = conditions['hashtag']
        if not hashtag.startswith("#"):
            hashtag = "#" + hashtag

        pattern = self.hashtag_pattern.replace("##", hashtag)

        if not re.search(pattern, payload["caption"]):
            # the triggered event did not match the hashtag from the user
            # defined recipe condition
            raise ConditionNotMet()

        wo_caption = re.sub(pattern, '', payload['caption'])

        payload['caption_without_hashtags'] = wo_caption

        inputs_with_photos = self._replace_image_inputs(payload, inputs)
        return self._replace_text_inputs(payload, inputs_with_photos)

    def _replace_text_inputs(self, payload, inputs):
        outs = {}
        for key in inputs:
            val = inputs[key]
            if type(val) is str:
                if val.find("%caption_without_hashtags%") > -1:
                    val = val.replace("%caption_without_hashtags%",
                                      payload["caption_without_hashtags"])
                if val.find("%caption%") > -1:
                    val = val.replace("%caption%", payload["caption"])
                if val.find("%url%") > -1:
                    val = val.replace("%url%", payload["url"])
            outs[key] = val

        return outs

    def _replace_image_inputs(self, payload, inputs):
        outs = {}
        for key in inputs:
            val = inputs[key]
            if val.find("%image_standard%") > -1:
                val = self.load_image(payload["image_standard"])
            elif val.find("%image_low%") > -1:
                val = self.load_image(payload["image_low"])

            outs[key] = val

        return outs

    def _build_absolute_uri(self, alias):
        domain_base = Config.get("DOMAIN_BASE")

        if domain_base is "":
            log.warning("Instagram Config DOMAIN_BASE was accessed before set")

        return domain_base + reverse(alias)

    def create_subscription(self):

        get_params = {
            "client_id": Config.get("CLIENT_ID"),
            "client_secret": Config.get("CLIENT_SECRET")
        }

        res = requests.get(Config.get("API_SUBSCRIPTION_ENDPOINT"), get_params)

        if res.ok:
            if 'data' in res.json():
                if len(res.json()["data"]) > 0:
                    log.info("Instagram already subscribed, do not repeat")
                    return
                else:
                    log.info("Instagram not yet subscribed, do it")
            else:
                log.warning("Instagram API subscription list returned code 200"
                            " but response had no attribute 'data'. "
                            "Nevertheless trying to create subscription")
        else:
            log.error("Error while fetching subscription list from Instagram. "
                      "Nevertheless trying to create subscription")

        post_data = {
            "client_id": Config.get("CLIENT_ID"),
            "client_secret": Config.get("CLIENT_SECRET"),
            "object": "user",
            "aspect": "media",
            "verify_token": self.generate_subscription_verify_token(),
            "callback_url": self._build_absolute_uri("instagram:subscription")
        }
        res = requests.post(Config.get("API_SUBSCRIPTION_ENDPOINT"), post_data)

        if not res.ok:
            log.error("Could not subscribe to Instagram. Error message:")
            log.error(res.json())
            return False

        return True

    def generate_subscription_verify_token(self):
        return hmac_new(Config.get("CLIENT_SECRET").encode("utf-8"),
                        msg=Config.get("DJANGO_SECRET").encode("utf-8"),
                        digestmod=sha256).hexdigest()

    def get_media_data(self, instagram_user, mediaid):

        # request data
        url = (Config.get("API_MEDIA_ENDPOINT") % mediaid) \
            + "?access_token=" + instagram_user.access_token
        r = requests.get(url)

        # request was successful
        if r.ok:
            try:
                return r.json()["data"]
            except KeyError:
                log.error("Error while fetch media metadata from instagram: "
                          "response json contained no 'data'")
                raise ApiException("Internal",
                                   "invalid_response",
                                   "The response contained no 'data' element.")

        # request failed
        else:
            log.error("Error while loading media metadata from instagram")
            log.error(r.json())
            error = r.json()["meta"]
            raise ApiException(error['error_type'],
                               error['code'],
                               error['error_message'])

    def load_image(self, url):
        r = requests.get(url, stream=True)
        if r.ok:
            tmp_file = TemporaryFile()
            for chunk in r.iter_content(chunk_size=1024):
                if chunk:
                    tmp_file.write(chunk)
            tmp_file.seek(0)
            return tmp_file
        else:
            log.error("Error while downloading media from instagram")
            log.error(r.json())
            raise ApiException("InternalDownloadError",
                               r.status_code,
                               "Error while loading image %s" % url)

    def fire_trigger(self, trigger):
        """Called by subscription view"""

        log.debug("Called InstagramChannel.fire_trigger with %s" % trigger)

        try:
            userid = trigger['object_id']
            mediaid = trigger['data']['media_id']
        except KeyError:
            log.error("[Instagram] Malformed incoming subscription json")
            return

        try:
            instagram_user = InstagramAccount.objects.get(instagram_id=userid)
        except InstagramAccount.DoesNotExist:
            # The user whose media changed is not registered in our system
            # Should never happen because Instagram sends us only triggers
            # for users who granted us access to their account via OAuth
            log.error(("[Instagram] incoming subscription for "
                       "unknown user {}").format(userid))
            return

        try:
            media = self.get_media_data(instagram_user, mediaid)

            if media["type"] == "image":
                self._fire_image_trigger(instagram_user.user, media)
            # elif media["type"] == "video":
                # self._fire_video_trigger(instagram_user.user, media)

        except ApiException:
            log.error("InstagramChannel.fire_trigger exited because of "
                      "ApiException")
            return
        except KeyError:
            log.error("[Instagram] Unexpected KeyError in fire_trigger")

    def _fire_image_trigger(self, user, media):
        """Queue image trigger at core"""

        log.debug("Called InstagramChannel._fire_image_trigger")

        payload = {}

        if isinstance(media["caption"], dict):
            payload['caption'] = media["caption"]["text"]
        else:
            payload['caption'] = ""

        payload["url"] = media["link"]

        if isinstance(media["images"], dict):
            images = media["images"]
            if isinstance(images["standard_resolution"], dict):
                payload["image_standard"] = images[
                        "standard_resolution"]["url"]
            if isinstance(images["low_resolution"], dict):
                payload["image_low"] = images["low_resolution"]["url"]
            if isinstance(images["thumbnail"], dict):
                payload["thumbnail"] = images["thumbnail"]["url"]

        core = Core()

        log.debug(("Instagram fires handle_trigger with type {}, user.id {}, "
                   "payload {}").format(
                       TriggerType.new_photo, user.id, payload))
        core.handle_trigger("Instagram",
                            TriggerType.new_photo,
                            user.id,
                            payload)

        if len(media["tags"]) > 0:
            payload["tags"] = media["tags"]
            log.debug(("Instagram fires handle_trigger with type {}, "
                       "user.id {}, payload {}").format(
                           TriggerType.new_photo_with_tags, user.id, payload))
            core.handle_trigger("Instagram",
                                TriggerType.new_photo_with_tags,
                                user.id,
                                payload)

    '''
    def _fill_mappings_for_video(self, payload, inputs):
        pass

    def _fill_mappings_for_video_with_tags(self, payload, conditions, inputs):
        pass

    def _fire_video_trigger(self, user, media):
        """Queue image trigger at core"""
        log.debug("Called InstagramChannel._fire_video_trigger")

        payload = {
            "caption": media["caption"]["text"],
            "url": media["link"],
            "video_standard": media["videos"]["standard_resolution"]["url"],
            "video_low": media["videos"]["low_resolution"]["url"],
            "video_low_bandwidth": media["videos"]["low_bandwidth"]["url"],
            "image_standard": media["images"]["standard_resolution"]["url"],
            "image_low": media["images"]["low_resolution"]["url"],
            "thumbnail": media["images"]["thumbnail"]["url"]
        }

        core = Core()

        core.handle_trigger("Instagram",
                            TriggerType.new_video,
                            user.id,
                            payload)

        if len(media["tags"]) > 0:
            payload["tags"] = media["tags"]
            core.handle_trigger("Instagram",
                                TriggerType.new_video_with_tags,
                                user.id,
                                payload)

        """
        if len(media['users_in_photo']) > 0:
            core.handle_trigger("Instagram",
                                TRIGGER_NEW_PHOTO_WITH_PERSON,
                                user)
        """
    '''
