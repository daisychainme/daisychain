from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import ugettext_lazy as _

# Create your models here.
class ClockUserSettings(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    utcoffset = models.SmallIntegerField(_("UTC Offset in minutes"))

    class Meta:
        verbose_name = _("Clock User Settings")
        verbose_name_plural = _("Clock User Settings")

    def __str__(self):
        return "Clock settings for user {} (id={})".format(self.user.username,
                                                           self.user.id)
