from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class MailAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    email_address = models.CharField(_('Email Address'), max_length=256)

    class Meta:
            verbose_name = _('EMail Account')
            verbose_name_plural = _('Email Account')


    def __str__(self):
        return 'Email Account: {}'.format(self.email_address)