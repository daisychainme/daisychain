from django.conf.urls import url

from home import views

urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'profile/?$', views.ProfileView.as_view(), name='profile'),
    url(r'^impressum$', views.ImpressumView.as_view(), name='impressum'),
    url(r'^privacy_policy$',
        views.PrivacyPolicyView.as_view(),
        name='privacypolicy'),
]
