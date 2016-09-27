from django.conf.urls import url, include


from . import views

urlpatterns = [
    url(r'^oauth-start/',
        views.StartAuthenticationView.as_view(),
        name='connect'),

    # callback url, that is for Twitter's OAuth
    url(r'^oauth-callback/',
        views.CallbackView.as_view(),
        name='callback'),

    url(r'^oauth-stop/',
        views.StopAuthenticationView.as_view(),
        name='disconnect'),
]
