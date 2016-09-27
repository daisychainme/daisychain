from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib.auth.mixins import LoginRequiredMixin

from logging import getLogger

from channel_mail.models import MailAccount
from channel_mail.forms import EmailForm


log = getLogger('channel')


class AuthenticationView(LoginRequiredMixin, View):
    """
    Views to authenticate the mail address of a user, i.e. specify a confirmed
    email address that shall be used to sent messages to.
    During the process of authentication a MailAccount object is created.
    """

    def get(self, request):
        # Check for model instance, i.e. email is chosen
        redirect_url = request.GET.get('next', '/') + '?status=success'
        try:
            MailAccount.objects.get(user=request.user)
            return redirect(redirect_url)
        except MailAccount.DoesNotExist:
            # new entry has to be created.
            pass
        request.session['mail_auth_next'] = redirect_url
        form = EmailForm(user=request.user)
        return render(request,
                      'channel_mail/choose_email.html',
                      {'form': form})


    def post(self, request):
        form = EmailForm(request.user, request.POST)
        if form.is_valid():
            # create mail account
            email = form.cleaned_data['email_choice'].email
            mail_account = MailAccount(user=request.user,
                                       email_address=email)
            mail_account.save()
            redirect_url = request.session.get('mail_auth_next', '/')
            return redirect(redirect_url + '?status=success')
        else:
            return render(request, 'channel_mail/choose_email.html',
                          {'form': form})


class EndAuthenticationView(LoginRequiredMixin, View):

    def get(self, request):
        try:
            mail_account = MailAccount.objects.get(user=request.user)
            mail_account.delete()
        except MailAccount.DoesNotExist:
            pass

        redirect_url = request.GET.get('next', '/') + "?status=success"
        return redirect(redirect_url)
