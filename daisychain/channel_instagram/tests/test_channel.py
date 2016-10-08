from django.test import TestCase
from channel_instagram import channel
from channel_instagram.conf import Config
from channel_instagram.models import InstagramAccount
from core import models
from core.channel import ChannelStateForUser
from django.contrib.auth.models import User
from mock import MagicMock, patch
import logging
import responses


class ChannelTest(TestCase):
    fixtures = ["core/fixtures/initial_data.json"]

    def setUp(self):
        self.channel = channel.InstagramChannel()
        logging.disable(logging.CRITICAL)

    @patch("channel_instagram.channel.Config.get")
    @patch("channel_instagram.channel.reverse")
    @patch("channel_instagram.channel.log.warning")
    def test_build_absolute_uri(self, mock_log, mock_reverse, mock_get):

        # first test without having set DOMAIN_BASE before
        mock_get.return_value = ""
        mock_reverse.return_value = "/test_alias"

        actual = self.channel._build_absolute_uri("test_alias")

        mock_get.assert_called_with("DOMAIN_BASE")
        mock_log.assert_called_with("Instagram Config DOMAIN_BASE "
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

    @patch("channel_instagram.channel.InstagramChannel."
           "generate_subscription_verify_token")
    @patch("channel_instagram.channel.InstagramChannel._build_absolute_uri")
    @patch("channel_instagram.channel.log.warning")
    @patch("channel_instagram.channel.log.error")
    @patch("channel_instagram.channel.log.info")
    @patch("channel_instagram.channel.Config.get")
    @responses.activate
    def test_create_subscription(self, mock_get, mock_info, mock_error,
                                 mock_warning, mock_build_url, mock_generate):

        # test with error in api
        mock_get.return_value = "http://test/0"
        with responses.RequestsMock() as resp:
            resp.add(responses.GET,
                     "http://test/0",
                     status=200,
                     json={"error": ["json has no data field"]})

            resp.add(responses.POST, "http://test/0", status=200)

            no_return = self.channel.create_subscription()

            mock_warning.assert_called_with("Instagram API subscription list "
                                            "returned code 200 but response "
                                            "had no attribute 'data'. "
                                            "Nevertheless trying to create "
                                            "subscription")

        # test with subscription already created, request correct
        mock_get.return_value = "http://test/1"
        with responses.RequestsMock() as resp:
            resp.add(responses.GET,
                     "http://test/1",
                     status=200,
                     json={"data": ["length needs to be > 0"]})

            no_return = self.channel.create_subscription()

            mock_info.assert_called_with("Instagram already subscribed, "
                                         "do not repeat")

        # test with subscription already created, request failed
        mock_get.return_value = "http://test/2"
        with responses.RequestsMock() as resp:
            resp.add(responses.GET,
                     "http://test/2",
                     status=400,
                     json={"meta": {}})

            resp.add(responses.POST, "http://test/2", status=200)

            no_return = self.channel.create_subscription()

            mock_error.assert_called_with("Error while fetching subscription "
                                          "list from Instagram. Nevertheless "
                                          "trying to create subscription")

        # test with subscription not yet created, request correct
        mock_error.reset_mock()
        mock_info.reset_mock()
        mock_get.return_value = "http://test/3"
        with responses.RequestsMock() as resp:
            resp.add(responses.GET,
                     "http://test/3",
                     status=200,
                     json={"data": []})

            resp.add(responses.POST,
                     "http://test/3",
                     status=200)

            no_return = self.channel.create_subscription()

            mock_info.assert_called_with("Instagram not yet subscribed, do it")
            mock_error.assert_not_called()

        # test with subscription not yet create, request failed
        mock_error.reset()
        mock_info.reset()
        mock_get.return_value = "http://test/4"
        with responses.RequestsMock() as resp:
            resp.add(responses.GET,
                     "http://test/4",
                     status=200,
                     json={"data": []})

            resp.add(responses.POST,
                     "http://test/4",
                     status=400, json={"error": "test_error_message"})

            no_return = self.channel.create_subscription()

            mock_error.assert_any_call("Could not subscribe to Instagram. "
                                       "Error message:")
            mock_error.assert_any_call({"error": "test_error_message"})

    @patch("channel_instagram.channel.hmac_new")
    def test_generate_subscription_verify_token(self, hmac_new):
        self.channel.generate_subscription_verify_token()

    @patch("channel_instagram.channel.Config.get")
    @responses.activate
    def test_get_media_data(self, mock_get):

        # test setup
        insta_user = InstagramAccount(instagram_id="42", access_token="1337")
        mediaid = 'test_id'
        mock_get.return_value = "http://test/1/%s"

        # test successful request
        response_body = {
            "meta": {"code": 200},
            "data": {"testing": "no data body needed"}
        }

        with responses.RequestsMock() as resp:
            resp.add(responses.GET,
                     "http://test/1/test_id?access_token=1337",
                     match_querystring=True,
                     status=200,
                     json=response_body)

            actual = self.channel.get_media_data(insta_user, mediaid)

            self.assertDictEqual(response_body['data'], actual)

        # test failed request
        mock_get.return_value = "http://test/2/%s"
        response_body = {
            "meta": {
                "code": 400,
                "error_type": "A testing error",
                "error_message": "Not a real error, we are just testing..."
            }
        }

        with responses.RequestsMock() as resp:
            resp.add(responses.GET,
                     "http://test/2/test_id?access_token=1337",
                     match_querystring=True,
                     status=400,
                     json=response_body)

            with self.assertRaises(channel.ApiException) as cm:
                will_fail = self.channel.get_media_data(insta_user, mediaid)

            exception = cm.exception
            self.assertEqual(exception.code,
                             response_body['meta']['code'])
            self.assertEqual(exception.type,
                             response_body['meta']['error_type'])
            self.assertEqual(exception.message,
                             response_body['meta']['error_message'])

            expected_exception_str = "{} [Code: {}] \"{}\"".format(
                    exception.type,
                    exception.code,
                    exception.message)

            self.assertEqual(expected_exception_str, str(exception))

    @responses.activate
    def test_load_image__200(self):
        response_body = b'\narbitrary test data\n'
        url = "http://example.com/test_data"
        responses.add(responses.GET, url, match_querystring=True,
                      status=200,
                      body=response_body)

        c = channel.InstagramChannel()
        tmp_file = c.load_image(url)
        tmp_data = tmp_file.read()

        self.assertEqual(response_body, tmp_data)

    @responses.activate
    def test_load_image__400(self):
        response_body = {"meta": "testing_error_body"}
        url = "http://example.com/test_data"
        responses.add(responses.GET, url, match_querystring=True,
                      status=400,
                      json=response_body)

        c = channel.InstagramChannel()

        with self.assertRaises(channel.ApiException) as cm:
            data = c.load_image(url)

        exception = cm.exception

        expected_error_message = "Error while loading image %s" % url

        self.assertEqual(exception.code, 400)
        self.assertEqual(exception.type, "InternalDownloadError")
        self.assertEqual(exception.message, expected_error_message)

        expected_exception_str = "{} [Code: {}] \"{}\"".format(
                "InternalDownloadError",
                400,
                expected_error_message)

        self.assertEqual(expected_exception_str, str(exception))

    def test_fire_trigger__image(self):

        user = User.objects.create_user('john', 'john@doe.com', 'passwd')
        user.save()
        userid = user.pk

        InstagramAccount(user=user,
                         instagram_id="3229602005",
                         access_token="").save()

        trigger_payload = {
            "object_id": "3229602005",
            "data": {
                "media_id": "1247762848237443409_3229602005"
            }
        }

        c = channel.InstagramChannel()

        media_data = {"type": "image"}
        c.get_media_data = MagicMock(return_value=media_data)
        c._fire_image_trigger = MagicMock()

        c.fire_trigger(trigger_payload)

        c._fire_image_trigger.assert_called_with(user, media_data)

    def test_fire_trigger__ApiException(self):

        user = User.objects.create_user('john', 'john@doe.com', 'passwd')
        user.save()
        userid = user.pk

        InstagramAccount(user=user,
                         instagram_id="3229602005",
                         access_token="").save()

        trigger_payload = {
            "object_id": "3229602005",
            "data": {
                "media_id": "1247762848237443409_3229602005"
            }
        }

        c = channel.InstagramChannel()

        c.get_media_data = MagicMock()
        c.get_media_data.side_effect = channel.ApiException("", 0, "")
        c._fire_image_trigger = MagicMock()
        c._fire_video_trigger = MagicMock()

        c.fire_trigger(trigger_payload)

        c._fire_image_trigger.assert_not_called()
        c._fire_video_trigger.assert_not_called()

    def test_fire_trigger__DoesNotExist(self):

        user = User.objects.create_user('john', 'john@doe.com', 'passwd')
        user.save()
        userid = user.pk

        InstagramAccount(user=user,
                         instagram_id="3229602005",
                         access_token="").save()

        trigger_payload = {
            "object_id": "42",
            "data": {
                "media_id": "1247762848237443409_3229602005"
            }
        }

        c = channel.InstagramChannel()

        c.get_media_data = MagicMock()

        c.fire_trigger(trigger_payload)

        c.get_media_data.assert_not_called()

    @patch("core.core.Core.handle_trigger")
    def test__fire_image_trigger__wo_tags(self, mock__handle_trigger):

        user = User.objects.create_user('john', 'john@doe.com', 'passwd')
        user.save()
        userid = user.pk

        channel_model = models.Channel(name="Instagram",
                                       color="#000000",
                                       image="none",
                                       font_color="#ffffff")
        channel_model.save()

        media_data = {
            "type": "image",
            "caption": {
                "text": "Test caption"
            },
            "link": "http://instagram.example.com/permalink/to/image",
            "images": {
                "standard_resolution": {
                    "url": "http://example.com/test_image_high"
                },
                "low_resolution": {
                    "url": "http://example.com/test_image_low"
                },
                "thumbnail": {
                    "url": "http://example.com/test_image_thumbnail"
                }
            },
            "tags": []
        }

        c = channel.InstagramChannel()
        c._fire_image_trigger(user, media_data)

        core_payload = {
            "caption": "Test caption",
            "url": "http://instagram.example.com/permalink/to/image",
            "image_standard": "http://example.com/test_image_high",
            "image_low": "http://example.com/test_image_low",
            "thumbnail": "http://example.com/test_image_thumbnail"
        }

        mock__handle_trigger.assert_called_with(
            channel_model.name,
            channel.TriggerType.new_photo,
            userid,
            core_payload
        )

    @patch("core.core.Core.handle_trigger")
    def test__fire_image_trigger__with_tags(self, mock__handle_trigger):

        user = User.objects.create_user('john', 'john@doe.com', 'passwd')
        user.save()
        userid = user.pk

        channel_model = models.Channel(
                name="Instagram",
                color="#000000",
                image="none",
                font_color="#ffffff")
        channel_model.save()

        media_data = {
            "type": "image",
            "caption": {
                "text": "Test caption"
            },
            "link": "http://instagram.example.com/permalink/to/image",
            "images": {
                "standard_resolution": {
                    "url": "http://example.com/test_image_high"
                },
                "low_resolution": {
                    "url": "http://example.com/test_image_low"
                },
                "thumbnail": {
                    "url": "http://example.com/test_image_thumbnail"
                }
            },
            "tags": ["hashtag_1", "hashtag_2"]
        }

        c = channel.InstagramChannel()
        c._fire_image_trigger(user, media_data)

        core_payload = {
            "caption": "Test caption",
            "url": "http://instagram.example.com/permalink/to/image",
            "image_standard": "http://example.com/test_image_high",
            "image_low": "http://example.com/test_image_low",
            "thumbnail": "http://example.com/test_image_thumbnail",
            "tags": ["hashtag_1", "hashtag_2"]
        }

        mock__handle_trigger.assert_called_with(
            channel_model.name,
            channel.TriggerType.new_photo_with_tags,
            userid,
            core_payload
        )

    def test_fill_mappings__new_photo(self):

        c = channel.InstagramChannel()

        c._fill_mappings_for_photo = MagicMock()

        payload = {"test": "payload-dict"}
        inputs = {"test": "inputs-dict"}

        c.fill_recipe_mappings(
                channel.TriggerType.new_photo,
                42,
                payload,
                [],
                inputs)

        c._fill_mappings_for_photo.assert_called_with(payload, inputs)

    def test_fill_mappings__new_photo_with_tags(self):

        c = channel.InstagramChannel()

        c._fill_mappings_for_photo_with_tags = MagicMock()

        payload = {"caption": "payload-dict"}
        conditions = {"hashtag": "foobar"}
        inputs = {"test": "inputs-dict"}

        c.fill_recipe_mappings(
                channel.TriggerType.new_photo_with_tags,
                42,
                payload,
                conditions,
                inputs)

        c._fill_mappings_for_photo_with_tags.assert_called_with(
                payload, conditions, inputs)

    def test_fill_mappings__NotSupportedTrigger(self):

        c = channel.InstagramChannel()

        payload = {"test": "payload-dict"}
        inputs = {"test": "inputs-dict"}

        with self.assertRaises(channel.NotSupportedTrigger) as cm:
            c.fill_recipe_mappings(
                    0,
                    42,
                    payload,
                    [],
                    inputs)

    def test__fill_mappings_for_photo(self):

        c = channel.InstagramChannel()

        inputs = {
            "a": "%caption%",
            "b": "prefix\"%caption%\"suffix",
            "c": "%url%",
            "d": "prefix\"%url%\"suffix",
            "e": "%image_standard%",
            "f": "prefix%image_standard%suffix",
            "g": "%image_low%",
            "h": "prefix%image_low%suffix"
        }
        payload = {
            "caption": "the caption",
            "url": "http://instagram.example.com/permalink/to/image",
            "image_standard": "http://example.com/test_image_standard",
            "image_low": "http://example.com/test_image_low",
            "thumbnail": "http://example.com/test_image_thumbnail"
        }
        dummy_file = b'In real life I would be a file handle'
        expected_inputs = {
            "a": payload["caption"],
            "b": "prefix\"" + payload["caption"] + "\"suffix",
            "c": payload["url"],
            "d": "prefix\"" + payload["url"] + "\"suffix",
            "e": dummy_file,
            "f": dummy_file,
            "g": dummy_file,
            "h": dummy_file
        }

        c.load_image = MagicMock(return_value=dummy_file)

        filled_inputs = c._fill_mappings_for_photo(payload, inputs)

        self.assertDictEqual(expected_inputs, filled_inputs)

    def test__fill_mappings_for_photo_with_tags(self):

        c = channel.InstagramChannel()

        inputs = {
            "a": "%caption%",
            "b": "prefix\"%caption%\"suffix",
            "c": "%url%",
            "d": "prefix\"%url%\"suffix",
            "e": "%image_standard%",
            "f": "prefix%image_standard%suffix",
            "g": "%image_low%",
            "h": "prefix%image_low%suffix",
            "i": "%caption_without_hashtags%",
            "j": "prefix\"%caption_without_hashtags%\"suffix"
        }
        payload = {
            "caption": "the caption #foobar",
            "url": "http://instagram.com/permalink/to/image",
            "image_standard": "http://example.com/test_image_standard",
            "image_low": "http://example.com/test_image_low",
            "thumbnail": "http://example.com/test_image_thumbnail",
            "tags": ["hashtag_1", "hashtag_2"]
        }
        conditions = {"hashtag": "foobar"}
        dummy_file = b'In real life I would be a file handle'
        expected_inputs = {
            "a": "the caption #foobar",
            "b": "prefix\"the caption #foobar\"suffix",
            "c": "http://instagram.com/permalink/to/image",
            "d": "prefix\"http://instagram.com/permalink/to/image\"suffix",
            "e": dummy_file,
            "f": dummy_file,
            "g": dummy_file,
            "h": dummy_file,
            "i": "the caption",
            "j": "prefix\"the caption\"suffix",
        }

        c.load_image = MagicMock(return_value=dummy_file)

        filled_inputs = c._fill_mappings_for_photo_with_tags(payload,
                                                             conditions,
                                                             inputs)

        self.assertDictEqual(expected_inputs, filled_inputs)

    def test__fill_mappings_for_photo_with_tags__without_hashtag(self):

        with self.assertRaises(channel.ConditionNotMet):
            self.channel._fill_mappings_for_photo_with_tags({}, {}, {})

    def test_handle_action(self):

        with self.assertRaises(channel.NotSupportedAction):
            self.channel.handle_action(0, 42, {})

    '''
    def test_fire_trigger__video(self):

        user = User.objects.create_user('john', 'john@doe.com', 'passwd')
        user.save()
        instagram_id = user.pk

        InstagramAccount(user=user,
                      instagram_id="3229602005",
                      access_token="").save()

        trigger_payload = {
            "object_id": "3229602005",
            "data": {
                "media_id": "1247762848237443409_3229602005"
            }
        }

        c = channel.InstagramChannel()

        media_data = {"type": "video"}
        c.get_media_data = MagicMock(return_value=media_data)
        c._fire_video_trigger = MagicMock()

        c.fire_trigger(trigger_payload)

        c._fire_video_trigger.assert_called_with(user, media_data)

    @patch("core.core.Core.handle_trigger")
    def test__fire_video_trigger__wo_tags(self, mock__handle_trigger):

        user = User.objects.create_user('john', 'john@doe.com', 'passwd')
        user.save()
        userid = user.pk

        media_data = {
            "type": "video",
            "caption": {
                "text": "Test caption"
            },
            "link": "http://instagram.example.com/permalink/to/image",
            "videos": {
                "standard_resolution": {
                    "url": "http://example.com/test_video_high"
                },
                "low_resolution": {
                    "url": "http://example.com/test_video_low"
                },
                "low_bandwidth": {
                    "url": "http://example.com/test_video_thumbnail"
                }
            },
            "images": {
                "standard_resolution": {
                    "url": "http://example.com/test_image_high"
                },
                "low_resolution": {
                    "url": "http://example.com/test_image_low"
                },
                "thumbnail": {
                    "url": "http://example.com/test_image_thumbnail"
                }
            },
            "tags": []
        }

        c = channel.InstagramChannel()
        c._fire_video_trigger(user, media_data)

        core_payload = {
            "caption": "Test caption",
            "url": "http://instagram.example.com/permalink/to/image",
            "video_standard": "http://example.com/test_video_high",
            "video_low": "http://example.com/test_video_low",
            "video_low_bandwidth": "http://example.com/test_video_thumbnail",
            "image_standard": "http://example.com/test_image_high",
            "image_low": "http://example.com/test_image_low",
            "thumbnail": "http://example.com/test_image_thumbnail"
        }

        mock__handle_trigger.assert_called_with(
            "Instagram",
            channel.TriggerType.new_video,
            userid,
            core_payload
        )

    @patch("core.core.Core.handle_trigger")
    def test__fire_video_trigger__with_tags(self, mock__handle_trigger):

        user = User.objects.create_user('john', 'john@doe.com', 'passwd')
        user.save()
        userid = user.pk

        media_data = {
            "type": "video",
            "caption": {
                "text": "Test caption"
            },
            "link": "http://instagram.example.com/permalink/to/image",
            "videos": {
                "standard_resolution": {
                    "url": "http://example.com/test_video_high"
                },
                "low_resolution": {
                    "url": "http://example.com/test_video_low"
                },
                "low_bandwidth": {
                    "url": "http://example.com/test_video_thumbnail"
                }
            },
            "images": {
                "standard_resolution": {
                    "url": "http://example.com/test_image_high"
                },
                "low_resolution": {
                    "url": "http://example.com/test_image_low"
                },
                "thumbnail": {
                    "url": "http://example.com/test_image_thumbnail"
                }
            },
            "tags": ["hashtag_1", "hashtag_2"]
        }

        c = channel.InstagramChannel()
        c._fire_video_trigger(user, media_data)

        core_payload = {
            "caption": "Test caption",
            "url": "http://instagram.example.com/permalink/to/image",
            "video_standard": "http://example.com/test_video_high",
            "video_low": "http://example.com/test_video_low",
            "video_low_bandwidth": "http://example.com/test_video_thumbnail",
            "image_standard": "http://example.com/test_image_high",
            "image_low": "http://example.com/test_image_low",
            "thumbnail": "http://example.com/test_image_thumbnail",
            "tags": ["hashtag_1", "hashtag_2"]
        }

        mock__handle_trigger.assert_called_with(
            "Instagram",
            channel.TriggerType.new_video_with_tags,
            userid,
            core_payload
        )

    def test_fill_mappings__new_video(self):

        c = channel.InstagramChannel()

        c._fill_mappings_for_video = MagicMock()

        payload = {"test": "payload-dict"}
        inputs = {"test": "inputs-dict"}

        c.fill_recipe_mappings(
                channel.TriggerType.new_video,
                42,
                payload,
                [],
                inputs)

        c._fill_mappings_for_video.assert_called_with(payload, inputs)

    def test_fill_mappings__new_video_with_tags(self):

        c = channel.InstagramChannel()

        c._fill_mappings_for_video_with_tags = MagicMock()

        payload = {"test": "payload-dict"}
        inputs = {"test": "inputs-dict"}

        c.fill_recipe_mappings(
                channel.TriggerType.new_video_with_tags,
                42,
                payload,
                [],
                inputs)

        c._fill_mappings_for_video_with_tags.assert_called_with(
                payload, [], inputs)
    '''

    def test_user_is_connected__no_model_object(self):

        user = User.objects.create_user('john', 'john@doe.com', 'passwd')
        user.save()

        result = self.channel.user_is_connected(user)

        self.assertEqual(result, ChannelStateForUser.initial)

    @patch("channel_instagram.channel.Config.get")
    @responses.activate
    def test_user_is_connected__invalid_access_token(self, mock_get):

        # test setup
        user = User.objects.create_user('john', 'john@doe.com', 'passwd')
        user.save()
        insta_user = InstagramAccount(user=user,
                                      instagram_id="42",
                                      access_token="1337")
        insta_user.save()
        mock_get.return_value = "http://test/0"

        with responses.RequestsMock() as resp:
            resp.add(responses.GET,
                     "http://test/0?access_token=1337",
                     match_querystring=True,
                     status=403,
                     json={})

            result = self.channel.user_is_connected(user)

            mock_get.assert_called_with("API_USER_SELF_ENDPOINT")

            self.assertEqual(result, ChannelStateForUser.expired)

    @patch("channel_instagram.channel.log.error")
    @patch("channel_instagram.channel.Config.get")
    @responses.activate
    def test_user_is_connected__corrupt_json(self, mock_get, mock_log):

        # test setup
        user = User.objects.create_user('john', 'john@doe.com', 'passwd')
        user.save()
        insta_user = InstagramAccount(user=user,
                                      instagram_id="42",
                                      access_token="1337")
        insta_user.save()
        mock_get.return_value = "http://test/0"

        with responses.RequestsMock() as resp:
            resp.add(responses.GET,
                     "http://test/0?access_token=1337",
                     match_querystring=True,
                     status=200,
                     json={})

            result = self.channel.user_is_connected(user)

            mock_get.assert_called_with("API_USER_SELF_ENDPOINT")

            self.assertEqual(result, ChannelStateForUser.expired)

    @patch("channel_instagram.channel.Config.get")
    @responses.activate
    def test_user_is_connected__valid(self, mock_get):

        # test setup
        user = User.objects.create_user('john', 'john@doe.com', 'passwd')
        user.save()
        insta_user = InstagramAccount(user=user,
                                      instagram_id="42",
                                      access_token="1337")
        insta_user.save()
        mock_get.return_value = "http://test/0"

        with responses.RequestsMock() as resp:
            resp.add(responses.GET,
                     "http://test/0?access_token=1337",
                     match_querystring=True,
                     status=200,
                     json={"data": "some data"})

            result = self.channel.user_is_connected(user)

            mock_get.assert_called_with("API_USER_SELF_ENDPOINT")

            self.assertEqual(result, ChannelStateForUser.connected)
