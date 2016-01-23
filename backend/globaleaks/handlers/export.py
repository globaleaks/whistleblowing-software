# -*- coding: utf-8 -*-
#
# export
# *****
#
# Tip export utils
import copy

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.admin import node, context, receiver, notification
from globaleaks.handlers.admin.context import admin_serialize_context
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.receiver import admin_serialize_receiver
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.files import serialize_receiver_file
from globaleaks.handlers.rtip import db_access_rtip, serialize_rtip, \
    db_get_comment_list, db_get_message_list
from globaleaks.handlers.submission import get_submission_sequence_number
from globaleaks.models import ReceiverTip, ReceiverFile
from globaleaks.rest import errors
from globaleaks.utils.templating import Templating
from globaleaks.utils.zipstream import ZipStream


@transact_ro
def get_tip_export(store, user_id, rtip_id):
    rtip = db_access_rtip(store, user_id, rtip_id)

    files = []
    for rf in store.find(models.ReceiverFile, models.ReceiverFile.receivertip_id == rtip_id):
        rf.downloads += 1
        file_dict = serialize_receiver_file(rf)
        file_dict['name'] = 'files/' + file_dict['name']
        files.append(copy.deepcopy(file_dict))

    receiver = rtip.receiver
    user_language = receiver.user.language

    export_dict = {
        'type': u'export_template',
        'node': db_admin_serialize_node(store, user_language),
        'notification': db_get_notification(store, user_language),
        'tip': serialize_rtip(store, rtip, user_language),
        'context': admin_serialize_context(store, rtip.internaltip.context, user_language),
        'receiver': admin_serialize_receiver(receiver, user_language),
        'comments': db_get_comment_list(rtip),
        'messages': db_get_message_list(rtip),
        'files': []
    }

    export_template = Templating().format_template(export_dict['notification']['export_template'], export_dict).encode('utf-8')

    export_dict['files'].append({'buf': export_template, 'name': "data.txt"})

    return export_dict


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
        tip_export = yield get_tip_export(self.current_user.user_id, rtip_id)

        self.set_status(200)

        self.set_header('X-Download-Options', 'noopen')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=\"%s.zip\"' % tip_export['tip']['sequence_number'])

        for data in ZipStream(tip_export['files']):
            self.write(data)

        self.finish()
