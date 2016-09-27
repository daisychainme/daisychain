from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from mock import Mock, patch

from channel_mail.channel import MailChannel
from channel_mail.models import MailAccount
from allauth.account.models import EmailAddress


class AuthenticationTest(TestCase):

    def setUp(self):
        self.user = self.create_user('mailuser',
                                     'mailing@mail.com',
                                     'Password')
        self.channel = MailChannel()
        self.client = Client()
        self.client.force_login(self.user)

    def create_user(self, username, email, password):
        user = User.objects.create_user(username,
                                        email,
                                        password)
        user.save()
        return user

    def create_mail_account(self, user):
        mail_account = MailAccount(user=user, email_address=user.email)
        mail_account.save()
        return mail_account

    def test_authentication_get_without_mail_account(self):
        response = self.client.get(reverse('mail:connect'))
        self.assertTemplateUsed(response=response,
                                template_name='channel_mail/choose_email.html')

    def test_authentication_get_with_existing_mail_account(self):
        self.create_mail_account(self.user)
        response = self.client.get(reverse('mail:connect'))
        self.assertRedirects(response,
                             '/?status=success',
                             status_code=302,
                             target_status_code=302)
        self.assertTemplateNotUsed(response=response,
                            template_name='channel_mail/choose_email.html')

    def test_authentication_post_valid_form_creates_mail_account(self):
        with self.assertRaises(MailAccount.DoesNotExist):
            MailAccount.objects.get(user=self.user)
        # create the form input
        chosen_email = EmailAddress(id=42,
                                    user=self.user,
                                    email="testmail@foo.bar",
                                    verified=True,
                                    primary=True)
        chosen_email.save()
        post_data = {'email_choice': chosen_email.email}
        response = self.client.post(reverse('mail:connect'), post_data)
        self.assertRedirects(response,
                             '/?status=success',
                             status_code=302,
                             target_status_code=302)
        mail_account = MailAccount.objects.get(user=self.user)
        self.assertEquals(mail_account.email_address, chosen_email.email)

    def test_authentication_post_invalid_form(self):
        actual_email = EmailAddress(id=42,
                                    user=self.user,
                                    email="testmail@foo.bar",
                                    verified=True,
                                    primary=True)
        actual_email.save()
        invalid_post_data = {'email_choice': 'other@foo.bar'}
        response = self.client.post(reverse('mail:connect'),
                                    invalid_post_data)
        self.assertTemplateUsed(response=response,
                                template_name='channel_mail/choose_email.html')
        # mail account should not be created
        with self.assertRaises(MailAccount.DoesNotExist):
            MailAccount.objects.get(user=self.user)

    def test_valid_post_with_next_url(self):
        with self.assertRaises(MailAccount.DoesNotExist):
            MailAccount.objects.get(user=self.user)
        # create the form input
        chosen_email = EmailAddress(id=42,
                                    user=self.user,
                                    email="testmail@foo.bar",
                                    verified=True,
                                    primary=True)
        chosen_email.save()
        post_data = {'email_choice': chosen_email.email}
        session = self.client.session
        session['mail_auth_next'] = '/recipes/new/step2'
        session.save()
        response = self.client.post(reverse('mail:connect'), post_data)
        self.assertRedirects(response,
                             '/recipes/new/step2?status=success',
                             status_code=302,
                             target_status_code=302)
        mail_account = MailAccount.objects.get(user=self.user)
        self.assertEquals(mail_account.email_address, chosen_email.email)

    def test_get_with_existing_account_and_next_url_parameter(self):
        self.create_mail_account(self.user)
        next_url = '/recipes/new/step2'
        complete_url = '{}?next={}'.format(reverse('mail:connect'),
                                         next_url)
        response = self.client.get(complete_url)
        self.assertRedirects(response,
                             '/recipes/new/step2?status=success',
                             status_code=302,
                             target_status_code=302)
        self.assertTemplateNotUsed(response=response,
                            template_name='channel_mail/choose_email.html')

    def test_disconnect_deleting_mail_account(self):
        self.create_mail_account(self.user)
        response = self.client.get(reverse('mail:disconnect'))
        with self.assertRaises(MailAccount.DoesNotExist):
            MailAccount.objects.get(user=self.user)
