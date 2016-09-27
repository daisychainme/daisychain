from django import forms
from nocaptcha_recaptcha.fields import NoReCaptchaField
from allauth.account.forms import SignupForm, ResetPasswordForm


class CaptchaSignupForm(SignupForm):

    captcha = NoReCaptchaField()

    def __init__(self, *args, **kwargs):
        super(CaptchaSignupForm, self).__init__(*args, **kwargs)

    def clean(self):
        super(CaptchaSignupForm, self).clean()
        return self.cleaned_data


class SilentResetPasswordForm(ResetPasswordForm):

    def clean_email(self):
        try:
            super(SilentResetPasswordForm, self).clean_email()
        except forms.ValidationError:
            # hide errormessage if it is not in db
            pass
        return self.cleaned_data["email"]

    def save(self, request, **kwargs):
        super(SilentResetPasswordForm, self).save(request, **kwargs)
        return self.cleaned_data["email"]
