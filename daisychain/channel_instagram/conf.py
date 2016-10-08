from config.keys import keys
from django.contrib.sites.models import Site
from logging import getLogger


log = getLogger("channel")

config = {
    "DJANGO_SECRET": keys["DJANGO"]["PRODUCTION"],

    "API_OAUTH_BASE_URI": "https://api.instagram.com/oauth",
    "API_BASE_URI": "https://api.instagram.com/v1",
    "API_MEDIA_ENDPOINT": "https://api.instagram.com/v1/media/%s",
    "API_USER_SELF_ENDPOINT": "https://api.instagram.com/v1/users/self",
    "API_SUBSCRIPTION_ENDPOINT": "https://api.instagram.com/v1/subscriptions"
}


class Config():

    def get(key, default=None):

        if key == "DOMAIN_BASE":
            return "https://{}".format(Site.objects.get_current().domain)
        elif key == "CLIENT_ID":
            domain_base = Site.objects.get_current().domain
            return keys["INSTAGRAM"][domain_base]["CLIENT_ID"]
        elif key == "CLIENT_SECRET":
            domain_base = Site.objects.get_current().domain
            return keys["INSTAGRAM"][domain_base]["CLIENT_SECRET"]

        try:
            return config[key]
        except KeyError as e:
            if default is not None:
                return default
            else:
                log.warning(("instagram.conf got request for non existent key "
                             "{}").format(key))
                raise e
