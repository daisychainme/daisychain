from django.conf.urls import url, include
from django.conf import settings
from django.conf.urls.static import static

from . import views

urlpatterns = [
    url(r'^oauth', views.OAuthView.as_view(), name='connect'),
    url(r'^signout', views.SignoutView.as_view(), name='disconnect'),
    url(r'^subscription', views.SubscriptionView.as_view(),
        name='subscription'),
]
