from django.test import TestCase
from django.contrib.auth.models import User
from mock import Mock, patch

from channel_mail.channel import MailChannel
from channel_mail.models import MailAccount
from channel_mail.config import SEND_EMAIL
from core.channel import NotSupportedAction, ChannelStateForUser


class ChannelTest(TestCase):

    def setUp(self):
        self.user = self.create_user('mailuser',
                                     'mailing@mail.com',
                                     'Password')
        self.mail_account = self.create_mail_account(self.user)
        self.channel = MailChannel()

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

    def test_user_is_connected_returns_true(self):
        self.assertEquals(
                ChannelStateForUser.connected,
                self.channel.user_is_connected(self.user))

    def test_user_is_connected_without_authentication_returns_false(self):
        disconnected_user = self.create_user('unauth',
                                             'test@example.com',
                                             'hunter2')
        self.assertEquals(
                ChannelStateForUser.initial,
                self.channel.user_is_connected(disconnected_user))

    def test_send_email(self):
        resp = self.channel.send_email(mail_account=self.mail_account,
                                       subject='testing mail',
                                       body='just a test')
        self.assertEquals(resp, 1)

    @patch('django.core.mail.EmailMessage.send')
    def test_send_email_raising_exception(self, mock_send):
        mock_send.side_effect = Exception('test exception')
        resp = self.channel.send_email(mail_account=self.mail_account,
                                       subject='testing mail',
                                       body='just a test')
        self.assertEquals(resp, 0)

    @patch('channel_mail.channel.MailChannel.send_email')
    def test_handle_action_send_mail_success(self, mock_send_email):
        inputs = {
            'subject': 'test_subject',
            'body': 'test_body'
        }
        self.channel.handle_action(action_type=SEND_EMAIL,
                                              userid=self.user.id,
                                              inputs=inputs)
        mock_send_email.assert_called_once_with(mail_account=self.mail_account,
                                                subject=inputs['subject'],
                                                body=inputs['body'])

    @patch('channel_mail.channel.MailChannel.send_email')
    def test_handle_action_send_mail_wrong_action_type(self, mock_send_email):
        inputs = {
            'subject': 'test_subject',
            'body': 'test_body'
        }

        with self.assertRaises(NotSupportedAction):
            self.channel.handle_action(action_type=-42,
                                              userid=self.user.id,
                                              inputs=inputs)
        mock_send_email.assert_not_called()

    @patch('channel_mail.channel.MailChannel.send_email')
    def test_handle_action_send_mail_wrong_user_id(self, mock_send_email):
        inputs = {
            'subject': 'test_subject',
            'body': 'test_body'
        }

        self.channel.handle_action(action_type=SEND_EMAIL,
                                   userid=-999,
                                   inputs=inputs)
        mock_send_email.assert_not_called()

    @patch('channel_mail.channel.MailChannel.send_email')
    def test_handle_action_send_mail_without_auth(self, mock_send_email):
        inputs = {
            'subject': 'test_subject',
            'body': 'test_body'
        }
        disconnected_user = self.create_user('unauth',
                                                'test@example.com',
                                                'hunter2')

        self.channel.handle_action(action_type=SEND_EMAIL,
                                       userid=disconnected_user.id,
                                       inputs=inputs)
        mock_send_email.assert_not_called()

    def test_send_email_subject_or_body_not_being_string(self):
        s = '42'
        b = 24
        with self.assertRaises(TypeError):
            self.channel.send_email(mail_account=self.mail_account,
                                    subject=s,
                                    body=b)
        s = 42
        b = '24'
        with self.assertRaises(TypeError):
            self.channel.send_email(mail_account=self.mail_account,
                                    subject=s,
                                    body=b)
        s = 42
        b = 24
        with self.assertRaises(TypeError):
            self.channel.send_email(mail_account=self.mail_account,
                                    subject=s,
                                    body=b)
