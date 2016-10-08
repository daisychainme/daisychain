from django.conf.urls import url, include
from django.views.generic import RedirectView, TemplateView
from . import views

urlpatterns = [
    url(r'^connect/',
        views.StartConnectionView.as_view(),
        name='connect'),

    url(r'^oauth-callback/',
        views.CallbackView.as_view(),
        name='callback'),

    url(r'^disconnect/',
        views.DisconnectView.as_view(),
        name='disconnect'),

]
