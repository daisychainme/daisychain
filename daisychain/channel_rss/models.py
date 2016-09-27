from django.db import models
from django.utils.translation import ugettext_lazy as _


class RssFeed(models.Model):
    feed_url = models.CharField(_('Feed URL'), max_length=2000)
    last_modified = models.DateTimeField(null=True)

    def __str__(self):
        return 'RSS feed, url: {}, last_modified: {}'.format(self.feed_url,
                                                             self.last_modified)
