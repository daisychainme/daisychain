from config.keys import keys
from logging import getLogger


log = getLogger("channel")


config = {
    "DJANGO_SECRET": keys["DJANGO"]["PRODUCTION"],
    "CLIENT_ID": keys["INSTAGRAM"]["CLIENT_ID"],
    "CLIENT_SECRET": keys["INSTAGRAM"]["CLIENT_SECRET"],

    "DOMAIN_BASE": "",

    "API_OAUTH_BASE_URI": "https://api.instagram.com/oauth",
    "API_BASE_URI": "https://api.instagram.com/v1",
    "API_MEDIA_ENDPOINT": "https://api.instagram.com/v1/media/%s",
    "API_USER_SELF_ENDPOINT": "https://api.instagram.com/v1/users/self",
    "API_SUBSCRIPTION_ENDPOINT": "https://api.instagram.com/v1/subscriptions"
}


class Config():

    def get(key, default=None):
        try:
            return config[key]
        except KeyError as e:
            if default is not None:
                return default
            else:
                log.warning(("instagram.conf got request for non existent key "
                             "{}").format(key))
                raise e

    def set_domain_base(base):
        if base.endswith("/"):
            config["DOMAIN_BASE"] = base[:-1]
        else:
            config["DOMAIN_BASE"] = base
