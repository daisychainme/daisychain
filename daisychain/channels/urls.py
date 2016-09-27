from django.conf.urls import url

from channels import views

urlpatterns = [
    url(r'^$', views.ChannelListView.as_view(), name='list'),
    url(r'^([a-zA-Z0-9]+)$', views.ChannelDetailView.as_view(), name='detail'),
]
