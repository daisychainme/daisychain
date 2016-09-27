from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _


class GithubAccount(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=100)
    username = models.CharField(max_length=256)

    class Meta:
        verbose_name = _("github account")
        verbose_name_plural = _("github accounts")

    def __str__(self):
        return "Github Account of user: {}".format(self.user)
