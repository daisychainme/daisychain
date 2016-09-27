from django.shortcuts import render
from twython import Twython
from django.core.urlresolvers import reverse
from django.shortcuts import get_object_or_404
from django.views.generic import View
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.contrib.auth.mixins import LoginRequiredMixin

from config.keys import keys
from .models import TwitterAccount


CONSUMER_KEY = keys['TWITTER']['APP_KEY']
CONSUMER_SECRET = keys['TWITTER']['APP_SECRET']

login_url='/accounts/login/'


class StartAuthenticationView(LoginRequiredMixin, View):
    """
        Begin the authentication
    """

    def get(self, request):
        twitter = Twython(CONSUMER_KEY, CONSUMER_SECRET)

        # build the callback url that contains the pk of the user
        callback_url = request.build_absolute_uri(reverse('twitter:callback'))
                                                  #+ "?user_id=%s" % user_id)

        auth_tokens = twitter.get_authentication_tokens(callback_url)

        request.session['twitter_request_token'] = auth_tokens
        request.session['twitter_next_url'] = request.GET.get('next', None)

        return HttpResponseRedirect(auth_tokens['auth_url'])


class StopAuthenticationView(LoginRequiredMixin, View):
    """Delete authentication information from database"""

    def get(self, request):

        try:
            twitter_account = TwitterAccount.objects.get(user=request.user)
            twitter_account.delete()
        except TwitterAccount.DoesNotExist:
            pass

        redirect_url = request.GET.get('next', '/') + "?status=success"

        return HttpResponseRedirect(redirect_url)


class CallbackView(View):
    """
        Twitter will redirect the user via a callback url

    """

    def get(self, request):
        if not request.user.is_authenticated():
            return HttpResponseRedirect(login_url)

        default_url = '/'
        redirect_url = request.session.get('twitter_next_url')
        if not redirect_url:
            redirect_url = default_url

        verifier = request.GET.get('oauth_verifier')
        if not verifier:
            failure_url = '{}?status=error'.format(redirect_url)
            return HttpResponseRedirect(failure_url)

        # oauth token and secret are stored in the session
        oauth_token = request.session['twitter_request_token']['oauth_token']
        oauth_secret = request.session['twitter_request_token']['oauth_token_secret']
        # get the authorized tokens using the verifier
        twitter = Twython(CONSUMER_KEY, CONSUMER_SECRET,
                          oauth_token, oauth_secret)

        authorized_tokens = twitter.get_authorized_tokens(verifier)

        # create a TwitterAccount object to store token and secret
        try:
            # check if account already exists
            TwitterAccount.objects.get(user=request.user)
            success_url = '{}?status=success'.format(redirect_url)
            return HttpResponseRedirect(success_url)
        except:
            twitter_account = TwitterAccount()
            twitter_account.user = request.user
            twitter_account.access_token = authorized_tokens['oauth_token']
            twitter_account.access_secret = authorized_tokens['oauth_token_secret']
            twitter_account.save()

        success_url = '{}?status=success'.format(redirect_url)
        return HttpResponseRedirect(success_url)
