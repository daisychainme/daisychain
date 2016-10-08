from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseBadRequest
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.utils.decorators import method_decorator

from json import loads as json_decode
from hmac import new as hmac_new
from hashlib import md5, sha1
from logging import getLogger
from requests import post as requests_post
from time import time
from urllib.parse import urlsplit, parse_qs, urlencode, urlunsplit

from .conf import Config
from .channel import InstagramChannel
from .models import InstagramAccount

DEFAULT_OAUTH_NEXT_URI = "/"
SESSKEY_OAUTH_VERIFY_TOKEN = "instagram_oauth_verify_token"
SESSKEY_OAUTH_NEXT_URI = "instagram_oauth_next_uri"

log = getLogger("channel")


class RedirectingView(View):

    def fetch_next_uri(self, request):

        # get ?next= parameter and store it in session, default to root
        q_next = request.GET.get('next', DEFAULT_OAUTH_NEXT_URI)
        request.session[SESSKEY_OAUTH_NEXT_URI] = q_next

    def get_next_uri(self, request):
        try:
            return request.session[SESSKEY_OAUTH_NEXT_URI]
        except KeyError:
            return DEFAULT_OAUTH_NEXT_URI

    def build_redirect_uri(self, request, verify_token):
        redirect_path = reverse("instagram:connect")
        return ''.join((request.build_absolute_uri(redirect_path),
                        "?verify_token=",
                        verify_token))

    def append_query_params(self, url, **kwargs):

        uri = urlsplit(url)
        query = parse_qs(uri.query)

        for key in kwargs:
            if key in query:
                query[key].append(kwargs[key])
            else:
                query[key] = kwargs[key]

        query_string = urlencode(query, doseq=True)

        uri_new = uri._replace(query=query_string)

        return urlunsplit(uri_new)

    def clear_session(self, request):

        try:
            del request.session[SESSKEY_OAUTH_NEXT_URI]
        except KeyError:
            pass

        try:
            del request.session[SESSKEY_OAUTH_VERIFY_TOKEN]
        except KeyError:
            pass

    def error(self, request, **kwargs):

        url = self.append_query_params(self.get_next_uri(request),
                                       status='error',
                                       **kwargs)

        self.clear_session(request)

        return redirect(url)

    def success(self, request, **kwargs):

        url = self.append_query_params(self.get_next_uri(request),
                                       status="success",
                                       **kwargs)

        self.clear_session(request)

        return redirect(url)


