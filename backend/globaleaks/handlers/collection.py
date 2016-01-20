# -*- coding: utf-8 -*-
#
# collection
# *****
#
# File Collections handlers and utils

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.admin import node, context, receiver, notification
from globaleaks.handlers.admin.context import admin_serialize_context
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.receiver import admin_serialize_receiver
from globaleaks.handlers.rtip import db_access_rtip, serialize_rtip
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.files import serialize_receiver_file
from globaleaks.models import ReceiverTip, ReceiverFile
from globaleaks.rest import errors
from globaleaks.utils.templating import Templating
from globaleaks.utils.zipstream import ZipStream


@transact
def get_file_collection(store, user_id, rtip_id):
    rtip = db_access_rtip(store, user_id, rtip_id)

    archive_dict = {'files': [], 'file_counter': 0, 'total_size': 0}

    file_list = []
    for rf in store.find(models.ReceiverFile, models.ReceiverFile.receivertip_id == rtip_id):
        rf.downloads += 1
        file_list.append(serialize_receiver_file(rf))
        archive_dict['file_counter'] += 1
        archive_dict['total_size'] += rf.size
        archive_dict['files'].append(serialize_receiver_file(rf))

    receiver = rtip.receiver
    user_language = receiver.user.language

    data = {
        'type': u'archive_description',
        'node': db_admin_serialize_node(store, user_language),
        'notification': db_get_notification(store, user_language),
        'tip': serialize_rtip(store, rtip, user_language),
        'context': admin_serialize_context(store, rtip.internaltip.context, user_language),
        'receiver': admin_serialize_receiver(receiver, user_language),
        'archive': archive_dict
    }

    archive_description = Templating().format_template(data['notification']['archive_description'], data).encode('utf-8')

    file_list.append(
        {
           'buf': archive_description,
           'name': "COLLECTION_INFO.txt"
        }
    )

    return file_list


@transact_ro
def get_receiver_from_rtip(store, rtip_id, language):
    rtip = store.find(ReceiverTip, ReceiverTip.id == rtip_id).one()

    if not rtip:
        raise errors.TipIdNotFound

    return receiver.admin_serialize_receiver(rtip.receiver, language)


class CollectionStreamer(object):
    def __init__(self, handler):
        self.handler = handler

    def write(self, data):
        if len(data) > 0:
            self.handler.write(data)


class CollectionDownload(BaseHandler):
    handler_exec_time_threshold = 3600

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def post(self, rtip_id):
        files_dict = yield get_file_collection(self.current_user.user_id, rtip_id)

        self.set_status(200)

        self.set_header('X-Download-Options', 'noopen')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=\"collection.zip\"')

        for data in ZipStream(files_dict):
            self.write(data)

        self.finish()
