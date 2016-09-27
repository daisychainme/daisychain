import logging
from django.core.mail import EmailMessage
from django.contrib.auth.models import User

from core.core import Core
from core.channel import (Channel, NotSupportedTrigger, NotSupportedAction,
                          ConditionNotMet, ChannelStateForUser)
from channel_mail.models import MailAccount
from channel_mail.config import SEND_EMAIL


log = logging.getLogger('channel')


class MailChannel(Channel):

    def send_email(self, mail_account, subject, body):
        """
        Send an email as the result of an action.

        Parameters
        ----------
        mail_account: MailAccount
            MailAccount correspoding to the user the mail is sent to
        body: str
        subject: str

        Returns
        -------
        resp: int
            1 if the message was sent successfully, 0 otherwise.
        """
        log.debug('send_email: mail account{} subject:{}, body{}'.format(
                                                             mail_account,
                                                             subject,
                                                             body))
        if not type(subject) is str or not type(body) is str:
            log.error("send_email should only be called with a string.")
            raise TypeError("Should only be called with a string.")

        recipient = [mail_account.email_address]
        log.debug('send_email: recipient'.format(recipient))
        email = EmailMessage(subject=subject,
                             body=body,
                             to=recipient)
        resp = 0
        try:
            resp = email.send()
        except Exception as e:
            log.error('Error sending email via mail channel: {}'.format(e))
        log.debug('mail sent, resp: {}'.format(resp))
        return resp

    def handle_action(self, action_type, userid, inputs):
        log.debug("handle action: action_type: {} userid: {}, inputs: {}".format(action_type,
                                                                                 userid,
                                                                                 inputs))
        try:
            user = User.objects.get(pk=userid)
        except User.DoesNotExist:
            log.error("User does not exist")
            return

        try:
            mail_account = MailAccount.objects.get(user=user)
        except MailAccount.DoesNotExist:
            log.error('No MailAccount corresponding to the user')
            return

        # action
        if action_type == SEND_EMAIL:
            log.debug('handle action: send_email called')
            self.send_email(mail_account=mail_account,
                            subject=inputs['subject'],
                            body=inputs['body'])
        else:
            raise NotSupportedAction()

    def fill_recipe_mappings(self, trigger_type, userid,
                             payload, conditions, mappings):
        """ Triggers are not yet supported by the mail channel """
        raise NotSupportedTrigger()

    def user_is_connected(self, user):
        """
        Check whether a user is authenticated.
        In this context authenticated means connected to the mail channel
        by specifying an email address.
        """
        if MailAccount.objects.filter(user=user).count() > 0:
            return ChannelStateForUser.connected
        else:
            return ChannelStateForUser.initial
