"""daisychain URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.views.generic import RedirectView

import json

admin.autodiscover()

urlpatterns = [
    url(r'^$', RedirectView.as_view(url='/home')),
    url(r'^home/', include('home.urls', namespace='home')),
    url(r'^useradmin/', include('useradmin.urls', namespace='useradmin')),
    url(r'^channels/', include('channels.urls', namespace='channels')),
    url(r'^recipes/', include('recipes.urls', namespace='recipes')),
    url(r'^admin/', admin.site.urls),
    url(r'^clock/', include('channel_clock.urls', namespace='clock')),
    url(r'^dropbox/', include('channel_dropbox.urls', namespace='dropbox')),
    url(r'^hue/', include('channel_hue.urls', namespace='hue')),
    url(r'^github/', include('channel_github.urls', namespace='github')),
    url(r'^twitter/', include('channel_twitter.urls', namespace='twitter')),
    url(r'^instagram/',
        include('channel_instagram.urls', namespace='instagram')),
    url(r'rss/', include('channel_rss.urls', namespace='rss')),
    url(r'^mail/', include('channel_mail.urls', namespace='mail')),
    url(r"^accounts/", include('allauth.urls')),
    url(r'^facebook/', include('channel_facebook.urls', namespace='facebook')),
]
