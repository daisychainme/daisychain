from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from mock import patch
import os
from twython.exceptions import TwythonError

from core.channel import NotSupportedTrigger
from core.channel import NotSupportedAction
from channel_twitter.channel import TwitterChannel
from channel_twitter.models import TwitterAccount


"""
    Test cases for the twitter channel.
"""

AUTHENTICATION_TOKENS = {
                        'oauth_token': 'testingtoken',
                        'oauth_token_secret': 'testing_secret',
                        'auth_url': 'https://api.twitter.com/placeholder'
                        }

AUTHORIZED_TOKENS = {
                     'oauth_token': 'testing_auth_token',
                     'oauth_token_secret': 'testing_auth_secret'
                    }

channel = TwitterChannel()


def make_twitter_account(user):
    twitter_account = TwitterAccount()
    twitter_account.user = user
    twitter_account.access_token = AUTHORIZED_TOKENS['oauth_token']
    twitter_account.access_secret = AUTHORIZED_TOKENS['oauth_token_secret']
    twitter_account.save()


class BaseTestCase(TestCase):

    def create_user(self):
        user = User.objects.create_user('Superuser',
            'superuser@super.com',
            'Password')
        user.save()
        return user

    def setUp(self):
        self.client = Client()
        self.user = self.create_user()
        self.user.save()


class TestStartAuthenticationView(BaseTestCase):

    @patch('twython.Twython.get_authentication_tokens')
    def test_twitter_oauth_with_logged_in_user(self,
                                               mock_get_authentication_tokens):
        mock_get_authentication_tokens.return_value = AUTHENTICATION_TOKENS
        self.client.force_login(self.user)
        response = self.client.get(reverse('twitter:connect'))
        # assert redirection
        self.assertEqual(response.status_code, 302)


    def test_twitter_oauth_without_login(self):
        response = self.client.get(reverse('twitter:connect'))
        # user should be redirected to login page if they are not logged in
        self.assertRedirects(response,
                             '/accounts/login/?next=/twitter/oauth-start/')


