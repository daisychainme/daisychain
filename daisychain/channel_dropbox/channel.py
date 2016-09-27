import contextlib
import datetime
import time
import os
#import six
import sys
import time
import unicodedata
import dropbox
from .models import DropboxAccount, DropboxUser

from core.channel import (Channel, NotSupportedTrigger, NotSupportedAction,
                          ConditionNotMet, ChannelStateForUser)

from django.contrib.auth.models import User
from tempfile import TemporaryFile
from enum import IntEnum
import re
import logging

logger = logging.getLogger('channel')

class ActionType(IntEnum):
    upload = 1
    download = 2
    download_to_destination = 3

    #TODO
    #sync = 4

class TriggerType(IntEnum):
    files_change = 1
    new_media = 2
    new_audio = 3
    new_shared = 4
    user_info_changed = 5


class DropboxChannel(Channel):

    def fill_recipe_mappings(self, trigger_type, userid,
        payload, conditions, mappings):

        user = User.objects.get(pk=userid)
        dropbox_account = DropboxAccount.objects.get(user=user)
        dbx = dropbox.Dropbox(dropbox_account.access_token)

        if conditions:
            for key in conditions:
                if conditions[key] == payload[key]:
                    return self._fill_mappings(dbx, mappings, payload)
                else:
                    logger.error("[Dropbox Channel - fill_recipe_mappings] Condition \
                            wasn't met. \nuserid:%s\nconditions: %s\npayload: %s" %
                         (userid, payload, conditions))
                    raise ConditionNotMet(
                        "The condition for filename was not met. \
                        Filename is \"{}\", but should be: \"{}\"".format(
                            conditions[key], payload[key]))
        else:
            return self._fill_mappings(dbx, mappings, payload)

    def _fill_mappings(self, dbx, mappings, payload):
        #TODO check file size and Users max_space i.e. disk_allocated
        download_trigger_names = ["data","jpg","png","video","audio"]
        for key in mappings:
            #get all the fields to fill, with %<fields>%
            fields = re.findall(r'%[a-z]+_?\-?[a-z]+%', mappings[key].lower())
            if not fields:
                continue
            #remove the percent sign from fields
            match_fields = list(map(lambda fields: fields[1:-1], fields))

            #check if mappings is expecting any file-object
            if not set(download_trigger_names) & set(match_fields):
                #no data objects necessary,
                #so just fill from mappings from payload
                #replace values from the key with the payload
                for opts in payload:
                    if opts in match_fields:
                        #get index of entry in match_field, because it will
                        #be the same in the fields, which we have to replace
                        index = match_fields.index(opts)
                        mappings[key] = mappings[key].replace(fields[index],
                            payload[opts])
            else:
                for data in download_trigger_names:
                    if data in match_fields:
                        mappings[key] = self._fill_data(dbx, payload)
                        #this key is set, and no further search
                        #in payloads is required
                        break
        return mappings

    def _fill_data(self, dbx, payload):
        #Dropbox API suggests to use this method only if
        #file size is below 150 MB
        if payload['size'] < 150.0:
            with self.stopwatch('fill_data'):
                try:
                    #meta is MetaData of file
                    meta, res = dbx.files_download(payload['path'])
                    data = res.content
                    tmp_file = TemporaryFile()
                    tmp_file.write(data)
                    tmp_file.seek(0)

                    logger.debug('downloading: %d bytes; metadata: %s' % \
                        (len(data), meta))

                    return tmp_file
                except (TypeError, dropbox.exceptions.ApiError) as err:
                        logger.error("[Dropbox Channel - fill_data] \
                            Api_Error: ", err)
                        raise ConditionNotMet("[DropboxChannel - fill_data]: ", err)

        else :
            #TODO write method which downlaods the data in chunks
            #meanwhile
            logger.error("[Dropbox Channel - fill_data] \
                FileSize not supported")
            raise NotSupportedTrigger("[Dropbox Channel - fill_data] \
                The File size for download is not yet supported.")

    def handle_action(self, action_type, userid, inputs):
        logger.debug("[DropboxChannel - handle_action] action_type: {}\
            \nuserid: {}\ninputs: {}".format(action_type, userid, inputs))

        user = User.objects.get(pk=userid)
        dropbox_account = DropboxAccount.objects.get(user=user)
        dbx = dropbox.Dropbox(dropbox_account.access_token)

        if action_type == ActionType.upload:
            self._dbx_upload(dbx, inputs['data'], inputs['path'],
                inputs['overwrite'])

        elif action_type == ActionType.download:
            #TODO need to do something with data
            data = self._dbx_download(dbx, inputs['path'])

        elif action_type == ActionType.download_to_destination:
            self._dbx_download_to_destination(
                dbx, inputs['path_to'], inputs['path_from'])
        else:
            raise NotSupportedAction("[DropboxChannel - handle_action]\
                This action is not supported by the Dropbox channel.")

    def user_is_connected(self, user):

        if DropboxAccount.objects.filter(user=user).count() > 0:
            return ChannelStateForUser.connected
        else:
            return ChannelStateForUser.initial

    #def dbx_download(dbx, folder, subfolder, name):
    def _dbx_download(self, dbx, path):
        """Download a file.

        Return the bytes of the file, or None if it doesn't exist.
        """
        #Here we can start stop the time it takes to downlaod:
        #https://github.com/dropbox/dropbox-sdk-python/blob/master/example/updown.py
        with self.stopwatch('download'):
            try:
                meta, res = dbx.files_download(path)
                data = res.content
                tmp_file = TemporaryFile()
                tmp_file.write(data)
                tmp_file.seek(0)
                logger.debug('downloading: %d bytes; metadata: %s' % \
                    (len(data), meta))
            except (TypeError, dropbox.exceptions.ApiError) as err:
                logger.error("[Dropbox Channel - dbx_download] \
                    Api Error while downloading: ", err)
                raise ConditionNotMet("[Dropbox Channel - dbx_download] \
                    API Failure")

        return tmp_file


    def _dbx_download_to_destination(self, dbx, path_to, path_from):
        """Download a file to a destination.

        Return response or None if something went wrong.
        """
        #Here we can start stop the time it takes to downlaod:
        #https://github.com/dropbox/dropbox-sdk-python/blob/master/example/updown.py
        with self.stopwatch('download_to_destination'):
            try:
                meta, res = dbx.files_download_to_file(path_from, path_to)
            except (TypeError, dropbox.exceptions.ApiError) as err:
                logger.error("[Dropbox Channel] \
                    Api Error while downloading_to_destination: ", err)
                raise ConditionNotMet("DropBox Channel - API Failure - \
                    function: dbx_download_to_destination")
        logger.debug('downloading: %d bytes; metadata: %s' % \
            (len(res.content), meta))
        #return res

    #def dbx_upload(dbx, folder, subfolder, name, overwrite=False):
    def _dbx_upload(self, dbx, data, path, overwrite=False):
        """Upload a file.

        Return the request response, or None in case of error.
        """

        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)
        mtime = os.path.getmtime(path)
        #Here we can start stop the time it takes to downlaod:
        #https://github.com/dropbox/dropbox-sdk-python/blob/master/example/updown.py
        with self.stopwatch('upload %d bytes: ' % data):
            try:
                res = dbx.files_upload(data, path, mode,
                    client_modified=datetime.datetime(*time.gmtime(mtime)[:6]),
                    mute=True)
                logger.debug('uploaded as {}'.format(res.name.encode('utf8')))
                return res
            except (dropbox.exceptions.BadInputError, dropbox.exceptions.ApiError) as err:
                logger.error("[Dropbox Channel - dbx_upload] \
                    Api Error while uploading: ", err)
                raise ConditionNotMet("[Dropbox Channel - dbx_upload] \
                    API Failure")

    #TODO easy implement features:
    #   restore, backup

    #just in case we want to know how long it took to upload/download the file
    @contextlib.contextmanager
    def stopwatch(self, message):
        """Context manager to print how long a block of code took."""
        t0 = time.time()
        try:
            yield
        finally:
            t1 = time.time()
            logger.debug('Total elapsed time for %s: %.3f' % (message, t1 - t0))
