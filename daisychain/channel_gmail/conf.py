from config.keys import keys
from logging import getLogger


log = getLogger("channel")


config = {
    "DJANGO_SECRET": keys["DJANGO"]["PRODUCTION"],
    "CLIENT_ID": keys["GMAIL"]["CLIENT_ID"],
    "CLIENT_SECRET": keys["GMAIL"]["CLIENT_SECRET"],

    "DOMAIN_BASE": "",

    "API_OAUTH_BASE_URI": "https://api.gmail.com/oauth",
    "API_BASE_URI": "https://api.gmail.com/oauthcallback",
}


class Config():

    def get(key, default=None):
        try:
            return config[key]
        except KeyError as e:
            if default is not None:
                return default
            else:
                log.warning(("gmail.conf got request for non existent key "
                             "{}").format(key))
                raise e

    def set_domain_base(base):
        if base.endswith("/"):
            config["DOMAIN_BASE"] = base[:-1]
        else:
            config["DOMAIN_BASE"] = base
