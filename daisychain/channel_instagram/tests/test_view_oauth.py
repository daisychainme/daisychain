from django.core.urlresolvers import reverse
from django.test import TransactionTestCase
from channel_instagram.views import (SESSKEY_OAUTH_NEXT_URI,
                                     SESSKEY_OAUTH_VERIFY_TOKEN)
from channel_instagram.models import InstagramAccount
from django.contrib.auth.models import User
import json
import responses
from urllib.parse import urlsplit, parse_qs


class OAuthTest(TransactionTestCase):
    fixtures = ["core/fixtures/initial_data.json"]

    def setUp(self):
        self.max_muster = User.objects.create_user("max_muster")
        self.client.force_login(self.max_muster)

    def test_get_initial(self):

        getData = {
            "next": "/test-redirect-uri/"
        }

        res = self.client.get(reverse("instagram:connect"), getData)

        self.assertIn("instagram_oauth_next_uri", self.client.session)
        self.assertEqual("/test-redirect-uri/",
                         self.client.session["instagram_oauth_next_uri"])

        self.assertEqual(res.status_code, 302)
        oauth_url = urlsplit(res['Location'])

        self.assertEqual('https', oauth_url.scheme)
        self.assertEqual('api.instagram.com', oauth_url.netloc)
        self.assertEqual('/oauth/authorize/', oauth_url.path)

        oauth_getParams = parse_qs(oauth_url.query)

        oauth_redir_url = urlsplit(oauth_getParams['redirect_uri'][0])
        oauth_redir_getParams = parse_qs(oauth_redir_url.query)

        self.assertIn(SESSKEY_OAUTH_VERIFY_TOKEN, self.client.session)
        self.assertEqual(self.client.session[SESSKEY_OAUTH_VERIFY_TOKEN],
                         oauth_redir_getParams['verify_token'][0])

    def test_get_initial__already_connected(self):

        InstagramAccount(user=self.max_muster).save()
        getData = {
            "next": "/test-redirect-uri/"
        }

        res = self.client.get(reverse("instagram:connect"), getData)

    def test_get_error_callback(self):

        getData = {
            "error": "access_denied",
            "error_reason": "user_denied",
            "error_description": "The user denied your request"
        }

        res = self.client.get(reverse("instagram:connect"), getData)

        self.assertEqual(302, res.status_code)

        # TODO check response

    def test_get_without_verify_token(self):

        session = self.client.session
        session[SESSKEY_OAUTH_NEXT_URI] = "/test?type=set"
        session.save()

        getData = {
            "code": "code_will_not_be_checked_anyway"
        }

        res = self.client.get(reverse("instagram:connect"), getData)

        self.assertEqual(302, res.status_code)

        redirect_uri = urlsplit(res['Location'])
        self.assertEqual("/test", redirect_uri.path)
        self.assertDictEqual({"status": ["error"],
                              "type": ["set", "api"],
                              "detail": ["verify_token_not_set"]},
                             parse_qs(redirect_uri.query))

    def test_get_with_no_verify_token_in_session(self):

        session = self.client.session
        session[SESSKEY_OAUTH_NEXT_URI] = "/test"
        session.save()

        getData = {
            "code": "code_will_not_be_checked_anyway",
            "verify_token": "token_will_not_be_checked_anyway"
        }

        res = self.client.get(reverse("instagram:connect"), getData)

        self.assertEqual(302, res.status_code)

        redirect_uri = urlsplit(res['Location'])
        self.assertEqual("/test", redirect_uri.path)
        self.assertDictEqual({"status": ["error"],
                              "type": ["internal"],
                              "detail": ["no_verify_token_in_session"]},
                             parse_qs(redirect_uri.query))

    def test_get_with_valid_code_and_invalid_verify_token(self):

        sessionValue = "correctvalue"
        session = self.client.session
        session[SESSKEY_OAUTH_NEXT_URI] = "/test"
        session[SESSKEY_OAUTH_VERIFY_TOKEN] = sessionValue
        session.save()

        getData = {
            "verify_token": "someothervaluethaninthesession",
            "code": "code_will_not_be_checked_anyway"
        }

        res = self.client.get(reverse("instagram:connect"), getData)

        self.assertEqual(302, res.status_code)
        redirect_uri = urlsplit(res['Location'])
        self.assertEqual("/test", redirect_uri.path)
        self.assertDictEqual({"status": ["error"],
                              "type": ["api"],
                              "detail": ["invalid_verify_token"]},
                             parse_qs(redirect_uri.query))

    @responses.activate
    def test_get_with_valid_data(self):

        def request_callback(request):
            headers = {}
            body = json.dumps({
                "access_token": "123457890",
                "user": {
                    "id": "1234567890"
                }
            })
            return (200, headers, body)

        session = self.client.session
        session[SESSKEY_OAUTH_VERIFY_TOKEN] = "session_token"
        session.save()

        getData = {
            "verify_token": "session_token",
            "code": "code_to_be_checked_by_responses"
        }

        with responses.RequestsMock() as resp:

            resp.add(responses.GET,
                     "https://api.instagram.com/v1/subscriptions",
                     status=200,
                     json={"data": [1]})

            resp.add_callback(
                    responses.POST,
                    "https://api.instagram.com/oauth/access_token",
                    callback=request_callback)

            res = self.client.get(reverse("instagram:connect"), getData)

    @responses.activate
    def test_get__with_valid_data_account_already_in_used(self):

        def request_callback(request):
            headers = {}
            body = json.dumps({
                "access_token": "123457890",
                "user": {
                    "id": "1234567890"
                }
            })
            return (200, headers, body)

        session = self.client.session
        session[SESSKEY_OAUTH_VERIFY_TOKEN] = "session_token"
        session.save()

        getData = {
            "verify_token": "session_token",
            "code": "code_to_be_checked_by_responses"
        }

        InstagramAccount(user=self.max_muster,
                         instagram_id="1234567890").save()

        with responses.RequestsMock() as resp:

            resp.add_callback(
                    responses.POST,
                    "https://api.instagram.com/oauth/access_token",
                    callback=request_callback)

            res = self.client.get(reverse("instagram:connect"), getData)

    @responses.activate
    def test_get_with_valid_data_but_api_error(self):

        def request_callback(request):
            headers = {}
            body = ''
            return (400, headers, body)

        session = self.client.session
        session[SESSKEY_OAUTH_VERIFY_TOKEN] = "session_token"
        session.save()

        getData = {
            "verify_token": "session_token",
            "code": "code_to_be_checked_by_responses"
        }

        with responses.RequestsMock() as resp:
            resp.add_callback(
                    responses.POST,
                    "https://api.instagram.com/oauth/access_token",
                    callback=request_callback)

            res = self.client.get(reverse("instagram:connect"), getData)

            self.assertEqual(302, res.status_code)
            redirect_uri = urlsplit(res['Location'])
            self.assertEqual("/", redirect_uri.path)
            self.assertDictEqual(
                    {"status": ["error"],
                     "type": ["api"],
                     "detail": ["error_while_fetching_access_token"]},
                    parse_qs(redirect_uri.query))
