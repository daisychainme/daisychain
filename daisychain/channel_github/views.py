from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.core.urlresolvers import reverse

import requests
import json
from uuid import uuid4
from urllib.parse import urlencode

from config.keys import keys
from core.models import Trigger, TriggerInput
from recipes.util import Draft
from channel_github.models import GithubAccount
from channel_github.forms import TriggerInputForm
from channel_github.channel import GithubChannel
from channel_github.config import EVENTS

CLIENT_ID = keys['GITHUB']['CLIENT_ID']
CLIENT_SECRET = keys['GITHUB']['CLIENT_SECRET']

user_url = 'https://api.github.com/user'
base_auth_url = 'https://github.com/login/oauth/authorize?'
access_token_url = 'https://github.com/login/oauth/access_token'


class StartAuthenticationView(LoginRequiredMixin, View):

    def get(self, request):
        callback_url = request.build_absolute_uri(reverse('github:callback'))
        state_string = str(uuid4())
        scopes = 'repo'
        params = {
                  'client_id': CLIENT_ID,
                  'state': state_string,
                  'scope': scopes
                 }
        oauth_url = ''.join((base_auth_url, urlencode(params)))
        # url the user is redirected after callback.
        request.session['github_next_url'] = request.GET.get('next', None)
        request.session['state'] = state_string
        return HttpResponseRedirect(oauth_url)


class StopAuthenticationView(LoginRequiredMixin, View):

    def get(self, request):

        try:
            github_account = GithubAccount.objects.get(user=request.user)
            github_account.delete()
        except GithubAccount.DoesNotExist:
            pass

        redirect_url = request.GET.get('next', '/') + "?status=success"
        return HttpResponseRedirect(redirect_url)


class CallbackView(View):

    def get(self, request):
        if not request.user.is_authenticated():
            return HttpResponseBadRequest()

        if request.session['state'] != request.GET['state']:
            return HttpResponseBadRequest()

        default_url = '/'
        redirect_url = request.session.get('github_next_url', None)
        if not redirect_url:
            redirect_url = default_url
        success_url = '{}?status=success'.format(redirect_url)

        code = request.GET.get('code', None)
        if not code:
            failure_url = '{}?status=error'.format(redirect_url)
            return HttpResponseRedirect(failure_url)

        data = {
                'client_id': CLIENT_ID,
                'client_secret': CLIENT_SECRET,
                'code': code
                }
        resp = requests.post(access_token_url, json=data,
                            headers={'Accept': 'application/json'})

        if not resp.ok:
            return HttpResponseBadRequest()

        access_token = resp.json()['access_token']
        # get username
        user_resp = requests.get(user_url,
                         headers={'Authorization': 'token ' + access_token})
        if not user_resp.ok:
            return HttpResponseBadRequest()
        username = user_resp.json()['login']

        # create account if it does not already exist
        try:
            existing_account = GithubAccount.objects.get(user=request.user)
            existing_account.access_token = access_token
            existing_account.username = username
            existing_account.save()
            return HttpResponseRedirect(success_url)
        except:
            github_account = GithubAccount(user=request.user,
                                       access_token=access_token,
                                       username=username)
            github_account.save()

        return HttpResponseRedirect(success_url)


class WebhookView(View):

    def get(self, request):
        return HttpResponseRedirect('/')

    def post(self, request):
        """
        Handles the POST request that is sent by Github when
        a webhook event takes place.
        """
        data = json.loads(request.body.decode("utf-8"))
        # get the data to the channel
        GithubChannel().fire_trigger(data)
        return HttpResponse()


class TriggerInputView(LoginRequiredMixin, View):

    @Draft.activate
    def get(self, request, draft):
        if 'trigger_id' not in draft:
            return redirect('recipes:new_step2')
        # next_url should be the url of get trigger inputs
        auth_url = '{}?next={}'.format(reverse('github:connect'),
                                       reverse('github:get_trigger_inputs'))
        return redirect(auth_url)


