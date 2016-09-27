from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User


class InstagramAccount(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    instagram_id = models.CharField(_("Instagram ID"), max_length=32)
    access_token = models.CharField(_("Access Token"), max_length=100)

    class Meta:
        verbose_name = _("Instagram Account")
        verbose_name_plural = _("Instagram Accounts")

    def __str__(self):
        return "Instagram Account #{} belongs to user {}".format(
                self.instagram_id,
                self.user)
