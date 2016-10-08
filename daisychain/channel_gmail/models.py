from django.utils.translation import ugettext_lazy as _

from django.contrib.auth.models import User
from django.db import models
from oauth2client.contrib.django_orm import FlowField
from oauth2client.contrib.django_orm import CredentialsField


class GmailAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    credentials = CredentialsField()
    flow = FlowField()

    class Meta:
        verbose_name = _("Gmail account")
        verbose_name_plural = _("Gmail accounts")
