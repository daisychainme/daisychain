from base64 import urlsafe_b64decode
from hashlib import sha1, sha256
from hmac import new as hmac_new
from json import loads as json_decode
from logging import getLogger
from urllib.parse import urlencode
from uuid import uuid4

import requests
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.utils import timezone
from django.utils.translation import ugettext as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View

from .channel import FacebookChannel
from .config import Config
from .models import FacebookAccount

log = getLogger('channel')


class StartAuthenticationView(LoginRequiredMixin, View):
    def get(self, request):
        callback_url = reverse('facebook:callback')
        state_string = str(uuid4())
        app_scope = 'public_profile,publish_actions,user_status,user_posts'
        params = {
            'client_id': Config.get("APP_ID"),
            'redirect_uri': request.build_absolute_uri(callback_url),
            'scope': app_scope,
            'state': state_string,
            'response_type': 'code'
        }
        oauth_url = Config.get("API_LOGIN_OAUTH_BASE_URI") + "?" + urlencode(params)
        # url the user is redirected after callback.
        request.session['facebook_next_url'] = request.GET.get('next', None)
        request.session['state'] = state_string
        return HttpResponseRedirect(oauth_url)


class StopAuthenticationView(LoginRequiredMixin, View):
    def get(self, request):
        if self.deleteEntry(request.user):
            log.debug(type(request.user))
            messages.success(request, _('Successfully revoked Facebook permissions'))
            status = "success"
        else:
            messages.success(request, _('Error occured'))
            status = "error"
        redirect_url = request.GET.get('next', reverse("channels:list")) + "?status={}".format(status)
        return HttpResponseRedirect(redirect_url)

    @staticmethod
    def deleteEntry(fb_user):
        try:
            #if isinstance(fb_user, FacebookAccount):
            #    facebook_account = fb_user
            if isinstance(fb_user, User):
                facebook_account = FacebookAccount.objects.get(user=fb_user)
            else:
                facebook_account = FacebookAccount.objects.get(username=fb_user)
            facebook_account.delete()
        except FacebookAccount.DoesNotExist:
            pass
        return True


class CallbackView(View):
    def get(self, request):
        callback_url = reverse('facebook:callback')
        if not request.user.is_authenticated():
            return HttpResponseBadRequest()

        if request.session['state'] != request.GET['state']:
            return HttpResponseBadRequest()

        default_url = reverse('channels:list')
        redirect_url = request.session.get('facebook_next_url', None)
        if not redirect_url:
            redirect_url = default_url
        success_url = '{}?status=success'.format(redirect_url)

        abort = request.GET.get('error', None)
        if abort:
            messages.error(request, _('Authentification canceld! Please try again!'))
            failure_url = '{}?status=error'.format(redirect_url)
            return HttpResponseRedirect(failure_url)

        code = request.GET.get('code', None)
        if not code:
            failure_url = '{}?status=error'.format(redirect_url)
            return HttpResponseRedirect(failure_url)

        data = {
            'client_id': Config.get("APP_ID"),
            'client_secret': Config.get("APP_SECRET"),
            'code': code,
            'redirect_uri': request.build_absolute_uri(callback_url),
        }
        resp = requests.get(Config.get("API_ACCESS_TOKEN_URI"), params=data)
        if not resp.ok:
            return HttpResponseBadRequest()
        try:
            access_token = resp.json()['access_token']
            expires_in = resp.json()['expires_in']

            # get username
            data = {
                'input_token': access_token,
                'access_token': Config.get('APP_ID') + '|' + Config.get('APP_SECRET'),
            }
            user_resp = requests.get(Config.get('API_CHECK_ACCESS_TOKEN_URI'),
                                     params=data)
        except Exception:
            return HttpResponseBadRequest()
        username = user_resp.json()['data']['user_id']
        try:
            existing_account = FacebookAccount.objects.get(user=request.user)
            existing_account.access_token = access_token
            existing_account.username = username
            existing_account.save()
            return HttpResponseRedirect(success_url)
        except:
            facebook_account = FacebookAccount(user=request.user,
                                               access_token=access_token,
                                               username=username,
                                               last_post_time=timezone.now())
            facebook_account.save()

        return HttpResponseRedirect(success_url)


class WebhookView(View):
    def get(self, request, *args, **kwargs):
        if (self.request.GET['hub.verify_token'] == Config.get("APP_WEBHOOK_CHALLENGE")):
            return HttpResponse(self.request.GET['hub.challenge'])
        else:
            return HttpResponseBadRequest()

    def post(self, request, *args, **kwargs):
        payload = request.body
        # check if request is from facebook by calculating a hash
        digest = hmac_new(Config.get("APP_SECRET").encode("utf-8"),
                          msg=payload,
                          digestmod=sha1).hexdigest()
        # check if the calculated hash is the same as sent by instagram
        # return 400 Bad Request if not
        try:
            prefix = 'sha1='
            if (prefix + digest) != request.META['HTTP_X_HUB_SIGNATURE']:
                log.warning("HTTP-X-HUB-SIGNATURE did not match")
                raise ValueError()
        except Exception:
            return HttpResponseBadRequest()
        # hashes match, process request
        jsonData = json_decode(payload.decode('utf-8'))
        channel = FacebookChannel()
        if 'user' in jsonData['object'] and 'entry' in jsonData:
            log.debug("Fire {} triggers".format(len(jsonData['entry'])))
            for trigger in jsonData['entry']:
                channel.fire_trigger(trigger)
        return HttpResponse()


class RevokeAuthenticationView(View):
    @csrf_exempt
    def post(self, request, *args, **kwargs):
        if 'signed_request' in request.POST:
            try:
                resp = self._parse_signed_request(request.POST['signed_request'])
                StopAuthenticationView.deleteEntry(fb_user=resp['user_id'])
            except ValueError:
                return HttpResponseBadRequest()
        return HttpResponse()

    @csrf_exempt
    def get(self, request, *args, **kwargs):
        return HttpResponse()

    @staticmethod
    def _parse_signed_request(signed_request):
        [encoded_sig, payload] = signed_request.split('.')

        # decode data
        sig = RevokeAuthenticationView.base64_url_decode(encoded_sig)
        data = json_decode(str(RevokeAuthenticationView.base64_url_decode(payload), 'utf-8'))

        if data['algorithm'].upper() != 'HMAC-SHA256':
            raise ValueError('Unknown algorithm. Expected HMAC-SHA256')

        # check sig
        secret = Config.get("APP_SECRET").encode('utf-8')
        expected_sig = hmac_new(secret, payload.encode(), sha256).digest()
        if sig != expected_sig:
            raise ValueError('Bad Signed JSON signature!')

        return data

    @staticmethod
    def base64_url_decode(input):
        input += '=' * (4 - (len(input) % 4))
        return urlsafe_b64decode(input.encode('utf-8'))
