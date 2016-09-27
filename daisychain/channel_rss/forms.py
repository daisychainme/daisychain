from django import forms


class TriggerInputForm(forms.Form):

    feed_url = forms.CharField(label='URL to feed', max_length=2000)
