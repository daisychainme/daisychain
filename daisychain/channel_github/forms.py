from django import forms


class TriggerInputForm(forms.Form):

    repository_name = forms.CharField(label='Repository', max_length=256)
