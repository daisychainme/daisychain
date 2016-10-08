from core.channel import (Channel, NotSupportedTrigger, NotSupportedAction,
                          ConditionNotMet, ChannelStateForUser)
from .models import GmailAccount
from django.contrib.auth.models import User
import logging
import httplib2
from googleapiclient.discovery import build

from oauth2client.contrib.django_orm import Storage
from oauth2client import file, client, tools

import base64
from email.mime.text import MIMEText

#log = logging.getLogger("channel")

SEND_MAIL = 100

class GmailChannel(Channel):

    def user_is_connected(self, user):
        if GmailAccount.objects.filter(user=user).count() > 0:
            return ChannelStateForUser.connected
        else:
            return ChannelStateForUser.initial

    def fill_recipe_mappings(self, trigger_type, userid,
                             payload, conditions, mappings):
        """ Triggers are not yet supported by the mail channel """
        raise NotSupportedTrigger()

    def _create_message(self, sender, to, subject, message_text):
        """Create a message for an email.

        Args:
          sender: Email address of the sender.
          to: Email address of the receiver.
          subject: The subject of the email message.
          message_text: The text of the email message.

        Returns:
          An object containing a base64url encoded email object.
        """
        message = MIMEText(message_text, 'plain')
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        raw = base64.urlsafe_b64encode(message.as_bytes())
        raw = raw.decode()
        return {'raw': raw}

    def _send_message(self, service, user_id, message):
        """Send an email message.

        Args:
          service: Authorized Gmail API service instance.
          user_id: User's email address. The special value "me"
          can be used to indicate the authenticated user.
          message: Message to be sent.

        Returns:
          Sent Message.
        """
        message = (service.users().messages().send(userId=user_id, body=message).execute())
        return message

    #def _create_message_with_attachment(self, sender, to, subject, message_text, file):

        """Create a message for an email.

        Args:
        sender: Email address of the sender.
        to: Email address of the receiver.
        subject: The subject of the email message.
        message_text: The text of the email message.
        file: The path to the file to be attached.

        Returns:
        An object containing a base64url encoded email object.

        message = MIMEMultipart()
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject

        msg = MIMEText(message_text)
        message.attach(msg)

        content_type, encoding = mimetypes.guess_type(file)

        if content_type is None or encoding is not None:
            content_type = 'application/octet-stream'
        main_type, sub_type = content_type.split('/', 1)
        if main_type == 'text':
            fp = open(file, 'rb')
            msg = MIMEText(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'image':
            fp = open(file, 'rb')
            msg = MIMEImage(fp.read(), _subtype=sub_type)
            fp.close()
        elif main_type == 'audio':
            fp = open(file, 'rb')
            msg = MIMEAudio(fp.read(), _subtype=sub_type)
            fp.close()
        else:
            fp = open(file, 'rb')
            msg = MIMEBase(main_type, sub_type)
            msg.set_payload(fp.read())
            fp.close()
        filename = os.path.basename(file)
        msg.add_header('Content-Disposition', 'attachment', filename=filename)
        message.attach(msg)

        raw = base64.urlsafe_b64encode(message.as_bytes())
        raw = raw.decode()
        return {'raw': raw}
        """
    def handle_action(self, action_type, userid, inputs):

        """Execute the action specified in action_type using userid and inputs.

        This method is called by worker threads when they process a trigger
        and any action of this channel is requested.

        Args:
            action_type (int): as defined in model Action.action_type
            userid (int): the user to whom the action belongs
            inputs (dict): the values that have been filled in another
                channel's get_trigger_inputs() and shall be used in this
                action

        Returns:
            void
        """
        try:
            user = User.objects.get(id=userid)
        except User.DoesNotExist:
            #log.error("User does not exist")
            return

        if (action_type == SEND_MAIL):
            # user credentials fehlerbehandlung
            gmailuser = GmailAccount.objects.get(user=user)

            storage = Storage(GmailAccount, 'user_id', user, 'credentials')
            credentials = storage.get()
            #log.debug(credentials.client_id)

            http = httplib2.Http()
            http = credentials.authorize(http)
            service = build('gmail', 'v1', http=credentials.authorize(http))

            msg = self._create_message(inputs['sender'], inputs['to'], inputs['subject'], inputs['message'])
            self._send_message(service, "me", msg)


        else:
            raise NotSupportedAction("This action is not supported!")


