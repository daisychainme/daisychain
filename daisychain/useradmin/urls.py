from django.conf.urls import url

from useradmin import views

urlpatterns = [
    url(r'^$', views.UserTableView.as_view(), name='usertable'),
]
