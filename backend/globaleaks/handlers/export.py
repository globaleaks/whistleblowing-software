# -*- coding: utf-8 -*-
#
# API handling export of submissions
from io import BytesIO
from twisted.internet.defer import inlineCallbacks
from twisted.internet.threads import deferToThread

from globaleaks import models
from globaleaks.handlers.admin.context import admin_serialize_context
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.public import db_get_submission_statuses
from globaleaks.handlers.rtip import serialize_rtip
from globaleaks.handlers.submission import decrypt_tip
from globaleaks.handlers.user import user_serialize_user
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.utils.crypto import Base64Encoder, GCE
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import msdos_encode
from globaleaks.utils.zipstream import ZipStream, ZipStreamProducer


def serialize_rtip_export(session, user, rtip, itip, context, language):
    rtip_dict = serialize_rtip(session, rtip, itip, language)

    return {
        'type': 'export_template',
        'node': db_admin_serialize_node(session, user.tid, language),
        'notification': db_get_notification(session, user.tid, language),
        'tip': rtip_dict,
        'crypto_tip_prv_key': Base64Encoder.decode(rtip.crypto_tip_prv_key),
        'user': user_serialize_user(session, user, language),
        'context': admin_serialize_context(session, context, language),
        'submission_statuses': db_get_submission_statuses(session, user.tid, language)
    }


@transact
def get_tip_export(session, tid, user_id, rtip_id, language):
    user, context, itip, rtip  = session.query(models.User, models.Context, models.InternalTip, models.ReceiverTip) \
                                        .filter(models.User.id == user_id,
                                                models.User.tid == tid,
                                                models.ReceiverTip.id == rtip_id,
                                                models.ReceiverTip.receiver_id == user_id,
                                                models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                                models.Context.id == models.InternalTip.context_id).one_or_none()

    if not user:
        raise errors.ResourceNotFound()

    return serialize_rtip_export(session, user, rtip, itip, context, language)


@transact
def get_tips_export(session, tid, user_id, language):
    results = session.query(models.User, models.Context, models.InternalTip, models.ReceiverTip) \
                     .filter(models.User.id == user_id,
                             models.User.tid == tid,
                             models.ReceiverTip.receiver_id == user_id,
                             models.InternalTip.id == models.ReceiverTip.internaltip_id,
                             models.Context.id == models.InternalTip.context_id)

    ret = []
    for user, context, itip, rtip in results:
        ret.append(serialize_rtip_export(session, user, rtip, itip, context, language))

    return ret


@inlineCallbacks
def prepare_tip_export(cc, tip_export):
    files = tip_export['tip']['rfiles'] + tip_export['tip']['wbfiles']

    if tip_export['crypto_tip_prv_key']:
        tip_export['tip'] = yield deferToThread(decrypt_tip, cc, tip_export['crypto_tip_prv_key'], tip_export['tip'])

        for file_dict in tip_export['tip']['rfiles'] + tip_export['tip']['wbfiles']:
            if file_dict.get('status', '') == 'encrypted':
                continue

            tip_prv_key = GCE.asymmetric_decrypt(cc, tip_export['crypto_tip_prv_key'])
            file_dict['fo'] = GCE.streaming_encryption_open('DECRYPT', tip_prv_key, file_dict['path'])
            del file_dict['path']

    for file_dict in tip_export['tip']['rfiles']:
        file_dict['name'] = 'files/' + file_dict['name']
        if file_dict.get('status', '') == 'encrypted':
            file_dict['name'] += '.pgp'

    for file_dict in tip_export['tip']['wbfiles']:
        file_dict['name'] = 'files_attached_from_recipients/' + file_dict['name']

    tip_export['comments'] = tip_export['tip']['comments']
    tip_export['messages'] = tip_export['tip']['messages']

    export_template = Templating().format_template(tip_export['notification']['export_template'], tip_export).encode()
    export_template = msdos_encode(export_template.decode()).encode()

    files.append({'fo': BytesIO(export_template), 'name': 'report.txt'})

    return files


class ExportHandler(BaseHandler):
    check_roles = 'receiver'
    require_token = [b'GET']
    handler_exec_time_threshold = 3600

    @inlineCallbacks
    def get(self, rtip_id):
        tip_export = yield get_tip_export(self.request.tid,
                                          self.session.user_id,
                                          rtip_id,
                                          self.request.language)

        files = yield prepare_tip_export(self.session.cc, tip_export)

        self.request.setHeader(b'X-Download-Options', b'noopen')
        self.request.setHeader(b'Content-Type', b'application/octet-stream')
        self.request.setHeader(b'Content-Disposition', b'attachment; filename="report-' + str(tip_export["tip"]["progressive"]).encode() + b'.zip"')

        self.zip_stream = iter(ZipStream(files))

        yield ZipStreamProducer(self, self.zip_stream).start()


class ExportAllHandler(BaseHandler):
    check_roles = 'receiver'
    require_token = [b'GET']
    handler_exec_time_threshold = 3600

    @inlineCallbacks
    def get(self):
        tips_export = yield get_tips_export(self.request.tid,
                                            self.session.user_id,
                                            self.request.language)

        files = []
        for tip_export in tips_export:
            _files = yield prepare_tip_export(self.session.cc, tip_export)
            for _file in _files:
                _file['name'] = str(tip_export['tip']['progressive']) + "/" + _file['name']
                files.append(_file)

        self.request.setHeader(b'X-Download-Options', b'noopen')
        self.request.setHeader(b'Content-Type', b'application/octet-stream')
        self.request.setHeader(b'Content-Disposition', b'attachment; filename="reports.zip"')

        self.zip_stream = iter(ZipStream(files))

        yield ZipStreamProducer(self, self.zip_stream).start()