class OAuthView(LoginRequiredMixin, RedirectingView):

    def get(self, request):

        log.debug("Instagram handling get-request")

        q_code = request.GET.get('code', False)
        q_error = request.GET.get('error', False)

        if q_error is not False:
            return self._handle_api_error_callback(request)
        elif q_code is not False:
            return self._handle_api_success_callback(request)
        else:
            return self._handle_initial_call(request)

    def _handle_initial_call(self, request):
        """build instagram oauth uri and redirect there"""

        log.debug("Instagram handling get-request: identified as initial")

        self.fetch_next_uri(request)

        # lookup if user is already connected to instagram
        try:
            InstagramAccount.objects.get(user=request.user)
            return self.success(request)
        except InstagramAccount.DoesNotExist:
            pass

        # create verify token and save it to the session
        verify_token = hmac_new(Config.get("CLIENT_SECRET").encode("utf-8"),
                                msg=request.user.email.encode("utf-8"),
                                digestmod=sha1).hexdigest()
        request.session[SESSKEY_OAUTH_VERIFY_TOKEN] = verify_token

        redirect_uri = self.build_redirect_uri(request, verify_token)

        instagram_oauth_uri = ''.join((Config.get("API_OAUTH_BASE_URI"),
                                       "/authorize/?client_id=",
                                       Config.get("CLIENT_ID"),
                                       "&redirect_uri=",
                                       redirect_uri,
                                       "&response_type=code"))

        return redirect(instagram_oauth_uri)

    def _handle_api_error_callback(self, request):
        """handle redirect from instagram when user denied access"""

        log.debug("Instagram handling get-request: "
                  "identified as error callback")

        # e.g. 'access_denied'
        # q_error = request.GET.get('error', False)

        # e.g. 'user_denied'
        q_error_reason = request.GET.get('error_reason', False)

        # e.g. 'The+user+denied+your+request'
        # q_error_description = request.GET.get('error_description', False)

        return self.error(request, type="api", detail=q_error_reason)

    def _handle_api_success_callback(self, request):
        """handle redirect from instagram when user granted access"""

        log.debug("Instagram handling get-request: "
                  "identified as success callback")

        # Instagram should return the verify_token it got from us
        try:
            q_verify_token = request.GET['verify_token']
        except KeyError:
            log.error("Instagram send us no verify_token. cancel oauth")
            return self.error(request,
                              type="api",
                              detail="verify_token_not_set")

        # and we should have it in the session too
        try:
            verify_token = request.session[SESSKEY_OAUTH_VERIFY_TOKEN]
        except KeyError:
            log.error("No verify_token in session. cancel oauth")
            return self.error(request,
                              type="internal",
                              detail="no_verify_token_in_session")

        # AND they should match!
        if q_verify_token != verify_token:
            log.error("verify_tokens did not match. cancel oauth")
            return self.error(request,
                              type="api",
                              detail="invalid_verify_token")

        log.debug("requesting access_token from instagram")
        res = requests_post(
            ''.join((Config.get("API_OAUTH_BASE_URI"), "/access_token")),
            {
                'client_id': Config.get("CLIENT_ID"),
                'client_secret': Config.get("CLIENT_SECRET"),
                'grant_type': 'authorization_code',
                'redirect_uri': self.build_redirect_uri(request, verify_token),
                'code': request.GET.get('code')
            }
        )

        if res.status_code is not 200:
            log.error("API error while fetching access_token from instagram")
            return self.error(request,
                              type='api',
                              detail="error_while_fetching_access_token")

        response = res.json()

        # create Instagram model
        try:
            InstagramAccount.objects.get(instagram_id=response['user']['id'])
        except InstagramAccount.DoesNotExist:
            log.info("creating InstagramAccount for {}".format(request.user))
            InstagramAccount(user=request.user,
                             instagram_id=response['user']['id'],
                             access_token=response['access_token']).save()
        else:
            log.info("InstagramAccount already connected")
            return self.error(request,
                              type='user',
                              detail="account_already_connected_to_other_user")

        # add subscription to instagram if not already happened
        log.debug("trying to create subscription")
        InstagramChannel().create_subscription()

        return self.success(request)


class SignoutView(LoginRequiredMixin, RedirectingView):

    def get(self, request):

        self.fetch_next_uri(request)

        try:
            account = InstagramAccount.objects.get(user=request.user)
            account.delete()
        except InstagramAccount.DoesNotExist:
            pass

        return self.success(request)


class SubscriptionView(View):

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        """The requests to this view come without any csrf mechanism."""
        return super(SubscriptionView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        """
            Instagram will send a GET request to confirm our subscription
            url. They send a GET-parameter 'hub.challenge' and we have to
            reply with that value and only the value.
        """
        log.debug("Instagram handling GET subscription")

        q_hub_mode = request.GET.get('hub.mode', False)
        q_hub_challenge = request.GET.get('hub.challenge', False)

        # TODO add a check when making a new subscription
        q_hub_verify_token = request.GET.get('hub.verify_token', False)

        log.debug("hub.mode: {}".format(q_hub_mode))
        log.debug("hub.challenge: {}".format(q_hub_challenge))
        log.debug("hub.verify_token: {}".format(q_hub_verify_token))

        if q_hub_mode == 'subscribe' and q_hub_challenge is not False:
            log.debug("instagram hub verification successful")

            return HttpResponse(q_hub_challenge, content_type="text/plain")

        log.error("instagram hub verification failed")
        return HttpResponseBadRequest()

    def post(self, request):

        log.debug("Instagram handling POST subscription")

        payload = request.body

        log.debug("payload: {}".format(payload))

        # check if request is from instagram by calculating a hash
        digest = self._calculate_signature(payload)

        # check if the calculated hash is the same as sent by instagram
        # return 400 Bad Request if not
        if digest != request.META['HTTP_X_HUB_SIGNATURE']:

            log.warning("HTTP-X-HUB-SIGNATURE did not match")

            return HttpResponseBadRequest()

        # hashes match, process request
        log.debug("Processing triggers")
        jsonData = json_decode(payload.decode('utf-8'))

        channel = InstagramChannel()

        for trigger in jsonData:
            channel.fire_trigger(trigger)

        return HttpResponse()

    def _calculate_signature(self, message):

        return hmac_new(Config.get("CLIENT_SECRET").encode("utf-8"),
                        msg=message,
                        digestmod=sha1).hexdigest()
