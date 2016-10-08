from django.core.urlresolvers import reverse
from mock import patch
from .test_base import FacebookBaseTestCase

from channel_facebook.config import Config


class TestWebhookView(FacebookBaseTestCase):
    @patch('channel_facebook.config.Config.get', return_value="prima")
    def test_webhook_start_challenge_with_right_token(self, mock_config_get):
        data = {
            'hub.verify_token': Config.get(1),
            'hub.challenge': 'aStrongChallenge'
        }
        response = self.client.get(reverse('facebook:hooks'), data)
        self.assertEqual(response.content, data['hub.challenge'].encode())
        self.assertEquals(response.status_code, 200)

    @patch('channel_facebook.config.Config.get', return_value="prima")
    def test_webhook_start_challenge_with_wrong_token(self, mock_config_get):
        data = {
            'hub.verify_token': 'thewrongone',
            'hub.challenge': 'aStrongChallenge'
        }
        response = self.client.get(reverse('facebook:hooks'), data)
        self.assertEquals(response.status_code, 400)

    @patch('channel_facebook.views.calculate_digest')
    def test_webhook_send_valid_webhook(self, mock_calculate_digest):
        payload = '{"entry":' \
                  '[{"time": 1474286151,' \
                  '"id": "101915710270588",' \
                  '"changed_fields": ["statuses"],' \
                  '"uid": "101915710270588"}],' \
                  '"object": "user"}'
        self.signature = 'sha1=test_signature'

        mock_calculate_digest.return_value = 'test_signature'

        resp = self.client.post(reverse("facebook:hooks"),
                                payload,
                                HTTP_X_HUB_SIGNATURE=self.signature,
                                content_type="application/json"
                                )

        mock_calculate_digest.assert_called_once()
        self.assertEqual(200, resp.status_code)


    def test_webhook_send_invalid_webhook(self):
        payload = '{"entry":' \
                  '[{"time": 1474286151,' \
                  '"id": "101915710270588",' \
                  '"changed_fields": ["statuses"],' \
                  '"uid": "101915710270588"}],' \
                  '"object": "user"}'
        self.signature = 'sha1=2fe4d79bb33f7e1e1a42a172435e8de370e57d80'

        resp = self.client.post(reverse("facebook:hooks"),
                                payload,
                                HTTP_X_HUB_SIGNATURE=self.signature,
                                content_type="application/json"
                                )
        self.assertEqual(400, resp.status_code)

    def test_webhook_send_no_query(self):
        resp = self.client.post(reverse("facebook:hooks"))
        self.assertEqual(400, resp.status_code)
