from django.core.urlresolvers import reverse
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.views.generic import View
from django.utils.translation import ugettext as _
from core.models import Channel, Trigger, Action
from core.utils import get_channel_instance


class ChannelListView(LoginRequiredMixin, View):

    def get(self, request):

        channels = Channel.objects.values()

        for channel in channels:

            name_lower = channel["name"].lower()
            detail_link = reverse("channels:detail", args=[name_lower])
            channel["detail_link"] = detail_link

            try:
                channel_instance = get_channel_instance(channel["name"])
            except ImportError:
                continue
            else:
                conn_state = channel_instance.user_is_connected(request.user)
                channel["connection_state"] = conn_state.name

        context = {
            "channel_list": channels
        }

        return render(request, 'channels/channel_list.html', context=context)


class ChannelDetailView(LoginRequiredMixin, View):

    def get(self, request, channelname):

        try:
            channel = Channel.objects.get(name__iexact=channelname)
            channel_instance = get_channel_instance(channelname)
        except (Channel.DoesNotExist, ImportError):
            messages.error(request, _("The selected channel does not exist"))
            return redirect("channels:list")

        triggers = Trigger.objects.filter(channel=channel)
        actions = Action.objects.filter(channel=channel)

        context = {
            'channel': channel,
            'trigger_list': triggers,
            'action_list': actions
        }

        name_lower = channelname.lower()

        auth_url = reverse("{}:connect".format(name_lower))
        auth_url += "?next=" + reverse("channels:detail", args=[name_lower])
        context['auth_url'] = auth_url

        unauth_url = reverse("{}:disconnect".format(name_lower))
        unauth_url += "?next=" + reverse("channels:detail", args=[name_lower])
        context['unauth_url'] = unauth_url

        connection_state = channel_instance.user_is_connected(request.user)
        context["connection_state"] = connection_state.name

        return render(request, 'channels/channel_detail.html', context=context)
