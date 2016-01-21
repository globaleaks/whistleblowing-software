# -*- coding: utf-8 -*-
#
# export
# *****
#
# Tip export utils

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
def get_tip_export(store, user_id, rtip_id):
    rtip = db_access_rtip(store, user_id, rtip_id)

    export_dict = {'files': [], 'file_counter': 0, 'total_size': 0}

    file_list = []
    for rf in store.find(models.ReceiverFile, models.ReceiverFile.receivertip_id == rtip_id):
        rf.downloads += 1
        file_list.append(serialize_receiver_file(rf))
        export_dict['file_counter'] += 1
        export_dict['total_size'] += rf.size
        export_dict['files'].append(serialize_receiver_file(rf))

    receiver = rtip.receiver
    user_language = receiver.user.language

    data = {
        'type': u'export_template',
        'node': db_admin_serialize_node(store, user_language),
        'notification': db_get_notification(store, user_language),
        'tip': serialize_rtip(store, rtip, user_language),
        'context': admin_serialize_context(store, rtip.internaltip.context, user_language),
        'receiver': admin_serialize_receiver(receiver, user_language),
        'export': export_dict
    }


    export_template = Templating().format_template(data['notification']['export_template'], data).encode('utf-8')

    file_list.append(
        {
           'buf': export_template,
           'name': "DATA.txt"
        }
    )

    return file_list


@transact_ro
def get_receiver_from_rtip(store, rtip_id, language):
    rtip = store.find(ReceiverTip, ReceiverTip.id == rtip_id).one()

    if not rtip:
        raise errors.TipIdNotFound

    return receiver.admin_serialize_receiver(rtip.receiver, language)


class ExportStreamer(object):
    def __init__(self, handler):
        self.handler = handler

    def write(self, data):
        if len(data) > 0:
            self.handler.write(data)


class ExportHandler(BaseHandler):
    handler_exec_time_threshold = 3600

    @transport_security_check('receiver')
    @authenticated('receiver')
    @inlineCallbacks
    def post(self, rtip_id):
        files_dict = yield get_tip_export(self.current_user.user_id, rtip_id)

        self.set_status(200)

        self.set_header('X-Download-Options', 'noopen')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=\"submission.zip\"')

        for data in ZipStream(files_dict):
            self.write(data)

        self.finish()
