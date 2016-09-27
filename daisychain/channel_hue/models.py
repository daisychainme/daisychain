from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User


class HueAccount(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    bridge_ip = models.CharField(_("Bridge IP"), max_length=32)
    access_token = models.CharField(_("Access Token"), max_length=100)

    class Meta:
        verbose_name = _("Phillips HUE Account")

    def __str__(self):
        return "Phillips HUE got User {}".format(
                self.user)
