from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.timezone import now


class FacebookAccount(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.TextField()
    username = models.CharField(max_length=256)
    expire_date = models.DateField(auto_now=False, auto_now_add=True)
    last_post_id = models.TextField()
    last_post_time = models.DateTimeField(default=now, blank=True)

    class Meta:
        verbose_name = _("Facebook Account")
        verbose_name_plural = _("Facebook Accounts")


    def __str__(self):
        return "Facebook Account of User: {}".format(self.user)