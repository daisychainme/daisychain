from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils import timezone
import django

class DropboxAccount(models.Model):
    """
        Dropbox account model that stores the access token and cursor
        for a given user.
        'cursor' - is used to save the last changed_file
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.CharField(_("Access Token"), max_length=255)
    cursor = models.CharField(_("Cursor"), max_length=255)

    class Meta:
        verbose_name = _("Dropbox Account")
        verbose_name_plural = _("Dropbox Accounts")

    def __str__(self):
        return "DropboxAccount belongs to user {}".format(
            self.user)

class DropboxUser(models.Model):
    """
        Dropbox user model that stores user_information.

        Fields:
            'dropbox_userid' - is used to find the user when the
            webhook is received.
            the other fields are used to save the user informations.
            the changes are used for a trigger (pk=7705)
    """
    dropbox_account = models.ForeignKey(DropboxAccount, on_delete=models.CASCADE)
    dropbox_userid = models.CharField(_("DropBox User ID"), null=False, max_length=255)
    display_name = models.CharField(_("DropBox Display Name"), max_length=100)
    email = models.CharField(_("email"),  max_length=100)
    profile_photo_url =  models.CharField(_("email"), null=True, max_length=255)
    disk_used = models.DecimalField(_("Used Disk Space"),  max_digits=12, decimal_places=4)
    disk_allocated = models.DecimalField(_("Total Allocated Disk Usage"), max_digits=12, decimal_places=4)

    class Meta:
        verbose_name = _("Dropbox User")
        verbose_name_plural = _("Dropbox Users")

    def __str__(self):
        return "Dropbox User #{} belongs to DropboxAccount {}".format(
            self.dropbox_userid, self.dropbox_account)
