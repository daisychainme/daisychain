from django.conf.urls import url
from django.views.decorators.csrf import csrf_exempt


from channel_github import views

urlpatterns = [
    url(r'^authenticate',
        views.StartAuthenticationView.as_view(),
        name='connect'),
    url(r'^oauth-callback',
        views.CallbackView.as_view(),
        name='callback'),
    url(r'^unauthenticate',
        views.StopAuthenticationView.as_view(),
        name='disconnect'),
    url(r'^hooks',
        csrf_exempt(views.WebhookView.as_view()),
        name='hooks'),
    url(r'^trigger-input',
        views.TriggerInputView.as_view(),
        name='trigger_input'),
    url(r'^create-trigger-inputs$',
        views.CreateTriggerInputsView.as_view(),
        name='get_trigger_inputs'),
]
