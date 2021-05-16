# -*- coding: utf-8 -*-
#
# API handling export of submissions
from io import BytesIO
from twisted.internet import abstract
from twisted.internet.defer import Deferred, inlineCallbacks
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
from globaleaks.utils.zipstream import ZipStream


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

    rtip_dict = serialize_rtip(session, rtip, itip, language)

    return {
        'type': 'export_template',
        'node': db_admin_serialize_node(session, tid, language),
        'notification': db_get_notification(session, tid, language),
        'tip': rtip_dict,
        'crypto_tip_prv_key': Base64Encoder.decode(rtip.crypto_tip_prv_key),
        'user': user_serialize_user(session, user, language),
        'context': admin_serialize_context(session, context, language),
        'submission_statuses': db_get_submission_statuses(session, tid, language)
    }


class ZipStreamProducer(object):
    """Streaming producter for ZipStream"""

    def __init__(self, handler, zipstreamObject):
        self.finish = Deferred()
        self.handler = handler
        self.zipstreamObject = zipstreamObject

    def start(self):
        self.handler.request.registerProducer(self, False)
        return self.finish

    def resumeProducing(self):
        if not self.handler:
            return

        data = self.zip_chunk()
        if data:
            self.handler.request.write(data)
        else:
            self.stopProducing()

    def stopProducing(self):
        self.handler.request.unregisterProducer()
        self.handler.request.finish()
        self.handler = None
        self.finish.callback(None)

    def zip_chunk(self):
        chunk = []
        chunk_size = 0

        for data in self.zipstreamObject:
            if data:
                chunk_size += len(data)
                chunk.append(data)
                if chunk_size >= abstract.FileDescriptor.bufferSize:
                    return b''.join(chunk)

        return b''.join(chunk)


class ExportHandler(BaseHandler):
    check_roles = 'receiver'
    handler_exec_time_threshold = 3600

    @inlineCallbacks
    def get(self, rtip_id):
        tip_export = yield get_tip_export(self.request.tid,
                                          self.current_user.user_id,
                                          rtip_id,
                                          self.request.language)

        if tip_export['crypto_tip_prv_key']:
            tip_export['tip'] = yield deferToThread(decrypt_tip, self.current_user.cc, tip_export['crypto_tip_prv_key'], tip_export['tip'])

            for file_dict in tip_export['tip']['rfiles'] + tip_export['tip']['wbfiles']:
                if file_dict.get('status', '') == 'encrypted':
                    continue

                tip_prv_key = GCE.asymmetric_decrypt(self.current_user.cc, tip_export['crypto_tip_prv_key'])
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

        files = tip_export['tip']['rfiles'] + tip_export['tip']['wbfiles']
        del tip_export['tip']['rfiles'], tip_export['tip']['wbfiles']

        export_template = Templating().format_template(tip_export['notification']['export_template'], tip_export).encode()
        export_template = msdos_encode(export_template.decode()).encode()

        files.append({'fo': BytesIO(export_template), 'name': 'data.txt'})

        self.request.setHeader(b'X-Download-Options', b'noopen')
        self.request.setHeader(b'Content-Type', b'application/octet-stream')
        self.request.setHeader(b'Content-Disposition', b'attachment; filename="submission.zip"')

        self.zip_stream = iter(ZipStream(files))

        yield ZipStreamProducer(self, self.zip_stream).start()
