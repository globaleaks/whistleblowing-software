# -*- coding: UTF-8
#
#   overview
#   ********
# Implementation of the code executed when an HTTP client reach /overview/* URI

import os

from twisted.internet.defer import inlineCallbacks
from storm.expr import Desc

from globaleaks.settings import transact_ro, GLSetting
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks import models

from globaleaks.utils.utility import pretty_date_time, log
from globaleaks.utils.structures import Rosetta

@transact_ro
def collect_tip_overview(store, language=GLSetting.memory_copy.default_language):

    tip_description_list = []
    all_itips = store.find(models.InternalTip)
    all_itips.order_by(Desc(models.InternalTip.creation_date))

    for itip in all_itips:
        tip_description = {
            "id": itip.id,
            "creation_date": pretty_date_time(itip.creation_date),
            "creation_lifetime": pretty_date_time(itip.creation_date),
            "expiration_date": pretty_date_time(itip.expiration_date),
            "context_id": itip.context_id,
            "pertinence_counter": itip.pertinence_counter,
            "status": itip.mark,
            "receivertips": [],
            "internalfiles": [],
            "comments": [],
        }

        mo = Rosetta()
        mo.acquire_storm_object(itip.context)
        tip_description['context_name'] = mo.dump_translated('name', language)

        # strip uncompleted submission, until GLClient open new submission
        # also if no data has been supply
        if itip.mark == models.InternalTip._marker[0]:
            continue

        for rtip in itip.receivertips:
            tip_description['receivertips'].append({
                'access_counter': rtip.access_counter,
                'notification_date': pretty_date_time(rtip.notification_date),
                # 'creation_date': pretty_date_time(rtip.creation_date),
                'status': rtip.mark,
                'receiver_id': rtip.receiver.id,
                'receiver_username': rtip.receiver.user.username,
                'receiver_name': rtip.receiver.name,
                # last_access censored willingly
            })

        for ifile in itip.internalfiles:
            tip_description['internalfiles'].append({
                'name': ifile.name,
                'size': ifile.size,
                'status': ifile.mark,
                'content_type': ifile.content_type
            })

        for comment in itip.comments:
            tip_description['comments'].append({
                'type': comment.type,
                'lifetime': pretty_date_time(comment.creation_date),
            })

        # whistleblower tip has not a reference from itip, then:
        wbtip = store.find(models.WhistleblowerTip,
            models.WhistleblowerTip.internaltip_id == itip.id).one()

        if wbtip is not None:
            tip_description.update({
                'wb_access_counter': wbtip.access_counter,
                'wb_last_access': pretty_date_time(wbtip.last_access)
            })
        else:
            tip_description.update({
                'wb_access_counter': u'Deleted', 'wb_last_access': u'Never'
            })

        tip_description_list.append(tip_description)

    return tip_description_list


@transact_ro
def collect_users_overview(store):

    users_description_list = []

    all_receivers = store.find(models.Receiver)

    for receiver in all_receivers:
        # all public of private infos are stripped, because know between the Admin resources
        user_description = {
            'id': receiver.id,
            'name': receiver.name,
            'receiverfiles': [],
            'receivertips': [],
            'gpg_key_status': receiver.gpg_key_status,
        }

        rcvr_files = store.find(models.ReceiverFile, models.ReceiverFile.receiver_id == receiver.id )
        for rfile in rcvr_files:

            if not rfile.internalfile:
                log.err("(user_overview) ReceiverFile without InternaFile available: skipped")
                continue

            user_description['receiverfiles'].append({
                'id': rfile.id,
                'file_name': rfile.internalfile.name,
                'downloads': rfile.downloads,
                'last_access': pretty_date_time(rfile.last_access),
                'status': rfile.mark,
            })

        rcvr_tips = store.find(models.ReceiverTip, models.ReceiverTip.receiver_id == receiver.id )
        for rtip in rcvr_tips:
            user_description['receivertips'].append({
                'internaltip_id': rtip.id,
                'status': rtip.mark,
                'last_access': pretty_date_time(rtip.last_access),
                'notification_date': pretty_date_time(rtip.notification_date),
                'access_counter': rtip.access_counter,
            })

        users_description_list.append(user_description)

    return users_description_list

@transact_ro
def collect_files_overview(store):

    file_description_list = []

    submission_dir = os.path.join(GLSetting.working_path, GLSetting.submission_path)
    disk_files = os.listdir(submission_dir)
    stored_ifiles = store.find(models.InternalFile)
    stored_ifiles.order_by(Desc(models.InternalFile.creation_date))

    for ifile in stored_ifiles:

        file_desc = {
            'id': ifile.id,
            'name': ifile.name,
            'content_type': ifile.content_type,
            'size': ifile.size,
            'itip': ifile.internaltip_id,
            'creation_date': pretty_date_time(ifile.creation_date),
            'rfiles': 0,
            'stored': None,
            'path': '',
        }

        file_desc['rfiles'] = store.find(models.ReceiverFile,
                        models.ReceiverFile.internalfile_id == ifile.id).count()

        absfilepath = os.path.join(submission_dir, ifile.file_path)

        if os.path.isfile(absfilepath):

            file_desc['stored'] = True
            file_desc['path'] = absfilepath

            # disk_files contain all the files present, the InternalFiles
            # are removed one by one, and the goal is to keep in disk_files
            # all the not referenced files.
            if ifile.file_path in disk_files:
                disk_files.remove(ifile.file_path)
            else:
                log.err("Weird failure: path %s not found in %s but still on dir" %
                    (ifile.file_path, submission_dir) )

        else:
            log.err("InternalFile %s has not a disk reference present: %s" %
                    (file_desc['name'], absfilepath) )
            file_desc['stored'] = False

        file_description_list.append(file_desc)

    # the files remained in disk_files array are without ifile
    for dfile in disk_files:

        absfilepath = os.path.join(submission_dir, dfile)

        file_desc = {
            'id': '',
            'name': '',
            'content_type': '',
            'size': os.stat(absfilepath).st_size,
            'itip': '',
            'rfiles_associated': 0,
            'stored': True,
            'path': absfilepath,
        }

        file_description_list.append(file_desc)

    return file_description_list


class Tips(BaseHandler):
    """
    A9

    /admin/overview/tips
    """

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: TipsOverviewList
        Errors: None
        """
        tips_complete_list = yield collect_tip_overview(self.request.language)

        self.set_status(200)
        self.finish(tips_complete_list)


class Users(BaseHandler):
    """
    AA

    /admin/overview/users
    """

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: UsersOverviewList
        Errors: None
        """
        users_complete_list = yield collect_users_overview()

        self.set_status(200)
        self.finish(users_complete_list)


class Files(BaseHandler):
    """
    /admin/overview/files

    Return the list of the files in InternalFile, ReceiverFile
    and the files in
    """

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: FilesOverviewList
        Errors: None
        """

        file_complete_list = yield collect_files_overview()

        self.set_status(200)
        self.finish(file_complete_list)


class StatsCollection(BaseHandler):
    """
    /admin/statistics

    This return the history of the anonymous activity over the node,
    this is needed to spot anomalies and raise 'alarms'
    """


