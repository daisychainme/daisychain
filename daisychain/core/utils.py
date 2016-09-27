from tempfile import TemporaryFile
import requests
from django.contrib.sites.models import Site
import logging
from importlib import import_module

log = logging.getLogger("channel")


class ApiException(Exception):
    def __init__(self, type, code, message):
        self.type = type
        self.code = code
        self.message = message

    def __str__(self):
        return "{} [Code: {}] \"{}\"".format(self.type,
                                             self.code,
                                             self.message)


def get_local_url():
    domain = Site.objects.get_current().domain
    return 'https://{domain}'.format(domain=domain)


def download_file(url):
    r = requests.get(url, stream=True)
    if r.ok:
        tmp_file = TemporaryFile()
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                tmp_file.write(chunk)
        tmp_file.seek(0)
        return tmp_file
    else:
        log.error("Error while downloading media")
        log.error(r.json())
        raise ApiException("InternalDownloadError",
                           r.status_code,
                           "Error while loading file %s" % url)


def replace_text_mappings(mappings, to_replace, payload):
    for key in mappings:
        val = mappings[key]
        if type(val) is str:
            for s in to_replace:
                # replace any placeholder by its concrete value
                placeholder = '%{}%'.format(s)
                val = val.replace(placeholder,
                                  payload[s])
            mappings[key] = val
    return mappings


def get_channel_instance(channel):

    module_name = 'channel_{}.channel'.format(channel.lower())
    channel_module = import_module(module_name)
    channel_class_name = '{}Channel'.format(channel.capitalize())
    channel_instance = getattr(channel_module, channel_class_name)()

    return channel_instance
