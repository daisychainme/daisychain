# communication within django and Client
from django.shortcuts import render, redirect
from django.core.urlresolvers import reverse
from django.http import HttpResponse, \
    HttpResponseBadRequest, HttpResponseForbidden, HttpRequest
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.views.generic import View
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site

#connection to Dropbox and DB
import dropbox
from dropbox.client import DropboxOAuth2Flow, DropboxClient
from .models import DropboxAccount, DropboxUser
from config.keys import keys
from channel_dropbox import tasks
#needed for webhook
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
import urllib
from hashlib import sha256
import hmac
import sys
import unicodedata
#logger
import logging
logger = logging.getLogger('channel')

#user = User.objects.create_user('770', 'lennon@effef.com', 'johnpassword')
#user.save()
APP_KEY = keys["DROPBOX"]["APP_KEY"]
APP_SECRET = keys["DROPBOX"]["APP_SECRET"]

login_url='/accounts/login/'
class AuthView(LoginRequiredMixin, View):
    """
        Check if user is already registered,
        if he is, he will have the access_token
        else he will be redirected to register to Dropbox
    """
    def __init__(self):
        pass

    #change for testing
    HOST = "daisychain.me"
    def get_redirect(self, request):
        default_url = '/'
        redirect_url = request.GET.get('next', None)
        if not redirect_url:
            redirect_url = default_url

        return redirect_url

    def set_host(self, request):
        global HOST
        #get the HOST; sanbox, staging or production
        full_uri = request.build_absolute_uri()
        if full_uri == full_uri.rsplit('.me')[0]:
            HOST = 'http://localhost:8000'
        else:
            HOST = full_uri.rsplit('.me')[0] + '.me'


    def error(self, request, **kwargs):
        url = '{}?status=error'.format(self.get_redirect(request))
        return redirect(url)

    def success(self, request):
        url = '{}?status=success'.format(self.get_redirect(request))
        return redirect(url)

    def get(self, request):

        logger.debug("Dropbox handling get-request")

        self.set_host(request)

        q_code = request.GET.get('code', False)

        if q_code is not False:
            return self._handle_api_callback(request)
        else:
            return self._handle_call(request)

    def _handle_call(self, request):
        """build Dropbox oauth uri and redirect there"""
        global HOST
        logger.debug("Dropbox handling get-request: identified as initial")

        try:
            #Check if user is already registered
            dbx_user = DropboxAccount.objects.get(user=request.user)
            return self.success(request)

        except DropboxAccount.DoesNotExist:
            pass

        redirect_dropbox =  HOST + "/dropbox/authenticate"
        authorize_url = DropboxOAuth2Flow(APP_KEY,
                                          APP_SECRET,
                                          redirect_dropbox,
                                          request.session,
                                          "dropbox-auth-csrf-token")\
                                          .start(self.get_redirect(request))

        return redirect(authorize_url)

    def _handle_api_callback(self, request):
        """handle redirect from instagram when user denied access"""
        global HOST
        logger.debug("Dropbox handling get-request: "
                  "identified as API callback")
        try:
            redirect_dropbox = HOST + "/dropbox/authenticate"
            access_token, userid, url_state = DropboxOAuth2Flow(APP_KEY,
                                                              APP_SECRET,
                                                              redirect_dropbox,
                                                              request.session,
                                                              "dropbox-auth-csrf-token"
                                                              ).finish(request.GET)

            return self._save_user(access_token, userid, url_state, request)

        except DropboxOAuth2Flow.BadRequestException as e:
            logger.error("[Dropbox - View - auth-finish] BadRequestException")
            return self.error(request)
        except DropboxOAuth2Flow.BadStateException as e:
            return redirect(reverse("dropbox:connect"))
        except DropboxOAuth2Flow.CsrfException as e:
            logger.error("[Dropbox - View - auth-finish] ... CsrfException")
            return self.error(request)
        except DropboxOAuth2Flow.NotApprovedException as e:
            logger.error("[Dropbox - View - auth-finish] ... 403")
            return self.error(request)
        except DropboxOAuth2Flow.ProviderException as e:
            logger.error("[Dropbox - View - auth-finish] ... NotApprovedException")
            return self.error(request)


    def _save_user(self, access_token, userid, url_state, request):
        dbx = dropbox.Dropbox(access_token)

        account = dbx.users_get_current_account()
        disk = dbx.users_get_space_usage()

        if disk.allocation.is_individual() is False:
            return self.error(request)

        init_dropbox_folder = dbx.files_list_folder(path='',
                                                    recursive=True,
                                                    include_media_info=True,
                                                    include_deleted=True)

        # to convert the bytes to megabytes
        MEGA_BYTE = 1000000
        used = (disk.used / MEGA_BYTE)
        allocated = (disk.allocation.get_individual().allocated / MEGA_BYTE)

        dropbox_account = DropboxAccount(user = request.user,
                                         access_token = access_token,
                                         cursor = init_dropbox_folder.cursor)
        dropbox_account.save()

        dropbox_user = DropboxUser(dropbox_account = dropbox_account,
                                   dropbox_userid = userid,
                                   display_name = account.name.display_name,
                                   email = account.email,
                                   profile_photo_url = account.profile_photo_url,
                                   disk_used = used,
                                   disk_allocated = allocated)
        dropbox_user.save()

        logger.debug('[Dropbox - View - auth-finish] \
            DropboxUser added to user: {}'.format(request.user.username))
        return self.success(request)

class SignoutView(LoginRequiredMixin, View):

    def get_redirect(self, request):
        default_url = '/'
        redirect_url = request.GET.get('next', None)
        if not redirect_url:
            redirect_url = default_url

        return redirect_url

    def success(self, request):
        url = '{}?status=success'.format(self.get_redirect(request))
        return redirect(url)

    def get(self, request):

        try:
            account = DropboxAccount.objects.get(user=request.user)
            account.delete()
        except DropboxAccount.DoesNotExist:
            pass

        return self.success(request)


class WebhookView(View):

    def get_redirect(self, request):
        default_url = '/'
        redirect_url = request.GET.get('next', None)
        if not redirect_url:
            redirect_url = default_url

        return redirect_url

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        """The requests to this view come without any csrf mechanism."""
        return super(WebhookView, self).dispatch(request, *args, **kwargs)

    def get(self, request):
        logger.debug("DropBox handling GET webhook")
        if request.method == "GET":
            logger.debug('[Dropbox - View - dropbox_call_webhook] \
                DropBox - send Hook-Test')
            return HttpResponse(request.GET.get('challenge'))

    def post(self, request):
        """Receive a list of changed user IDs from Dropbox and process each."""
        # Make sure this is a valid request from Dropbox
        logger.debug('[Dropbox - View - Webhook] received a webhook')
        signature = request.environ.get('HTTP_X_DROPBOX_SIGNATURE')
        try:
            request_body_size = int(request.environ.get('CONTENT_LENGTH', 0))
        except (ValueError):
            request_body_size = 0
            pass

        request_body = request.environ['wsgi.input'].read(request_body_size)
        request_hashed = hmac.new(  APP_SECRET.encode("utf-8"),
                                    request_body,
                                    sha256).hexdigest()

        if not hmac.compare_digest(signature, request_hashed):
            error_url = '{}?status=error'.format(self.get_redirect(request))
            return redirect(error_url)
        try:
            data = json.loads(request_body.decode('utf-8'))

            for user in data['delta']['users']:
                logger.debug('[Dropbox - View - webhook] \
                    firedTrigger for user with id:{}'.format(user))

                tasks.fireTrigger(user)
        except json.decoder.JSONDecodeError:
            pass
        return HttpResponse()
