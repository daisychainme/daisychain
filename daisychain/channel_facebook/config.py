from config.keys import keys
from logging import getLogger
from django.contrib.sites.models import Site


log = getLogger("channel")


config = {
    "DJANGO_SECRET": keys["DJANGO"]["PRODUCTION"],
    "APP_ID": "APP_KEY",
    "APP_SECRET": "APP_SECRET",
    "APP_WEBHOOK_CHALLENGE": "WEBHOOK_CHALLENGE",

    "DOMAIN_BASE": "DOMAIN_BASE",

    "API_VERSION": "v2.7",
    "API_BASE_URI" : "https://graph.facebook.com/{API_VERSION}",
    "API_LOGIN_OAUTH_BASE_URI": "https://www.facebook.com/dialog/oauth",
    "API_OAUTH_BASE_URI": "{API_BASE_URI}/oauth",
    "API_ACCESS_TOKEN_URI": "{API_OAUTH_BASE_URI}/access_token",
    "API_CHECK_ACCESS_TOKEN_URI": "{API_BASE_URI}/debug_token",
    "API_MEDIA_ENDPOINT": "https://api.facebook.com/v1/media/%s",
    "API_SUBSCRIPTION_ENDPOINT": "https://api.facebook.com/v1/subscriptions"
}


class Config():

    def get(key, default=None):
        try:
            Config.set_app_data()
            Config.set_domain_base()
            tmp = config[key]
            while tmp != tmp.format(API_VERSION=config['API_VERSION'], 
                                    API_BASE_URI=config['API_BASE_URI'],
                                    API_OAUTH_BASE_URI=config['API_OAUTH_BASE_URI']):
                tmp = tmp.format(API_VERSION=config['API_VERSION'], 
                                      API_BASE_URI=config['API_BASE_URI'],
                                      API_OAUTH_BASE_URI=config['API_OAUTH_BASE_URI'])
            return tmp
        
        except KeyError as e:
            if default is not None:
                return default.format(API_VERSION=config['API_VERSION'],
                                      API_BASE_URI=config['API_BASE_URI'],
                                      API_OAUTH_BASE_URI=config['API_OAUTH_BASE_URI'])
            else:
                log.warning(("facebook.conf got request for non existent key "
                             "{}").format(key))
                raise e
    @staticmethod
    def set_domain_base():
        config["DOMAIN_BASE"] = Site.objects.get_current().domain

    @staticmethod
    def set_app_data():
        config["APP_ID"] = keys["FACEBOOK"][Site.objects.get_current().domain]["APP_ID"]
        config["APP_SECRET"] = keys["FACEBOOK"][Site.objects.get_current().domain]["APP_SECRET"]
        config["APP_WEBHOOK_CHALLENGE"] = keys["FACEBOOK"]["WEBHOOK_CHALLENGE"]