from config.keys import keys
from core.utils import get_local_url
from django.contrib.sites.models import Site


CHANNEL_NAME = "Github"

CLIENT_ID = keys['GITHUB']['CLIENT_ID']
CLIENT_SECRET = keys['GITHUB']['CLIENT_SECRET']

"""dictionary mapping trigger_types to events"""
EVENTS = {
    100: ['push'],
    101: ['issues']
}

TRIGGER_TYPE = {
    'push': 100,
    'issues': 101,
}

TRIGGER_OUTPUT = {
    'push': [
        'head_commit_message',
        'head_commit_author',
        'repository_name',
        'repository_url'
    ],
    'issues': [
        ''
    ]
}
# URLs needed for communication and authorization with github
ACCESS_TOKEN_URL = 'https://github.com/login/oauth/access_token'
API_URL = 'https://api.github.com/{}'
BASE_AUTH_URL = 'https://github.com/login/oauth/authorize?'
USER_URL = 'https://api.github.com/user'
REPO_HOOKS_URL = 'https://api.github.com/repos/{}/hooks'


def get_webhook_url():
    local_url = get_local_url()
    return '/'.join([local_url, 'github/hooks'])


WEBHOOK_TEST = 'daisychain.me/github/hooks'
