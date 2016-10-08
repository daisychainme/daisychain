import logging
import re
from enum import IntEnum
from uuid import uuid4

import magic
import requests
from django.core.urlresolvers import reverse
from django.utils.dateparse import parse_datetime
from django.utils.translation import ugettext as _

import core.utils
from core import models
from core.channel import (Channel, NotSupportedTrigger, NotSupportedAction,
                          ConditionNotMet, ChannelStateForUser)
from core.core import Core
from .config import Config
from .models import FacebookAccount

log = logging.getLogger("channel")


class TriggerType(IntEnum):
    new_post = 100
    new_photo = 101
    new_photo_with_hashtag = 102
    new_link = 103
    new_video = 104


class ActionType(IntEnum):
    post_new_post = 100
    post_new_photo = 101
    post_new_link = 103
    post_new_video = 104
    delete_posts_until = 105


class FacebookChannel(Channel):
    hashtag_pattern = r"(^.*\s##$|^##\s.*$|^.*##\s.*$|^##$)"

    def fire_trigger(self, trigger_data):
        """
        Handles incoming triggers

        params:
            trigger_data = a dictionary that contains the payload sent by
                           facebook as the event payload.
        """
        if 'statuses' in trigger_data['changed_fields']:
            # extract data
            fb_timestamp = trigger_data['time']
            fb_user_id = trigger_data['uid']
            try:
                fb_user = FacebookAccount.objects.get(username=fb_user_id)
            except FacebookAccount.DoesNotExist:
                log.error("Facebook-Trigger for UID:{} could not found! Ignoring webhook".format(fb_user_id))
                return
            fb_response_fields = 'message,actions,full_picture,picture,from,created_time,' \
                                 'link,permalink_url,type,description,source,object_id'

            feeds = self._getFeeds(user=fb_user,
                                   time=fb_timestamp,
                                   fields=fb_response_fields)

            for feed in feeds:
                trigger_types = self._get_trigger_types(feed)
                payload = self._get_payload(feed)
                # pass the data to the core and let it handle the trigger
                try:
                    channel = models.Channel.objects.get(name="Facebook")
                except models.Channel.DoesNotExist:
                    log.error("Facebook is made by Schroedinger. Class does exist, "
                              "Database entry does not.. o.O")
                    return
                for trigger in trigger_types:
                    log.debug(("Facebook fires handle_trigger with type {}, fb_user.id {}, "
                               "payload {}").format(trigger,
                                                    fb_user.user_id,
                                                    payload))
                    Core().handle_trigger(channel_name=channel.name,
                                          trigger_type=trigger,
                                          userid=fb_user.user_id,
                                          payload=payload)
        else:
            raise NotSupportedTrigger()

    @staticmethod
    def _get_trigger_types(feed):
        trigger_types = []
        if 'link' in feed['type']:
            trigger_types.append(TriggerType.new_link)
        elif 'status' in feed['type']:
            trigger_types.append(TriggerType.new_post)
        elif 'photo' in feed['type']:
            trigger_types.append(TriggerType.new_photo)
            if 'message' in feed.keys() and '#' in feed['message']:
                trigger_types.append(TriggerType.new_photo_with_hashtag)
        elif 'video' in feed['type']:
            trigger_types.append(TriggerType.new_video)
        else:
            raise NotSupportedTrigger()
        return trigger_types

    def fill_recipe_mappings(self, trigger_type, userid,
                             payload, conditions, mappings):
        """Implementing abstract class core.Channel"""
        log.debug(("Called fill_recipe_mappings with type {}, userid {}, "
                   "payload {}, conditions {}, mappings {}").format(
            trigger_type, userid, payload, conditions, mappings))

        if trigger_type == TriggerType.new_photo_with_hashtag:
            return self._fill_mappings_for_new_entry_with_hashtags(payload=payload,
                                                                   conditions=conditions,
                                                                   inputs=mappings)
        else:
            return self._fill_mappings_for_new_entry(payload=payload,
                                                     inputs=mappings)

    def handle_action(self, action_type, userid, inputs):
        """Execute the action specified in action_type using userid and inputs.

        This method is called by worker threads when they process a trigger
        and any action of this channel is requested.

        Args:
            action_type (int): as defined in model Action.action_type
            userid (int): the user to whom the action belongs
            inputs (dict): the values that have been filled in another
                channel's get_trigger_inputs() and shall be used in this
                action
        Returns:
            None
        """

        # get user
        try:
            fb_user = FacebookAccount.objects.get(user_id=userid)
        except FacebookAccount.DoesNotExist:
            log.error("Facebook-Action for UID:{} could not found! Ignoring webhook".format(userid))
            return
        # initiate action based on the given action type
        if action_type == ActionType.post_new_post:
            self.new_post(fb_user=fb_user, status=inputs['message'])
        elif action_type == ActionType.post_new_photo:
            self.new_picture(fb_user=fb_user, fields=inputs)
        elif action_type == ActionType.post_new_link:
            self.new_link(fb_user=fb_user, fields=inputs)
        elif action_type == ActionType.post_new_video:
            self.new_video(fb_user=fb_user, fields=inputs)
        else:
            raise NotSupportedAction(
                "This action is not supported by the Facebook channel.")

    def trigger_synopsis(self, trigger_id, conditions):
        """Overriding abstract class core.Channel"""

        trigger_type = models.Trigger.objects.get(id=trigger_id).trigger_type

        if trigger_type == TriggerType.new_post:
            return "new post by you on Facebook"
        elif trigger_type == TriggerType.new_link:
            return "new link posted by you on Facebook"
        elif trigger_type == TriggerType.new_photo:
            return "new photo posted by you on Facebook"
        elif trigger_type == TriggerType.new_photo_with_hashtag:
            hashtag = conditions[0]['value']
            return ('new photo by you with hashtag "{}" '
                    'on Facebook').format(hashtag)
        elif trigger_type == TriggerType.new_video:
            return "new video posted by you on Facebook"

    def _fill_mappings_for_new_entry(self, payload, inputs):
        log.error("fill_mappings")
        inputs_with_photos = self._replace_image_inputs(payload, inputs)
        return self._replace_text_inputs(payload, inputs_with_photos)

    def _fill_mappings_for_new_entry_with_hashtags(self, payload, conditions, inputs):
        if 'hashtag' not in conditions:
            log.error("fill_recipe_mappings has been called but there was "
                      "no 'hashtag' field in the conditions")
            raise ConditionNotMet()  # TODO semantically correct exception
        hashtag = conditions['hashtag']
        if not hashtag.startswith("#"):
            hashtag = "#" + hashtag
        pattern = self.hashtag_pattern.replace("##", hashtag)
        if not re.search(pattern, payload["message"]):
            # the triggered event did not match the hashtag from the user
            # defined recipe condition
            log.error('condition not met!')
            raise ConditionNotMet()
        # payload['message'] = re.sub(pattern, '', payload['message'])
        return self._fill_mappings_for_new_entry(payload=payload,
                                                 inputs=inputs)

    def new_post(self, fb_user, status):
        if not isinstance(status, str):
            raise ValueError(_('Should only be called with a string.'))

        data = {
            'message': status,
            'access_token': fb_user.access_token,
        }

        fb_request_url = Config.get("API_BASE_URI") + "/me/feed"
        resp = requests.post(fb_request_url, data=data)
        if resp.ok and "id" in resp.json():
            log.info(_("A new Post with ID {} published!".format(resp.json()['id'])))
        else:
            log.error(_("A failure occurred while posting on Facebook : {}".format(resp.json())))

    # def delete_post_until(self, fb_user, inputs):
    #      #try:
    #          data = {
    #              'access_token': fb_user.access_token,
    #              'fields': 'id',
    #              'until': int(time.mktime(parser(inputs['date']))),
    #          }
    #
    #          fb_request_url = Config.get("API_BASE_URI") + "/me/feed"
    #          resp = requests.get(fb_request_url, params=data)
    #          break_loop = False
    #          while resp.ok and not break_loop:
    #              for feed in resp.json()['data']:
    #                  resp_del = requests.delete(Config.get("API_BASE_URI" + feed['id']))
    #                  log.debug("ReturnValue {}".format(resp_del.json()))
    #              try:
    #                  resp = requests.get(resp.json()['paging']['next'], timeout=5.00)
    #              except Exception:
    #                  pass
    #                  break
    #          if resp.ok and "id" in resp.json():
    #              fb_user.last_post_id = resp.json()['id']
    #              fb_user.save
    #          else:
    #              log.error(_("A failure occurred while posting on Facebook : {}".format(resp.json())))
    #   #   iexcept:
    # #    pass

    def new_link(self, fb_user, fields):

        fields['access_token'] = fb_user.access_token

        fb_request_url = Config.get("API_BASE_URI") + "/me/feed"
        resp = requests.post(fb_request_url, data=fields)
        if resp.ok and "id" in resp.json():
            log.info(_("A new link with ID {} published!".format(resp.json()['id'])))
        else:
            log.error(_("A failure occurred while posting on Facebook : {}".format(resp.json())))

    def new_picture(self, fb_user, fields):
        if 'message' not in fields:
            fields['message'] = ''

        image_file = fields['image']
        image_file.seek(0)
        mime_type = magic.from_buffer(image_file.read(), mime=True)

        image_file.seek(0)

        post_data = [('access_token', (None, fb_user.access_token)),
                     ('source', (str(uuid4()) + '.' + mime_type.split('/')[1], image_file)),
                     ('caption', (None, fields['message'])),
                     ('message', (None, fields['message']))]

        try:
            fb_request_url = Config.get("API_BASE_URI") + "/{}/photos".format(fb_user.username)
            resp = requests.post(fb_request_url, files=post_data)

            if resp.ok and "post_id" in resp.json():
                log.info(_("A new Post with ID {} published!".format(resp.json()['post_id'])))
            else:
                raise Exception
        except Exception:
            pass
            log.error(_("A failure occurred while posting on Facebook : "
                        "called with data: {}\n response: {}".format(post_data,
                                                                     resp.json()
                                                                     )
                        )
                      )
        image_file.close()
        webhook_data = {
            "time": 0,
            "id": "101915710270588",
            "changed_fields": ["statuses"],
            "uid": fb_user.username
        }
        self.fire_trigger(webhook_data)

    def new_video(self, fb_user, fields):
        if 'message' not in fields:
            fields['message'] = ''
        if 'title' not in fields:
            fields['title'] = ''

        video_file = fields['video']
        video_file.seek(0)
        mime_type = magic.from_buffer(video_file.read(), mime=True)
        video_file.seek(0)

        post_data = [('access_token', (None, fb_user.access_token)),
                     ('source', (str(uuid4()) + '.' + mime_type.split('/')[1], video_file)),
                     ('message', (None, fields['message']))]

        try:
            fb_request_url = Config.get("API_BASE_URI_VIDEO") + "/me/videos"
            resp = requests.post(fb_request_url, files=post_data)
        except Exception:
            pass
            log.error(_("A failure occurred while posting on Facebook : "
                        "called with data: {}".format(post_data)))
        video_file.close()

    def user_is_connected(self, user):

        if FacebookAccount.objects.filter(user=user).count() > 0:
            return ChannelStateForUser.connected
        else:
            return ChannelStateForUser.initial

    @staticmethod
    def _replace_text_inputs(payload, inputs):
        outs = {}
        for key in inputs:
            val = inputs[key]
            if type(val) is str:
                if val.find("%message%") > -1:
                    try:
                        val = val.replace("%message%",
                                          payload["message"])
                    except:
                        pass
                if val.find("%link%") > -1:
                    try:
                        val = val.replace("%link%",
                                          payload["link"])
                    except:
                        pass
                if val.find("%permalink_url%") > -1:
                    try:
                        val = val.replace("%permalink_url%",
                                          payload["permalink_url"])
                    except:
                        pass
                if val.find("%description%") > -1:
                    try:
                        val = val.replace("%description%",
                                          payload["description"])
                    except:
                        pass
            outs[key] = val
        return outs

    @staticmethod
    def _replace_image_inputs(payload, inputs):
        outs = {}
        for key in inputs:
            val = inputs[key]
            if val.find("%image_standard%") > -1:
                try:
                    val = core.utils.download_file(payload["full_picture"])
                except:
                    pass
            elif val.find("%image_low%") > -1:
                try:
                    val = core.utils.download_file(payload["picture"])
                except:
                    pass
            elif val.find("%video%") > -1:
                try:
                    val = core.utils.download_file(payload["video"])
                except:
                    pass
            outs[key] = val
        return outs

    def _build_absolute_uri(self, alias):
        domain_base = Config.get("DOMAIN_BASE")

        if domain_base is "":
            log.warning("Facebook Config DOMAIN_BASE was accessed before set")

        return domain_base + reverse(alias)

    def _getFeeds(self, user, time, fields=None):
        returnvalue = []
        data = {
            'access_token': user.access_token,
            'fields': fields,
            'limit': 1,
        }
        fb_request_url = Config.get("API_BASE_URI") + "/me/feed"
        fb_user_last_post_id = user.last_post_id
        fb_user_last_post_time = user.last_post_time
        try:
            resp = requests.get(fb_request_url, params=data)
            break_loop = False
            while resp.ok and not break_loop:
                for feed in resp.json()['data']:
                    log.debug(feed)
                    if feed['id'] == user.last_post_id \
                            or parse_datetime(feed['created_time']) <= user.last_post_time \
                            or feed['id'] == fb_user_last_post_id:
                        break_loop = True
                        break
                    returnvalue.append(feed)
                    if fb_user_last_post_time < parse_datetime(feed['created_time']):
                        fb_user_last_post_id = feed['id']
                        fb_user_last_post_time = parse_datetime(feed['created_time'])

                    resp = requests.get(resp.json()['paging']['next'], timeout=5.00)
        except requests.exceptions.RequestException:
            pass

        user.last_post_id = fb_user_last_post_id
        user.last_post_time = fb_user_last_post_time
        user.save()
        return returnvalue[::-1]

    @staticmethod
    def _get_payload(feed):
        payload = {}
        if 'description' in feed:
            payload['description'] = feed['description']
        if 'message' in feed:
            payload['message'] = feed['message']
        if 'caption' in feed:
            payload['message'] = feed['caption']
        if 'picture' in feed:
            payload['picture'] = feed['picture']
        if 'full_picture' in feed:
            payload['full_picture'] = feed['full_picture']
        if 'permalink_url' in feed:
            payload['permalink_url'] = feed['permalink_url']
        if 'link' in feed:
            payload['link'] = feed['link']
        if 'source' in feed:
            payload['video'] = feed['source']
        return payload
