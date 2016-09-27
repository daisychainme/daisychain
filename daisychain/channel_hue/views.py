from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.views.generic import View
from django.shortcuts import redirect

from .models import HueAccount

import json
import requests

import logging
logger = logging.getLogger('channel')

login_url='/accounts/login/'
class RegisterView(LoginRequiredMixin, View):

    def get_redirect(self, request):
        default_url = '/'
        redirect_url = request.GET.get('next', None)

        if not redirect_url:
            redirect_url = default_url

        return redirect_url


    def error(self, request, **kwargs):
        url = '{}?status=error'.format(self.get_redirect(request))
        return redirect(url)


    def success(self, request):
        url = '{}?status=success'.format(self.get_redirect(request))
        return redirect(url)


    def get(self, request):
        try:
            #Check if user is already registered
            dbx_user = HueAccount.objects.get(user=request.user)
            return self.success(request)

        except HueAccount.DoesNotExist:
            pass

        req = requests.get('https://www.meethue.com/api/nupnp')

        bridge_ip = req.json()[0]['internalipaddress']

        # TODO press the bottom
        address = 'http://'+bridge_ip+'/api'
        data = '{"devicetype":"daisychain#'+request.user.username+'"}'

        res = requests.post(address, data)

        logger.debug('Response from Hue: {}'.format(json.dumps(res.json())))
        access_token = res.json()[0]['success']['username']
        if access_token is None:
            return self.error(request)

        hue = HueAccount(user = request.user,
                         bridge_ip=bridge_ip,
                         access_token=access_token)
        hue.save()
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
            account = HueAccount.objects.get(user=request.user)
            account.delete()
        except HueAccount.DoesNotExist:
            pass

        return self.success(request)
