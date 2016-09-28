import json
import logging
import requests
from core.channel import (Channel, NotSupportedTrigger, NotSupportedAction,
                          ConditionNotMet, ChannelStateForUser)
from core.core import Core
from channel_github.models import GithubAccount
from channel_github.config import (TRIGGER_TYPE, CHANNEL_NAME, CLIENT_ID,
                                   CLIENT_SECRET, TRIGGER_OUTPUT,
                                   API_URL, get_webhook_url, WEBHOOK_TEST,
                                   REPO_HOOKS_URL)


log = logging.getLogger('channel')




class GithubChannel(Channel):

    def _check_for_webhook(self, repo_name, auth_header):
        """
        returns true if a webhook for the given repo already exists
        """
        check_url = REPO_HOOKS_URL.format(repo_name)
        response =  requests.get(check_url, headers=auth_header)
        data = json.loads(response.content.decode('utf-8'))
        # check if our webhook url is associated with any webhook of the repo
        return any(get_webhook_url() in e['config']['url'] for e in data)

    def repo_exists(self, repo_name, owner):
        """
        Check if a github repository exists.

        Args:
            repo_name: The name of the repository
            owner: Github username of the owner.

        Returns:
            True if the repository exists, false otherwise.
        """
        resp = requests.get(API_URL.format(repo_name))
        return resp.ok

    def create_webhook(self,
                       github_account,
                       repository,
                       events,
                       owner=None):
        """
            This method creates a subscription to a repository of a
            github user whose account previously has been authenticated.
        """
        if not owner:
            owner = github_account.username
        # full repo name
        repo_name = '/'.join([owner, repository])

        auth_header = {'Authorization': 'token ' + github_account.access_token}

        # check whether a webhook already exists
        if self._check_for_webhook(repo_name, auth_header):
            # no need to create another!
            return repo_name

        data = {
                    'name': 'web',
                    'active': True,
                    'events': events,
                    'config': {
                        'url': get_webhook_url(),
                        'content_type': 'json'
                    }
                }
        subscribe_url = REPO_HOOKS_URL.format(repo_name)
        resp = requests.post(subscribe_url,
                  json=data,
                  headers=auth_header)
        if resp.ok:
            return repo_name
        else:
            return None

    def fire_trigger(self, trigger_data):
        """
        Handles incoming triggers

        params:
            trigger_data = a dictionary that contains the payload sent by
                           github as the event payload.
        """
        if 'commits' in trigger_data and 'pusher' in trigger_data:
            # push trigger
            self._fire_push_trigger(data=trigger_data)
        elif 'issue' in trigger_data:
            self._fire_issue_trigger(data=trigger_data)
            # TODO distinguish whether issue was created updated or something?

    def _fire_push_trigger(self, data):
        username = data['repository']['owner']['name']
        github_account = GithubAccount.objects.get(username=username)
        user_id = github_account.user.id
        trigger_type = TRIGGER_TYPE['push']
        payload = {
                   'repository_name': data['repository']['name'],
                   'repository_url': data['repository']['url'],
                   'head_commit_message': data['head_commit']['message'],
                   'head_commit_author': data['head_commit']['author']['name'],
                   'repository_full_name': data['repository']['full_name']
                   }
        # pass the data to the core and let it handle the trigger
        Core().handle_trigger(channel_name=CHANNEL_NAME,
                              trigger_type=trigger_type,
                              userid=user_id,
                              payload=payload)

    def _fire_issue_trigger(self, data):
        pass
        #TODO: complete implementation!

    def fill_recipe_mappings(self, trigger_type, userid,
                             payload, conditions, mappings):
        if trigger_type == TRIGGER_TYPE['push']:
            # check whether the the repository, that was pushed
            # matches the repository of the recipe.
            if conditions['repository_name'] != payload['repository_full_name']:
                raise ConditionNotMet()

            return self._replace_mappings(mappings=mappings,
                                          payload=payload,
                                          to_replace=['repository_name',
                                                    'repository_url',
                                                    'head_commit_message',
                                                    'head_commit_author'])
        elif trigger_type == TRIGGER_TYPE['issues']:
            # TODO implement!
            raise NotSupportedTrigger()
        else:
            raise NotSupportedTrigger()

    def _replace_mappings(self, mappings, to_replace, payload):
        for key in mappings:
            val = mappings[key]
            if type(val) == str:
                for s in to_replace:
                    # replace any placeholder by its concrete value
                    placeholder = '%{}%'.format(s)
                    val = val.replace(placeholder,
                                      payload[s])
                mappings[key] = val
        return mappings

    def handle_action(self, action_type, userid, inputs):
        raise NotSupportedAction()

    def user_is_connected(self, user):
        """
        Check whether the user is authenticated, i.e. whether a TwitterAccount
        has been saved.

        Args:
            user: The user that is checked.
        Returns:
            True if the user is authenticated, false otherwise.
        """
        if GithubAccount.objects.filter(user=user).count() > 0:
            return ChannelStateForUser.connected
        else:
            return ChannelStateForUser.initial
