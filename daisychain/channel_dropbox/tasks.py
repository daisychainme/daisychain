from __future__ import absolute_import

from celery import shared_task
import dropbox
from .models import DropboxAccount, DropboxUser
from dropbox.files import FileMetadata, FolderMetadata, DeletedMetadata

from core.core import Core
import os
import logging

logger = logging.getLogger('channel')

MEGA_BYTE = 1000000
@shared_task
def fireTrigger(userid):
    dropbox_user = DropboxUser.objects.get(dropbox_userid=userid)
    dropbox_account = dropbox_user.dropbox_account
    daisy_userid = dropbox_account.user.id
    dbx = dropbox.Dropbox(dropbox_account.access_token)
    core = Core()

    user_info = account_info_changed(dbx, userid)
    #Check if User Info Changed
    if user_info is not None:
        logger.debug("user_info changed")
        #print(type(user_info) is dict)
        core.handle_trigger(channel_id=770,
                            trigger_type=5,
                            userid=daisy_userid,
                            payload=user_info)

    cursor = dropbox_account.cursor
    if cursor == '':
        cursor = None

    has_more_files_modified = True
    while has_more_files_modified:
        if cursor is None:
            result = dbx.files_list_folder(path='',
                recursive=True, include_media_info=True,
                include_deleted=True)
        else:
            result = dbx.files_list_folder_continue(cursor)
            logger.debug('[Dropbox - tasks - fireTrigger] - has cursor')

        if  not result.entries:
            logger.debug('[Dropbox - tasks - fireTrigger] - list is empty')
        else:
            logger.debug('[Dropbox - tasks - fireTrigger] - list has {}'.format(
                                                            len(result.entries)))

        for entry in result.entries:
            # Ignore deleted files, folders, and previously modified files
            if isinstance(entry, FileMetadata):
                logger.debug('[Dropbox - tasks - fireTrigger] - entry:\n{}'
                    .format(entry))
                payload = {}
                url = dbx.files_get_temporary_link(entry.path_display).link
                filename, file_extension = os.path.splitext(entry.name)
                #skip dot of file_extension
                file_extension =  file_extension[1:]
                payload['filename'] = filename+"."+file_extension
                payload['file_extension'] = file_extension
                payload['path'] =  entry.path_display
                payload['url'] = url
            #    payload['modified'] = (entry.server_modified).isoformat()
                payload['size'] = entry.size / MEGA_BYTE
            #    print(type(entry.server_modified))
                trigger_type = get_trigger_type(file_extension)

                if trigger_type is not None:
                    core.handle_trigger(channel_id=770,
                                            trigger_type=trigger_type,
                                            userid=daisy_userid,
                                            payload=payload)
                #trigger_type 1 reresents that there is a file change or new file
                #file was modified
                core.handle_trigger(channel_id=770,
                                    trigger_type=1,
                                    userid=daisy_userid,
                                    payload=payload)

        # Update ans overwrite cursor
        cursor = result.cursor
        dropbox_account.cursor = cursor
        dropbox_account.save()

        has_more_files_modified = result.has_more

#check whether User_Info changed
def account_info_changed(dbx, userid):
    dropbox_user = DropboxUser.objects.get(dropbox_userid=userid)
    user_info = {}
    current_account = dbx.users_get_current_account()
    disk = dbx.users_get_space_usage()
    allocated = disk.allocation.get_individual().allocated

    changed_flag = False
    if current_account.name.display_name != dropbox_user.display_name:
        dropbox_user.display_name = current_account.name.display_name
        changed_flag = True
    if current_account.email != dropbox_user.email:
        dropbox_user.email =  current_account.email
        changed_flag = True
    if current_account.profile_photo_url != dropbox_user.profile_photo_url:
        dropbox_user.profile_photo_url =  current_account.profile_photo_url
        changed_flag = True
    #if (disk.used/MEGA_BYTE) != float(dropbox_user.disk_used):
    #    dropbox_user.disk_used = (disk.used / MEGA_BYTE)
    #    changed_flag = True
    if (allocated/MEGA_BYTE) != float(dropbox_user.disk_allocated):
        dropbox_user.disk_allocated = (allocated / MEGA_BYTE)
        changed_flag = True

    if not changed_flag:
        return None
    else:
        dropbox_user.save()
        user_info['display_name'] = dropbox_user.display_name
        user_info['email'] = dropbox_user.email
        user_info['profile_photo_url'] = dropbox_user.profile_photo_url
        #user_info['disk_used'] = dropbox_user.disk_used
        user_info['disk_allocated'] = allocated
        #user_info['disk_allocated'] = dropbox_user.disk_allocated
        return user_info

#interested in following file types
def get_trigger_type(ext):
    return {
        "jpg": 2,
        #".jpeg": 2,
        #".gif": 2,
        "png": 2,
        "mp4": 2,
        #".avi": 2,
        "movie": 2,
        "mp3": 3,
        #".wma": 3,
        #".xls": 105,
        #".ppt": 105,
        #".doc": 105,
        #".dot": 105,
        #".xlsx": 105,
        #".dox": 105,
        #".zip": 105,
        }.get(ext, None)
