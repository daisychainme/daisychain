from django.views.generic.base import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin


class HomeView(TemplateView):
    template_name = 'home/index.html'


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = 'home/profile.html'


class ImpressumView(TemplateView):
    template_name = 'home/impressum.html'


class PrivacyPolicyView(TemplateView):
    template_name = 'home/privacy_policy.html'
