from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class TwitterAccount(models.Model):
    """
        Twitter account model that stores the oauth token and secret
        for a given user.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=100)
    access_secret = models.CharField(max_length=100)

    class Meta:
        verbose_name = _("twitter account")
        verbose_name_plural = _("twitter accounts")

    def __str__(self):
        return "Twitter Account of user: {}".format(self.user)
