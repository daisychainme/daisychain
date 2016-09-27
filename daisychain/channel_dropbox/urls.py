from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    url(r'^authenticate', views.AuthView.as_view(), name='connect'),
    url(r'^unauthenticate', views.SignoutView.as_view(), name='disconnect'),
    url(r'webhook$', views.WebhookView.as_view(), name='webhook'),

]