class CreateTriggerInputsView(LoginRequiredMixin, View):

    @Draft.activate
    def get(self, request, draft):
        # should be called after step 2
        if 'trigger_id' not in draft:
            return redirect('recipes:new_step2')
        # github account should be authorized
        try:
            github_account = GithubAccount.objects.get(user=request.user)
        except:
            auth_url = '{}?next={}'.format(reverse('github:connect'),
                                           reverse('github:get_trigger_inputs'))
            return redirect(auth_url)

        form = TriggerInputForm(
                       initial={'repository_name':
                       "Enter a repository you own"})

        return render(request, 'channel_github/trigger_input.html',
                      {'form': form})

    @Draft.activate
    def post(self, request, draft):
        # should be called after step 2
        if 'trigger_id' not in draft:
            return redirect('recipes:new_step2')
        # github account should be authorized
        try:
            github_account = GithubAccount.objects.get(user=request.user)
        except:
            auth_url = '{}?next={}'.format(reverse('github:connect'),
                                           reverse('github:get_trigger_inputs'))
            return redirect(auth_url)

        # process form input
        form = TriggerInputForm(request.POST)

        if form.is_valid():
            trigger = Trigger.objects.get(pk=draft['trigger_id'])
            events = EVENTS[trigger.trigger_type]
            repository_name = form.cleaned_data['repository_name']
            github = GithubChannel()
            # check if github repo exists
            if not github.repo_exists(repo_name=repository_name,
                                      owner=github_account.username):
                return render(request,
                              'channel_github/trigger_input.html',
                              {'form': form,
                               'repo_error': "This Repository does not exist."})

            full_repo_name = github.create_webhook(
                                             github_account=github_account,
                                             repository=repository_name,
                                             events=events)
            # check if the creation of the webhook was sucessfull.
            if not full_repo_name:
                return redirect('github:trigger_input')
            else:
                # save trigger input in draft object.
                # TODO more general implementation
                trigger_input = TriggerInput.objects.get(
                                             trigger_id=draft['trigger_id'])
                draft['recipe_conditions'] = [{
                    'id': trigger_input.id,
                    'value': full_repo_name
                }]
                return HttpResponseRedirect(reverse('recipes:new_step4'))
        else:
            return render(request,
                          'channel_github/trigger_input.html',
                          {'form': form})




# @Draft.activate
# def get_trigger_inputs(request, draft):#, draft):
#     # should be called after step 2
#     if 'trigger_id' not in draft:
#         return redirect('recipes:new_step2')
#     # github account should be authorized
#     try:
#         github_account = GithubAccount.objects.get(user=request.user)
#     except:
#         auth_url = '{}?next={}'.format(reverse('github:connect'),
#                                        reverse('github:get_trigger_inputs'))
#         return redirect(auth_url)

#     # if this is a POST request we need to process the form data
#     if request.method == 'POST':
#         # create a form instance and populate it with data from the request:
#         form = TriggerInputForm(request.POST)
#         if form.is_valid():
#             trigger = Trigger.objects.get(pk=draft['trigger_id'])
#             events = EVENTS[trigger.trigger_type]
#             repository_name = form.cleaned_data['repository_name']
#             github = GithubChannel()
#             full_repo_name = github.create_webhook(
#                                              github_account=github_account,
#                                              repository=repository_name,
#                                              events=events)
#             # check if the creation of the webhook was sucessfull.
#             if not full_repo_name:
#                 return redirect('github:trigger_input')
#             else:
#                 # save trigger input in draft object.
#                 # TODO more general implementation
#                 trigger_input = TriggerInput.objects.get(trigger_id=draft['trigger_id'])
#                 draft['recipe_conditions'] = {
#                     'id': trigger_input.id,
#                     'value': full_repo_name
#                 }
#                 return HttpResponseRedirect(reverse('recipes:new_step4'))

#     else:
#         form = TriggerInputForm(
#                        initial={'repository_name':
#                        "Enter a repository you own"})

#     return render(request, 'channel_github/trigger_input.html',
#                   {'form': form})
