from twython import Twython
from twython.exceptions import TwythonError
from django.contrib.auth.models import User
import logging

from channel_twitter.models import TwitterAccount
from channel_twitter.config import (CONSUMER_KEY, CONSUMER_SECRET, POST_IMAGE,
                                    POST_STATUS, SEND_MESSAGE,
                                    UPDATE_PROFILE_IMAGE)
from core.channel import (Channel, NotSupportedTrigger, NotSupportedAction,
                          ChannelStateForUser)


log = logging.getLogger('channel')


class TwitterChannel(Channel):

    def __init__(self):
        pass

    def create_api(self, user):
        """
        creates an instance of the twython api
        """
        twitter_account = user.twitteraccount
        return Twython(CONSUMER_KEY,
                       CONSUMER_SECRET,
                       twitter_account.access_token,
                       twitter_account.access_secret)

    def post_tweet_from_text(self, user, status):
        """
        Post a tweet to the users timeline.

        Args:
            user: The user on whose behalf the tweet is posted.
            status(str): Status to be posted.
        Raises:
            ValueError: If the length of the given status string exceeds 140
                        characters.
            TypeError: If status is not a string.
        """
        if not type(status) is str:
            raise TypeError("Should only be called with a string.")

        if len(status) > 140:
            raise ValueError("Twitter status should be at most 140 characters.")

        twitter_api = self.create_api(user)

        try:
            twitter_api.update_status(status=status)
        except TwythonError as e:
            log.error(e)
        except:
            log.error("Unexpected error posting twitter status")

    def post_image(self, user, image, status=None):
        """
        Post an image to twitter timeline.

        Args:
            user: The User on whose behalf the tweet is posted.
            image: The image to be posted.
            status: Status to be posted (optional)
        Returns:
            None
        Raises:
            ValueError: If the length of the given status string exceeds 140
                        characters.
            TypeError: If status is not a string.
        """
        if status:
            if not type(status) is str:
                raise TypeError("Should only be called with a string.")

            if len(status) > 140:
                raise ValueError("Status should be at most 140 characters.")

        twitter_api = self.create_api(user)

        try:
            media_response = twitter_api.upload_media(media=image)
        except TwythonError as e:
            log.error(e)
            return
        except:
            log.error("Unexpected error during image upload to twitter")
            return

        try:
            twitter_api.update_status(media_ids=[media_response['media_id']],
                                  status=status)
        except TwythonError as e:
            log.error(e)
        except:
            log.error("Unexpected error posting status with image to twitter")

    def update_profile_image(self, user, image):
        """
        Update profile image.
        """
        twitter_api = self.create_api(user)
        try:
            twitter_api.update_profile_image(image=image)
        except TwythonError as e:
            log.error(e)

    def send_message(self, user, screen_name, text):
        twitter_api = self.create_api(user)
        try:
            twitter_api.send_direct_message(screen_name=screen_name, text=text)
        except TwythonError as e:
            log.error(e)
        except:
            log.error("Unexpected error sending a twitter message.")

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
            user = User.objects.get(pk=userid)
        except User.DoesNotExist:
            log.error("User does not exist")
            return

        # initiate action based on the given action type
        if action_type == POST_STATUS:
            self.post_tweet_from_text(user=user, status=inputs['status'])
        elif action_type == POST_IMAGE:
            if inputs['status']:
                self.post_image(user=user,
                                image=inputs['image'],
                                status=inputs['status'])
            else:
                # post without status
                self.post_image(user=user, image=inputs['image'])
        elif action_type == UPDATE_PROFILE_IMAGE:
            self.update_profile_image(user=user, image=inputs['image'])
        elif action_type == SEND_MESSAGE:
            self.send_message(user=user,
                              screen_name=inputs['screen_name'],
                              text=inputs['text'])
        else:
            raise NotSupportedAction(
                "This action is not supported by the Twitter channel.")

    def fill_recipe_mappings(self, trigger_type, userid,
                             payload, conditions, mappings):
        # twitter does not deliver any triggers yet
        raise NotSupportedTrigger(
                  "The Twitter channel does not offer any triggers currently.")

    def user_is_connected(self, user):
        """
        Check whether the user is connected, i.e. whether the oauth handshake
        has taken place and a TwitterAccount has been saved.

        Args:
            user: The user that is checked.
        Returns:
            ChannelStateForUser.connected if user is authenticated,
            ChannelStateForUser.initial otherwise.
        """
        if TwitterAccount.objects.filter(user=user).count() > 0:
            return ChannelStateForUser.connected
        else:
            return ChannelStateForUser.initial
