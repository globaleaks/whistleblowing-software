# -*- coding: utf-8 -*-
#
# export
# *****
#
# Tip export utils
from twisted.internet.defer import Deferred, inlineCallbacks

from globaleaks import models
from globaleaks.handlers.admin.context import admin_serialize_context
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.rtip import db_access_rtip, serialize_rtip
from globaleaks.handlers.user import user_serialize_user
from globaleaks.orm import transact
from globaleaks.settings import Settings
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import msdos_encode
from globaleaks.utils.zipstream import ZipStream


@transact
def get_tip_export(session, tid, user_id, rtip_id, language):
    rtip, itip = db_access_rtip(session, tid, user_id, rtip_id)

    user, context = session.query(models.User, models.Context) \
                         .filter(models.User.id == rtip.receiver_id,
                                 models.Context.id == models.InternalTip.context_id,
                                 models.InternalTip.id == rtip.internaltip_id,
                                 models.User.tid == tid).one()

    rtip_dict = serialize_rtip(session, rtip, itip, language)

    export_dict = {
        'type': u'export_template',
        'node': db_admin_serialize_node(session, tid, language),
        'notification': db_get_notification(session, tid, language),
        'tip': rtip_dict,
        'user': user_serialize_user(session, user, language),
        'context': admin_serialize_context(session, context, language),
        'comments': rtip_dict['comments'],
        'messages': rtip_dict['messages'],
        'files': []
    }

    export_template = Templating().format_template(export_dict['notification']['export_template'], export_dict).encode('utf-8')

    export_template = msdos_encode(export_template)

    export_dict['files'].append({'buf': export_template, 'name': "data.txt"})

    for rfile in session.query(models.ReceiverFile).filter(models.ReceiverFile.receivertip_id == rtip_id, models.ReceiverFile.tid == tid):
        rfile.downloads += 1
        file_dict = models.serializers.serialize_rfile(session, tid, rfile)
        file_dict['name'] = 'files/' + file_dict['name']
        export_dict['files'].append(file_dict)

    for wf in session.query(models.WhistleblowerFile).filter(models.WhistleblowerFile.receivertip_id == models.ReceiverTip.id, models.ReceiverTip.internaltip_id == rtip.internaltip_id, models.ReceiverTip.tid == tid):
        file_dict = models.serializers.serialize_wbfile(tid, wf)
        file_dict['name'] = 'files_from_recipients/' + file_dict['name']
        export_dict['files'].append(file_dict)

    return export_dict


class ZipStreamProducer(object):
    """ Streaming producter for ZipStream

    @ivar handler: The L{IRequest} to write the contents of the file to.
    @ivar fileObject: The file the contents of which to write to the request.
    """
    bufferSize = Settings.file_chunk_size

    def __init__(self, handler, zipstreamObject):
        """
        Initialize the instance.
        """
        self.finish = Deferred()
        self.handler = handler
        self.zipstreamObject = zipstreamObject

    def start(self):
        self.handler.request.registerProducer(self, False)
        return self.finish

    def resumeProducing(self):
        try:
            if not self.handler:
                return

            data = self.zip_chunk()
            if data:
                self.handler.request.write(data)
            else:
                self.stopProducing()
        except:
            self.stopProducing()
            raise

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
                if chunk_size >= Settings.file_chunk_size:
                    return ''.join(chunk)

        return ''.join(chunk)


class ExportHandler(BaseHandler):
    check_roles = 'receiver'
    handler_exec_time_threshold = 3600

    @inlineCallbacks
    def get(self, rtip_id):
        tip_export = yield get_tip_export(self.request.tid,
                                          self.current_user.user_id,
                                          rtip_id,
                                          self.request.language)

        self.request.setHeader('X-Download-Options', 'noopen')
        self.request.setHeader('Content-Type', 'application/octet-stream')
        self.request.setHeader('Content-Disposition', 'attachment; filename=\"%s.zip\"' % tip_export['tip']['sequence_number'])

        self.zip_stream = iter(ZipStream(tip_export['files']))

        yield ZipStreamProducer(self, self.zip_stream).start()
