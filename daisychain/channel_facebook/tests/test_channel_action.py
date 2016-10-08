import requests
from django.utils.dateparse import parse_datetime
from mock import patch, MagicMock

from channel_facebook.channel import ActionType
from channel_facebook.config import Config
from core.channel import (NotSupportedAction)
from .test_base import FacebookBaseTestCase


class ChannelActionTestCase(FacebookBaseTestCase):
    @patch('channel_facebook.channel.log.error')
    def test_handle_action_with_invalid_user(self, mock_log):
        user_id = -99
        self.channel.handle_action(ActionType.post_new_post, user_id, {})
        mock_log.assert_called_with("Facebook-Action for UID:{} "
                                    "could not found! Ignoring webhook".format(user_id))

    @patch('channel_facebook.channel.FacebookChannel.new_post')
    def test_handle_action_new_post(self, mock_new_post):
        # action_inputs = ActionInput.objects.get_by_natural_key("Facebook", ActionType.post_new_post)
        inputs = {
            'message': 'test'
        }
        self.channel.handle_action(ActionType.post_new_post, self.user.id, inputs)
        mock_new_post.assert_called_with(fb_user=self.facebook_account,
                                         status=inputs['message'])

    @patch('channel_facebook.channel.FacebookChannel.new_picture')
    def test_handle_action_new_photo(self, mock_new_post):
        # action_inputs = ActionInput.objects.get_by_natural_key("Facebook", ActionType.post_new_post)
        inputs = {
            'message': 'test',
            'image': 'http://example.com/test.png'
        }
        self.channel.handle_action(ActionType.post_new_photo, self.user.id, inputs)
        mock_new_post.assert_called_with(fb_user=self.facebook_account,
                                         fields=inputs)

    @patch('channel_facebook.channel.FacebookChannel.new_link')
    def test_handle_action_new_link(self, mock_new_link):
        # action_inputs = ActionInput.objects.get_by_natural_key("Facebook", ActionType.post_new_post)
        inputs = {
            'message': 'test',
            'link': 'http://example.com/'
        }
        self.channel.handle_action(ActionType.post_new_link, self.user.id, inputs)
        mock_new_link.assert_called_with(fb_user=self.facebook_account,
                                         fields=inputs)

    # @patch('channel_facebook.channel.FacebookChannel.delete_post_until')
    # def test_handle_action_delete_post_until(self, mock_delete_post_until):
    #     # action_inputs = ActionInput.objects.get_by_natural_key("Facebook", ActionType.post_new_post)
    #     inputs = {
    #         'date': datetime.now(),
    #     }
    #     self.channel.handle_action(ActionType.delete_posts_until, self.user.id, inputs)
    #     mock_delete_post_until.assert_called_with(fb_user=self.facebook_account,
    #                                               inputs=inputs)

    @patch('channel_facebook.channel.FacebookChannel.new_video')
    def test_handle_action_new_video(self, mock_new_video):
        # action_inputs = ActionInput.objects.get_by_natural_key("Facebook", ActionType.post_new_post)
        inputs = {
            'message': 'testmessage',
            'title': 'testtitle',
            'video': 'http://example.com/testvideo.mp4'
        }
        self.channel.handle_action(ActionType.post_new_video, self.user.id, inputs)
        mock_new_video.assert_called_with(fb_user=self.facebook_account,
                                          fields=inputs)

    def test_handle_action_not_supportet_action(self):
        with self.assertRaises(NotSupportedAction):
            self.channel.handle_action(-99, self.user.id, {})

    @patch('requests.post')
    @patch('channel_facebook.channel.log.error')
    def test_new_post(self, mock_log, mock_post):
        with self.assertRaises(ValueError):
            self.channel.new_post(self.facebook_account, {})

        inputs = {
            'message': 'test',
            'access_token': self.facebook_account.access_token
        }

        mock_post.return_value = MagicMock()
        mock_post.return_value.json = MagicMock()
        mock_post.return_value.json.return_value = {'id': '1337'}
        mock_post.return_value.ok = True

        fb_request_url = Config.get("API_BASE_URI") + "/me/feed"

        self.channel.new_post(self.facebook_account, inputs['message'])
        mock_post.assert_called_with(fb_request_url, data=inputs)

        mock_post.return_value.ok = False
        self.channel.new_post(self.facebook_account, inputs['message'])
        mock_log.assert_called_once()

    @patch('requests.post')
    @patch('channel_facebook.channel.log.error')
    def test_new_link(self, mock_log, mock_post):
        inputs = {
            'message': 'http://www.example.com',
            'access_token': self.facebook_account.access_token
        }

        mock_post.return_value = MagicMock()
        mock_post.return_value.json = MagicMock()
        mock_post.return_value.json.return_value = {'id': '1337'}
        mock_post.return_value.ok = True

        fb_request_url = Config.get("API_BASE_URI") + "/me/feed"

        self.channel.new_link(self.facebook_account, inputs)
        mock_post.assert_called_with(fb_request_url, data=inputs)

        mock_post.return_value.ok = False
        self.channel.new_link(self.facebook_account, inputs)
        mock_log.assert_called_once()

    @patch('requests.post')
    @patch('channel_facebook.channel.log.error')
    def test_new_picture(self, mock_log, mock_post):
        inputs = {
            'message': 'http://www.example.com',
            'access_token': self.facebook_account.access_token,
            'image': open('channel_facebook/static/channel_facebook/fb_logo.png', 'r+b')
        }

        mock_post.return_value = MagicMock()
        mock_post.return_value.json = MagicMock()
        mock_post.return_value.json.return_value = {'post_id': '1337'}
        mock_post.return_value.ok = True

        fb_request_url = Config.get("API_BASE_URI") + "/me/feed"

        mock_log.assert_not_called()

        mock_post.return_value.ok = False
        self.channel.new_picture(self.facebook_account, inputs)
        mock_log.assert_called_once()

    @patch('requests.post')
    @patch('channel_facebook.channel.log.error')
    def test_new_video(self, mock_log, mock_post):
        inputs = {
            'message': 'http://www.example.com',
            'access_token': self.facebook_account.access_token,
            'video': open('channel_facebook/static/channel_facebook/fb_logo.png', 'r+b')
        }

        mock_post.return_value = MagicMock()
        mock_post.return_value.json = MagicMock()
        mock_post.return_value.json.return_value = {'post_id': '1337'}
        mock_post.return_value.ok = True

        fb_request_url = Config.get("API_BASE_URI") + "/me/feed"

        self.channel.new_video(self.facebook_account, inputs)
        mock_log.assert_not_called()

        inputs = {
            'access_token': self.facebook_account.access_token,
            'video': open('channel_facebook/static/channel_facebook/fb_logo.png', 'r+b')
        }
        mock_post.side_effect = ValueError()
        mock_post.return_value.ok = False
        self.channel.new_video(self.facebook_account, inputs)
        mock_log.assert_called_once()

    @patch('requests.get')
    def test_get_feeds(self, mock_get):
        fb_response_fields = 'message,actions,full_picture,picture,from,created_time,' \
                             'link,permalink_url,type,description,source,object_id'

        data = {'paging': {'next': 'https://graph.facebook.com/v2.7/1ZD',
                           'previous': 'https://graph.facebook.com/v2.7/101'
                           },
                'data': [{'message': 'Tet',
                          'id': '101915710270588_133598340435658',
                          'created_time': '2016-10-04T15:26:44+0000',
                          }]
                }

        mock_get.return_value = MagicMock()
        mock_get.return_value.json = MagicMock()
        mock_get.return_value.json.return_value = data
        mock_get.return_value.ok = True
        self.facebook_account.last_post_id = 1
        self.facebook_account.last_post_time = parse_datetime('2016-01-04T15:26:44+0000')
        self.facebook_account.save()
        resp = self.channel._getFeeds(self.facebook_account, None, fb_response_fields)
        self.assertEqual(data['data'], resp)

        mock_get.side_effect = requests.exceptions.ConnectTimeout
        resp = self.channel._getFeeds(self.facebook_account, None, fb_response_fields)
        self.assertEqual([], resp)
