from django.conf.urls import url

from recipes import views

urlpatterns = [
    url(r'^$', views.RecipeListView.as_view(), name='list'),
    url(r'^new/?$', views.RecipeCreateResetView.as_view(), name='new'),
    url(r'^new/step1$',
        views.RecipeCreateTriggerChannelSelectionView.as_view(),
        name='new_step1'),
    url(r'^new/step2$',
        views.RecipeCreateTriggerSelectionView.as_view(),
        name='new_step2'),
    url(r'^new/step3$',
        views.RecipeCreateTriggerInputView.as_view(),
        name='new_step3'),
    url(r'^new/step4$',
        views.RecipeCreateActionChannelSelectionView.as_view(),
        name='new_step4'),
    url(r'^new/step5$',
        views.RecipeCreateActionSelectionView.as_view(),
        name='new_step5'),
    url(r'^new/step6$',
        views.RecipeCreateRecipeMappingView.as_view(),
        name='new_step6'),
    url(r'^new/step7$',
        views.RecipeCreateSaveView.as_view(),
        name='new_step7'),
    url(r'^edit/([0-9]+)/?$', views.RecipeEditView.as_view(), name='edit'),
    url(r'^toggle/([0-9]+)/?$', views.RecipeEditView.as_view(), name='toggle'),
    url(r'^delete/([0-9]+)/?',
        views.RecipeDeleteView.as_view(),
        name='delete'),
]
