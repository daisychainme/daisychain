from mock import patch

from channel_facebook.channel import TriggerType
from core.channel import (NotSupportedTrigger, NotSupportedAction, ConditionNotMet)
from core.models import Channel, Trigger
from .test_base import FacebookBaseTestCase


class ChannelTestCase(FacebookBaseTestCase):
    def test_fire_trigger_post(self):
        get_data = [{
            'message': 'Testmessage',
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=1234',
            'created_time': '2016-09-14T14:27:06+0000',
            'id': '101915710270588_102025766926249',
            'type': 'status'
        }]

        payload = {
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=1234',
            'message': 'Testmessage'
        }

        with patch('channel_facebook.channel.FacebookChannel._getFeeds') as mock_get_feeds, \
                patch('core.core.Core.handle_trigger') as mock_handle_trigger:
            trigger_type = TriggerType.new_post
            mock_get_feeds.return_value = get_data
            self.channel.fire_trigger(self.webhook_data)
            mock_get_feeds.assert_called_once_with(fields=self.fields,
                                                   user=self.facebook_account,
                                                   time=self.time)
            mock_handle_trigger.assert_called_once_with(channel_name=self.channel_name,
                                                        trigger_type=trigger_type,
                                                        userid=self.facebook_account.user_id,
                                                        payload=payload)

    def test_fire_trigger_photo(self):
        get_data = [{
            'id': '101915710270588_101933616935464',
            'message': 'testmessage',
            'link': 'https://www.facebook.com/photo.php?fbid=101933566935469',
            'created_time': '2016-09-14T13:08:39+0000',
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=1019&id=100',
            'full_picture': 'https://scontent.xx.fbcdn.net/1_n.jpg',
            'picture': 'https://scontent.xx.fbcdn.net/1_n.jpg',
            'type': 'photo'
        }]

        payload = {
            'message': 'testmessage',
            'link': 'https://www.facebook.com/photo.php?fbid=101933566935469',
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=1019&id=100',
            'full_picture': 'https://scontent.xx.fbcdn.net/1_n.jpg',
            'picture': 'https://scontent.xx.fbcdn.net/1_n.jpg'
        }

        with patch('channel_facebook.channel.FacebookChannel._getFeeds') as mock_get_feeds, \
                patch('core.core.Core.handle_trigger') as mock_handle_trigger:
            trigger_type = TriggerType.new_photo
            mock_get_feeds.return_value = get_data
            self.channel.fire_trigger(self.webhook_data)
            mock_get_feeds.assert_called_once_with(fields=self.fields,
                                                   user=self.facebook_account,
                                                   time=self.time)
            mock_handle_trigger.assert_called_once_with(channel_name=self.channel_name,
                                                        trigger_type=trigger_type,
                                                        userid=self.facebook_account.user_id,
                                                        payload=payload)

    def test_fire_trigger_photo_with_hashtag(self):
        get_data = [{
            'id': '101915710270588_101933616935464',
            'message': '#me',
            'link': 'https://www.facebook.com/photo.php?fbid=101933566935469',
            'created_time': '2016-09-14T13:08:39+0000',
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=1019&id=100',
            'full_picture': 'https://scontent.xx.fbcdn.net/1_n.jpg',
            'picture': 'https://scontent.xx.fbcdn.net/1_n.jpg',
            'type': 'photo'}]

        payload = {
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=1019&id=100',
            'message': '#me', 'full_picture': 'https://scontent.xx.fbcdn.net/1_n.jpg',
            'picture': 'https://scontent.xx.fbcdn.net/1_n.jpg',
            'link': 'https://www.facebook.com/photo.php?fbid=101933566935469'
        }

        with patch('channel_facebook.channel.FacebookChannel._getFeeds') as mock_get_feeds, \
                patch('core.core.Core.handle_trigger') as mock_handle_trigger:
            trigger_type = TriggerType.new_photo_with_hashtag
            mock_get_feeds.return_value = get_data
            self.channel.fire_trigger(self.webhook_data)
            mock_get_feeds.assert_called_once_with(fields=self.fields,
                                                   user=self.facebook_account,
                                                   time=self.time)

            mock_handle_trigger.assert_called_with(channel_name=self.channel_name,
                                                   trigger_type=trigger_type,
                                                   userid=self.facebook_account.user_id,
                                                   payload=payload)

    def test_fire_trigger_link(self):
        get_data = [{
            'link': 'http://daisychain.me/',
            'id': '101915710270588_102045486924277',
            'message': 'testmessage',
            'created_time': '2016-09-14T14:45:28+0000',
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=102',
            'type': 'link'
        }]

        payload = {
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=102',
            'link': 'http://daisychain.me/',
            'message': 'testmessage'
        }

        with patch('channel_facebook.channel.FacebookChannel._getFeeds') as mock_get_feeds, \
                patch('core.core.Core.handle_trigger') as mock_handle_trigger:
            trigger_type = TriggerType.new_link
            mock_get_feeds.return_value = get_data
            self.channel.fire_trigger(self.webhook_data)
            mock_get_feeds.assert_called_once_with(fields=self.fields,
                                                   user=self.facebook_account,
                                                   time=self.time)
            mock_handle_trigger.assert_called_once_with(channel_name=self.channel_name,
                                                        trigger_type=trigger_type,
                                                        userid=self.facebook_account.user_id,
                                                        payload=payload)

    def test_fire_trigger_video(self):
        get_data = [{
            'link': 'https://www.facebook.com/101915710270588/videos/102056993589793',
            'id': '101915710270588_102057203589772',
            'message': 'Video',
            'created_time': '2016-09-14T14:48:18+0000',
            'permalink_url': 'https://www.facebook.com/permalink.php',
            'type': 'video',
            'picture': 'https://scontent.xx.fbcdn.net/v/t15.0-10/s130x130/14356708_n.jpg?',
            'full_picture': 'https://scontent.xx.fbcdn.net/v/t15.0-10/s720x720/1435_n.jpg'
        }]

        payload = {'message': 'Video',
                   'link': 'https://www.facebook.com/101915710270588/videos/102056993589793',
                   'full_picture': 'https://scontent.xx.fbcdn.net/v/t15.0-10/s720x720/1435_n.jpg',
                   'permalink_url': 'https://www.facebook.com/permalink.php',
                   'picture': 'https://scontent.xx.fbcdn.net/v/t15.0-10/s130x130/14356708_n.jpg?'}

        with patch('channel_facebook.channel.FacebookChannel._getFeeds') as mock_get_feeds, \
                patch('core.core.Core.handle_trigger') as mock_handle_trigger:
            trigger_type = TriggerType.new_video
            mock_get_feeds.return_value = get_data
            self.channel.fire_trigger(self.webhook_data)
            mock_get_feeds.assert_called_once_with(fields=self.fields,
                                                   user=self.facebook_account,
                                                   time=self.time)
            mock_handle_trigger.assert_called_once_with(channel_name=self.channel_name,
                                                        trigger_type=trigger_type,
                                                        userid=self.facebook_account.user_id,
                                                        payload=payload)

    def test_fire_trigger_invalid(self):
        invalid_webhook_data = {
            "time": self.time,
            "id": "101915710270588",
            "changed_fields": ["feed"],
            "uid": "101915710270588"
        }

        with self.assertRaises(NotSupportedTrigger):
            self.channel.fire_trigger(invalid_webhook_data)

    @patch('channel_facebook.channel.FacebookChannel._getFeeds')
    def test_fire_trigger_with_invalid_user(self, mock_getFeeds):
        invalid_webhook_data = {
            "time": self.time,
            "id": "101915710270588",
            "changed_fields": ["statuses"],
            "uid": "invaliduser2"
        }

        self.channel.fire_trigger(invalid_webhook_data)
        mock_getFeeds.assert_not_called()

    def test_fire_trigger_with_invalid_channel_object(self):
        get_data = [{
            'message': 'Testmessage',
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=1234',
            'created_time': '2016-09-14T14:27:06+0000',
            'id': '101915710270588_102025766926249',
            'type': 'status'
        }]

        payload = {
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=1234',
            'message': 'Testmessage'
        }

        with patch('channel_facebook.channel.FacebookChannel._getFeeds') as mock_get_feeds, \
                patch('core.models.Channel.objects.get') as mock_get_Channel, \
                patch('core.core.Core.handle_trigger') as mock_handle_trigger:
            mock_get_feeds.return_value = get_data
            mock_get_Channel.side_effect = Channel.DoesNotExist

            self.channel.fire_trigger(self.webhook_data)
            mock_get_feeds.assert_called_once()
            mock_handle_trigger.assert_not_called()

    def test_fill_recipe_mappings_with_valid_trigger(self):
        payload = {
            'message': 'testmessage #me',
            'link': 'https://www.facebook.com/photo.php?fbid=101933566935469',
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=1019&id=100',
            'full_picture': 'https://scontent.xx.fbcdn.net/1_n.jpg',
            'picture': 'https://scontent.xx.fbcdn.net/1_n.jpg'
        }

        conditions = {'hashtag': '#me'}
        with patch('channel_facebook.channel.FacebookChannel._fill_mappings_for_new_entry') as mock_replace_mappings:
            self.channel.fill_recipe_mappings(trigger_type=TriggerType.new_photo,
                                              userid=self.user.id,
                                              payload=payload,
                                              conditions=self.conditions,
                                              mappings={})

            mock_replace_mappings.assert_called_once_with(inputs={},
                                                          payload=payload)
        with patch(
                'channel_facebook.channel.FacebookChannel._fill_mappings_for_new_entry_with_hashtags') as mock_replace_mappings:
            self.channel.fill_recipe_mappings(trigger_type=TriggerType.new_photo_with_hashtag,
                                              userid=self.user.id,
                                              payload=payload,
                                              conditions=self.conditions,
                                              mappings={})

            mock_replace_mappings.assert_called_once_with(inputs={},
                                                          payload=payload,
                                                          conditions=conditions)

    def test_get_trigger_types_with_notSupportedTrigger(self):
        data = {'type': 'notSupported'}
        with self.assertRaises(NotSupportedTrigger):
            self.channel._get_trigger_types(data)

    @patch('channel_facebook.channel.FacebookChannel._fill_mappings_for_new_entry')
    def test_fill_recipe_mappings_with_ínvalid_trigger(self,
                                                       mock_replace_mappings):
        payload = {
            'message': 'testmessage',
            'link': 'https://www.facebook.com/photo.php?fbid=101933566935469',
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=1019&id=100',
            'full_picture': 'https://scontent.xx.fbcdn.net/1_n.jpg',
            'picture': 'https://scontent.xx.fbcdn.net/1_n.jpg'
        }

        self.channel.fill_recipe_mappings(trigger_type=-42,
                                              userid=self.user.id,
                                              payload=payload,
                                              conditions=self.conditions,
                                              mappings={})
        self.assertTrue(mock_replace_mappings.called)

    @patch('channel_facebook.channel.FacebookChannel._fill_mappings_for_new_entry')
    def test_fill_mappings_for_new_entry_with_hashtags_without_hashtag(self,
                                                                       mock_replace_mappings):
        payload = {
            'message': 'testmessage',
            'link': 'https://www.facebook.com/photo.php?fbid=101933566935469',
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=1019&id=100',
            'full_picture': 'https://scontent.xx.fbcdn.net/1_n.jpg',
            'picture': 'https://scontent.xx.fbcdn.net/1_n.jpg'
        }
        with self.assertRaises(ConditionNotMet):
            self.channel.fill_recipe_mappings(trigger_type=TriggerType.new_photo_with_hashtag,
                                              userid=self.user.id,
                                              payload=payload,
                                              conditions={},
                                              mappings={})
        self.assertFalse(mock_replace_mappings.called)

    @patch('channel_facebook.channel.FacebookChannel._fill_mappings_for_new_entry')
    def test_fill_mappings_for_new_entry_with_hashtags_not_matching_hashtag(self,
                                                                            mock_replace_mappings):
        payload = {
            'message': 'testmessage #falseHashtag',
            'link': 'https://www.facebook.com/photo.php?fbid=101933566935469',
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=1019&id=100',
            'full_picture': 'https://scontent.xx.fbcdn.net/1_n.jpg',
            'picture': 'https://scontent.xx.fbcdn.net/1_n.jpg'
        }
        with self.assertRaises(ConditionNotMet):
            self.channel.fill_recipe_mappings(trigger_type=TriggerType.new_photo_with_hashtag,
                                              userid=self.user.id,
                                              payload=payload,
                                              conditions=self.conditions,
                                              mappings={})
        self.assertFalse(mock_replace_mappings.called)

    @patch('channel_facebook.channel.FacebookChannel._fill_mappings_for_new_entry')
    def test_fill_mappings_for_new_entry_with_hashtags_without_hash(self,
                                                                    mock_replace_mappings):
        payload = {
            'message': 'testmessage #me',
            'link': 'https://www.facebook.com/photo.php?fbid=101933566935469',
            'permalink_url': 'https://www.facebook.com/permalink.php?story_fbid=1019&id=100',
            'full_picture': 'https://scontent.xx.fbcdn.net/1_n.jpg',
            'picture': 'https://scontent.xx.fbcdn.net/1_n.jpg'
        }
        conditions = {'hashtag': 'me'}
        self.channel.fill_recipe_mappings(trigger_type=TriggerType.new_photo_with_hashtag,
                                          userid=self.user.id,
                                          payload=payload,
                                          conditions=conditions,
                                          mappings={})
        mock_replace_mappings.assert_called_once()

    def test_replace_mappings(self):
        def mock_downloadfile(input):
            return input

        payload = {
            'message': 'testmessage',
            'description': 'a test description',
            'link': 'https://www.facebook.com/photo.php?fbid=101933566935469',
            'permalink_url': 'https://www.facebook.com/',
            'full_picture': 'https://scontent.xx.fbcdn.net/1_n.jpg',
            'picture': 'https://scontent.xx.fbcdn.net/1_n.jpg'
        }
        mappings = {
            'input1': 'you wrote: %message%',
            'input2': 'New Post: %permalink_url%',
            'input3': 'A link: %link%',
            'input4': 'A Men wrote: %description%',
            'input5': 'a picture in small: %image_low%',
            'input6': 'a large picture: %image_standard%'
        }
        with patch('core.utils.download_file') as mock_download:
            mock_download.side_effect = mock_downloadfile

            res = self.channel._fill_mappings_for_new_entry(inputs=mappings,
                                                            payload=payload)
            expected = {
                'input1': 'you wrote: ' + payload['message'],
                'input2': 'New Post: ' + payload['permalink_url'],
                'input3': 'A link: ' + payload['link'],
                'input4': 'A Men wrote: ' + payload['description'],
                'input5': payload['picture'],
                'input6': payload['full_picture'],
            }
            self.assertEquals(res, expected)

            res = self.channel._fill_mappings_for_new_entry(inputs=mappings,
                                                            payload={})
            self.assertEquals(res, mappings)

    def test_handle_action_raises_exception(self):
        with self.assertRaises(NotSupportedAction):
            self.channel.handle_action(action_type=TriggerType.new_photo,
                                       userid=self.user.id,
                                       inputs={})

    def test_trigger_synopsis(self):
        conditions = [{'value': '#Daisychain'}]

        for trigger in TriggerType:
            trigger_id = Trigger.objects.get(trigger_type=trigger,
                                             channel_id=self.channel_id).id
            if trigger == TriggerType.new_post:
                return_value = "new post by you on Facebook"
            elif trigger == TriggerType.new_link:
                return_value = "new link posted by you on Facebook"
            elif trigger == TriggerType.new_photo:
                return_value = "new photo posted by you on Facebook"
            elif trigger == TriggerType.new_photo_with_hashtag:
                return_value = 'new photo by you with hashtag "{}" ' \
                               'on Facebook'.format(conditions[0]['value'])
            elif trigger == TriggerType.new_video:
                return_value = "new video posted by you on Facebook"

            self.assertEqual(self.channel.trigger_synopsis(
                trigger_id, conditions=conditions
            ), return_value)

    def test_get_payload(self):
        feed = {
            'description': 'blablabla',
            'message': 'blablub',
            'picture': 'nakedwoman',
            'full_picture': 'largepicture',
            'permalink_url': 'http://daisychain.me/secret',
            'link': 'http://daisychain.me/s3cr3t'
        }

        self.assertDictEqual(self.channel._get_payload(feed), feed)

    @patch("channel_facebook.channel.Config.get")
    @patch("channel_facebook.channel.reverse")
    @patch("channel_facebook.channel.log.warning")
    def test_build_absolute_uri(self, mock_log, mock_reverse, mock_get):

        # first test without having set DOMAIN_BASE before
        mock_get.return_value = ""
        mock_reverse.return_value = "/test_alias"

        actual = self.channel._build_absolute_uri("test_alias")

        mock_get.assert_called_with("DOMAIN_BASE")
        mock_log.assert_called_with("Facebook Config DOMAIN_BASE "
                                    "was accessed before set")
        mock_reverse.assert_called_with("test_alias")
        self.assertEqual("/test_alias", actual)

        # reset mocks
        mock_log.reset_mock()
        mock_reverse.reset_mock()
        mock_get.reset_mock()

        # second test with having set DOMAIN_BASE before
        mock_get.return_value = "http://test.domain:1234"

        actual = self.channel._build_absolute_uri("test_alias")

        mock_get.assert_called_with("DOMAIN_BASE")
        mock_log.assert_not_called()
        mock_reverse.assert_called_with("test_alias")
        self.assertEqual("http://test.domain:1234/test_alias", actual)
