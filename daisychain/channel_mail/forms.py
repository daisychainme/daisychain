from django import forms
from allauth.account.models import EmailAddress


class EmailModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        # only the email address should be displayed
        return obj.email


class EmailForm(forms.Form):

    email_choice = EmailModelChoiceField(queryset=None)

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # get the confirmed emails of the account as the queryset
        queryset = EmailAddress.objects.filter(user=user, verified=True)
        self.fields['email_choice'].queryset = queryset
        self.fields['email_choice'].empty_label = None
        self.fields['email_choice'].to_field_name = 'email'
        self.fields['email_choice'].label = 'Choose a verified email you own'