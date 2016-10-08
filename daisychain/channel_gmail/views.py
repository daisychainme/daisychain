from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.core.urlresolvers import reverse

from oauth2client.client import OAuth2WebServerFlow
from config.keys import keys
from .models import GmailAccount

import logging

CLIENT_ID = keys["GMAIL"]["APP_KEY"]
CLIENT_SECRET = keys["GMAIL"]["APP_SECRET"]

#log = logging.getLogger("channel")


class StartConnectionView(LoginRequiredMixin, View):

    def get(self, request):
        flow = OAuth2WebServerFlow(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=request.build_absolute_uri(reverse('gmail:callback')),
            scope='https://www.googleapis.com/auth/gmail.send',
        )
        #log.debug(flow.redirect_uri)
        auth_uri = flow.step1_get_authorize_url()

        try:
            GmailAccount.objects.get(user=request.user)
            #return HttpResponseRedirect(auth_uri)
        except GmailAccount.DoesNotExist:
            pass

        GmailAccount(user=request.user, flow=flow).save()

        return HttpResponseRedirect(auth_uri)


class CallbackView(View):

    def get(self, request):

        if not request.user.is_authenticated():
            return HttpResponseBadRequest()

        code = request.GET.get('code', None)

        if code is None:
            return HttpResponseBadRequest()

        try:
            gmail_user = GmailAccount.objects.get(user=request.user)
            flow = gmail_user.flow
        except GmailAccount.DoesNotExist:
            gmail_user = GmailAccount(user=request.user, flow = OAuth2WebServerFlow(
                                                    client_id=CLIENT_ID,
                                                    client_secret=CLIENT_SECRET,
                                                    redirect_uri=request.build_absolute_uri(reverse('gmail:callback')),
                                                    scope='https://www.googleapis.com/auth/gmail.send',
                                                    ))
            gmail_user.save()
            flow = gmail_user.flow


        credentials = flow.step2_exchange(code)

        account = GmailAccount.objects.get(user=request.user)
        account.credentials = credentials
        account.flow = flow
        account.save()

        redirect_url = request.GET.get('next', reverse('channels:list')) + "?status=success"
        #log.debug(redirect_url)
        return HttpResponseRedirect(redirect_url)


class DisconnectView(LoginRequiredMixin, View):

    def get(self, request):
        try:
            gmail_account = GmailAccount.objects.get(user=request.user)
            gmail_account.delete()
        except GmailAccount.DoesNotExist:
            pass

        return HttpResponseRedirect(reverse('channels:list'))