from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin

from recipes.util import Draft
from channel_rss.forms import TriggerInputForm
from core.models import Trigger, TriggerInput


from logging import getLogger


class AuthenticationView(View):

    def get(self, request):
        redirect_url = request.GET.get('next', '/') + "?status=success"
        return redirect(redirect_url)


class EndAuthenticationView(View):

    def get(self, request):
        redirect_url = request.GET.get('next', '/') + "?status=success"
        return redirect(redirect_url)