from django.conf.urls import url, include

from channel_mail import views


urlpatterns = [
    url(r'^choose-email',
        views.AuthenticationView.as_view(),
        name='connect'),
    url(r'^disconnect',
        views.EndAuthenticationView.as_view(),
        name='disconnect'),
]
