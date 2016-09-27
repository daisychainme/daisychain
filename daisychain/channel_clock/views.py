from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic import View
from urllib.parse import urlsplit, parse_qs, urlencode, urlunsplit
from channel_clock.channel import ClockChannel
from channel_clock.models import ClockUserSettings
from channel_clock.timezones import timezones

DEFAULT_OAUTH_NEXT_URI = "/"
SESSKEY_OAUTH_NEXT_URI = "clock_oauth_next_uri"

class SetupView(LoginRequiredMixin, View):

    def fetch_next_uri(self, request):

        if SESSKEY_OAUTH_NEXT_URI in request.session:
            return

        # get ?next= parameter and store it in session, default to root
        q_next = request.GET.get('next', DEFAULT_OAUTH_NEXT_URI)
        request.session[SESSKEY_OAUTH_NEXT_URI] = q_next

    def get_next_uri(self, request):
        try:
            return request.session[SESSKEY_OAUTH_NEXT_URI]
        except KeyError:
            return DEFAULT_OAUTH_NEXT_URI

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

    def get(self, request):

        self.fetch_next_uri(request)

        if ClockChannel().user_is_connected(request.user):
            return self.success(request)

        context = {'timezones': timezones}

        return render(request, 'channel_clock/setup.html', context=context)

    def post(self, request):

        offset = request.POST.get("offset", 0)

        try:
            ClockUserSettings(user=request.user, utcoffset=offset).save()
        except:
            return self.error(request, type="django.db")
        else:
            return self.success(request)

class ResetView(LoginRequiredMixin, View):

    def get(self, request):

        redirect_url = request.GET.get('next', '/')

        try:
            ClockUserSettings.objects.get(user=request.user).delete()
        except:
            return redirect(redirect_url + "?status=error")
        else:
            return redirect(redirect_url + "?status=success")
