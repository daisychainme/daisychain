from django.conf.urls import url
from channel_clock import views

urlpatterns = [
    url(r'^setup', views.SetupView.as_view(), name='connect'),
    url(r'^reset', views.ResetView.as_view(), name='disconnect'),
]
