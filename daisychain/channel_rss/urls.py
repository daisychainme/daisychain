from django.conf.urls import url, include

from channel_rss import views


urlpatterns = [
    url(r'^choose-feed',
        views.AuthenticationView.as_view(),
        name='connect'),
    url(r'^unauthenticate',
        views.EndAuthenticationView.as_view(),
        name='disconnect'),
    #url(r'^trigger-input',
     #   views.TriggerInputView.as_view(),
      #  name='trigger_input'),
]