class TestCallbackView(BaseTestCase):

    @patch('twython.Twython.get_authorized_tokens')
    def test_callback_with_valid_user(self,
                                      mock_get_authorized_tokens):
        self.client.force_login(self.user)
        session = self.client.session
        session['twitter_request_token'] = AUTHENTICATION_TOKENS
        session.save()

        mock_get_authorized_tokens.return_value = AUTHORIZED_TOKENS

        response = self.client.get(reverse('twitter:callback'),
                                   {'oauth_verifier': 'test_verifier'})
        # user should be redirected, twitter profile is created and stored
        #self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/?status=success',
                             status_code=302, target_status_code=302)
        twitter_account = TwitterAccount.objects.get(user=self.user)
        self.assertNotEqual(twitter_account, None)

    def test_callback_without_login(self):
        tokens = {
                  'oauth_token': 'testingtoken',
                  'oauth_token_secret': 'testing_secret'
                 }
        session = self.client.session
        session['twitter_request_token'] = tokens
        session.save()
        response = self.client.get(reverse('twitter:callback'))
        self.assertRedirects(response, '/accounts/login/')

    def test_callback_without_verifier(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['twitter_request_token'] = AUTHENTICATION_TOKENS
        session.save()
        response = self.client.get(reverse('twitter:callback'))
        self.assertRedirects(response, '/?status=error',
                             status_code=302, target_status_code=302)

    def test_callback_without_verifier_with_next_url(self):
        self.client.force_login(self.user)
        session = self.client.session
        session['twitter_request_token'] = AUTHENTICATION_TOKENS
        session['twitter_next_url'] = '/home/'
        session.save()
        response = self.client.get(reverse('twitter:callback'))
        self.assertRedirects(response, '/home/?status=error',
                             status_code=302, target_status_code=200)

    @patch('twython.Twython.get_authentication_tokens')
    @patch('twython.Twython.get_authorized_tokens')
    def test_callback_with_previous_oauth_start(self,
                                                mock_get_authorized_tokens,
                                                mock_get_authentication_tokens):
        mock_get_authentication_tokens.return_value = AUTHENTICATION_TOKENS
        self.client.force_login(self.user)
        response = self.client.get(reverse('twitter:connect'))
        # assert redirection
        self.assertEqual(response.status_code, 302)

        mock_get_authorized_tokens.return_value = AUTHORIZED_TOKENS

        response = self.client.get(reverse('twitter:callback'),
                                   {'oauth_verifier': 'test_verifier'})
        # user should be redirected, twitter profile is created and stored
        self.assertEqual(response.status_code, 302)
        twitter_account = TwitterAccount.objects.get(user=self.user)
        self.assertNotEqual(twitter_account, None)


upload_response = {'media_id': 'test_id'}
this_dir = os.path.dirname(__file__) # get current dir
img_path = os.path.join(this_dir, 'testdata/test.jpg')
img_path_too_large = os.path.join(this_dir, 'testdata/test_large.jpg')

class TestTwitterChannel(BaseTestCase):
    """
        Tests for the twitter channel.
    """

    def setUp(self):
        super().setUp()
        self.twython_error = TwythonError(msg="test")


    @patch('twython.Twython.update_status')
    def test_post_tweet_should_result_in_tweet(self, mock_update_status):
        make_twitter_account(self.user)
        status = "daisies are my favourite flower."
        channel.post_tweet_from_text(self.user, status)
        mock_update_status.assert_called_once_with(status=status)

    @patch('twython.Twython.update_status')
    @patch('logging.Logger.error')
    def test_post_tweet_raising_twython_error(self,
                                              mock_error,
                                              mock_update_status):
        make_twitter_account(self.user)
        status = "daisies are my favourite flower."
        twython_error = TwythonError(msg="test")
        mock_update_status.side_effect = twython_error
        channel.post_tweet_from_text(self.user, status)
        mock_error.assert_called_once_with(twython_error)

    @patch('twython.Twython.update_status')
    @patch('logging.Logger.error')
    def test_post_tweet_raising_unexpected_exception(self,
                                                     mock_error,
                                                     mock_update_status):
        make_twitter_account(self.user)
        status = "daisies are my favourite flower."
        mock_update_status.side_effect = Exception("test")
        channel.post_tweet_from_text(self.user, status)
        mock_error.assert_called_once()

    def test_post_tweet_without_twitter_account(self):
        """
            if no twitter account is saved the twitter api should not be called
            and a meainingful error message should be logged.
        """
        status = "this flower has gone foul."

        self.assertRaises(TwitterAccount.DoesNotExist,
                          channel.post_tweet_from_text,
                          user=self.user,
                          status=status)

    def test_post_tweet_with_more_than_140_characters(self):
        """
            if no twitter account is saved the twitter api should not be called
            and a meainingful error message should be logged.
        """
        make_twitter_account(self.user)
        status =  """
                This flower has gone foul. And this tweet is far too long for
                twitter to except it. Far to long. Yes, that's right, it is
                too long. There are no jokes here. Just a text that is too long
                to tweet. Move along!
                """
        self.assertRaises(ValueError,
                         channel.post_tweet_from_text,
                         user=self.user,
                         status=status)

    def test_post_tweet_with_wrong_type(self):
        self.assertRaises(TypeError, channel.post_tweet_from_text,
                          user=self.user, status=1234)

    @patch('twython.Twython.upload_media')
    @patch('twython.Twython.update_status')
    def test_post_image_should_upload_and_post(self, mock_update_status,
                                               mock_upload_media):
        make_twitter_account(self.user)

        image = open(img_path, 'rb')
        mock_upload_media.return_value = upload_response

        channel.post_image(self.user, image)
        mock_upload_media.assert_called_once_with(media=image)
        mock_update_status.assert_called_once_with(
                                        media_ids=[upload_response['media_id']],
                                        status=None)

    @patch('twython.Twython.upload_media')
    def test_post_image_without_twitter_account(self, mock_upload_media):
        image = open(img_path, 'rb')
        self.assertRaises(TwitterAccount.DoesNotExist, channel.post_image,
                          user=self.user, image=image)

    @patch('twython.Twython.upload_media')
    @patch('logging.Logger.error')
    def test_post_image_raising_twython_error_during_upload(self,
                                                            mock_error,
                                                            mock_upload_media):
        make_twitter_account(self.user)
        mock_upload_media.side_effect = self.twython_error
        channel.post_image(self.user, img_path)
        mock_error.assert_called_once_with(self.twython_error)

    @patch('twython.Twython.upload_media')
    @patch('logging.Logger.error')
    def test_post_image_raising_unexpected_error_during_upload(self,
                                                            mock_error,
                                                            mock_upload_media):
        make_twitter_account(self.user)
        mock_upload_media.side_effect = Exception("test")
        channel.post_image(self.user, img_path)
        mock_error.assert_called_once()

    @patch('twython.Twython.upload_media')
    @patch('twython.Twython.update_status')
    @patch('logging.Logger.error')
    def test_post_image_raising_twython_error(self,
                                              mock_error,
                                              mock_update_status,
                                              mock_upload_media):
        make_twitter_account(self.user)
        image = open(img_path, 'rb')
        mock_upload_media.return_value = upload_response
        mock_update_status.side_effect = self.twython_error
        channel.post_image(self.user, img_path)
        mock_error.assert_called_once_with(self.twython_error)

    @patch('twython.Twython.upload_media')
    @patch('twython.Twython.update_status')
    @patch('logging.Logger.error')
    def test_post_image_raising_unexpected_error(self,
                                              mock_error,
                                              mock_update_status,
                                              mock_upload_media):
        make_twitter_account(self.user)
        image = open(img_path, 'rb')
        mock_upload_media.return_value = upload_response
        mock_update_status.side_effect = Exception("test")
        channel.post_image(self.user, img_path)
        mock_error.assert_called_once()

    @patch('twython.Twython.update_profile_image')
    def test_update_profile_image(self, mock_update_profile_image):
        make_twitter_account(self.user)
        image = open(img_path, 'rb')
        channel.update_profile_image(user=self.user, image=image)
        mock_update_profile_image.assert_called_once_with(image=image)

    @patch('twython.Twython.update_profile_image')
    @patch('logging.Logger.error')
    def test_update_profile_image_raises_twython_exception(self,
                                                   mock_error,
                                                   mock_update_profile_image):
        make_twitter_account(self.user)
        image = open(img_path, 'rb')
        mock_update_profile_image.side_effect = self.twython_error
        channel.update_profile_image(user=self.user, image=image)
        mock_error.assert_called_once_with(self.twython_error)


    @patch('twython.Twython.send_direct_message')
    def test_send_message(self, mock_send_direct_message):
        make_twitter_account(self.user)
        screen_name = "Frodo"
        text = "All we have to decide is what to do with the time that is given us"
        channel.send_message(user=self.user, screen_name=screen_name, text=text)
        mock_send_direct_message.assert_called_once_with(screen_name=screen_name,
                                                  text=text)

    @patch('logging.Logger.error')
    @patch('twython.Twython.send_direct_message')
    def test_send_message_with_Twython_exception(self,
                                                 mock_send_direct_message,
                                                 mock_error):
        make_twitter_account(self.user)
        screen_name = "Frodo"
        text = "All we have to decide is what to do with the time that is given us"
        twython_error = TwythonError(msg="test")
        mock_send_direct_message.side_effect = twython_error
        channel.send_message(user=self.user, screen_name=screen_name, text=text)
        mock_error.assert_called_once_with(twython_error)

    @patch('logging.Logger.error')
    @patch('twython.Twython.send_direct_message')
    def test_send_message_with_other_exception(self,
                                                 mock_send_direct_message,
                                                 mock_error):
        make_twitter_account(self.user)
        screen_name = "Frodo"
        text = "All we have to decide is what to do with the time that is given us"
        mock_send_direct_message.side_effect = Exception("test")
        channel.send_message(user=self.user, screen_name=screen_name, text=text)
        mock_error.assert_called_once()


    @patch('channel_twitter.channel.TwitterChannel.post_tweet_from_text')
    def test_handle_action_with_post_status_and_text(self,
                                                     mock_post_tweet_from_text):
        status =  "daisies are my favourite flower."
        inputs = {}
        inputs['status'] = status
        channel.handle_action(action_type=100,
                              userid=self.user.id,
                              inputs=inputs)
        mock_post_tweet_from_text.assert_called_once_with(user=self.user,
                                                          status=status)

    @patch('channel_twitter.channel.TwitterChannel.post_image')
    def test_handle_action_with_post_image(self, mock_post_image):
        image = open(img_path, 'rb')
        inputs = {}
        inputs['image'] = image
        inputs['status'] = ''
        channel.handle_action(userid=self.user.id,
                           action_type=200,
                           inputs=inputs)
        mock_post_image.assert_called_once_with(user=self.user,
                                                image=image)

    @patch('channel_twitter.channel.TwitterChannel.post_image')
    def test_handle_action_with_post_image_and_text(self, mock_post_image):
        image = open(img_path, 'rb')
        status = "daisies are my favourite flower"
        inputs = {}
        inputs['image'] = image
        inputs['status'] = status
        channel.handle_action(userid=self.user.id,
                           action_type=200,
                           inputs=inputs)
        mock_post_image.assert_called_once_with(user=self.user,
                                                image=image,
                                                status=status)

    @patch('channel_twitter.channel.TwitterChannel.update_profile_image')
    def test_handle_action_update_profile_image(self,
                                                mock_update_profile_image):
        image = open(img_path, 'rb')
        inputs = {}
        inputs['image'] = image
        channel.handle_action(userid=self.user.id,
                              action_type=300,
                              inputs=inputs)
        mock_update_profile_image.assert_called_once_with(user=self.user,
                                                          image=image)


    def test_fill_recipe_mappings_raises_exception(self):
        self.assertRaises(NotSupportedTrigger,
                          channel.fill_recipe_mappings,
                          trigger_type=42,
                          userid=42,
                          payload={},
                          conditions={},
                          mappings={})

    def test_handle_action_not_supported(self):
        self.assertRaises(NotSupportedAction,
                          channel.handle_action,
                          action_type=42,
                          userid=self.user.id,
                          inputs={})

    @patch('logging.Logger.error')
    def test_handle_action_with_incorrect_user_id(self,
                                                  mock_error):
        channel.handle_action(action_type=100,
                              userid=-42,
                              inputs={})
        mock_error.assert_called_once()

    @patch('channel_twitter.channel.TwitterChannel.send_message')
    def test_handle_action_send_message(self, mock_send_message):
        name = 'gandalf'
        text = 'have you seen any ents lately?'
        inputs = {'screen_name': name, 'text': text}
        channel.handle_action(action_type=400,
                              userid=self.user.id,
                              inputs=inputs)
        mock_send_message.assert_called_once_with(user=self.user,
                                                  screen_name=name,
                                                  text=text)

    def test_post_image_with_status_exceeding_140_characters(self):
        status = """
            This flower has gone foul. And this tweet is far too long for
            twitter to except it. Far to long. Yes, that's right, it is
            too long. There are no jokes here. Just a text that is too long
            to tweet. Move along!
            """
        with self.assertRaises(ValueError):
            channel.post_image(user=self.user, image=None, status=status)

    def test_post_image_with_status_not_string(self):
        with self.assertRaises(TypeError):
            channel.post_image(user=self.user, image=None, status=42)
