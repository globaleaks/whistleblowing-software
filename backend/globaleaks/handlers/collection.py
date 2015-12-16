# -*- coding: utf-8 -*-
#
# collection
# *****
#
# File Collections handlers and utils

from twisted.internet.defer import inlineCallbacks

from globaleaks.orm import transact_ro
from globaleaks.handlers.admin import node, context, receiver, notification
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.files import download_all_files, serialize_receiver_file
from globaleaks.handlers.submission import serialize_usertip
from globaleaks.models import ReceiverTip, ReceiverFile
from globaleaks.rest import errors
from globaleaks.utils.templating import Templating
from globaleaks.utils.zipstream import ZipStream


@transact_ro
def get_rtip_info(store, rtip_id, language):
    """
    This function return a receiver tip
    """
    rtip = store.find(ReceiverTip, ReceiverTip.id == rtip_id).one()
    if not rtip:
        raise errors.TipIdNotFound

    rtip_dict = serialize_usertip(store, rtip, language)

    return rtip_dict


@transact_ro
def get_collection_info(store, rtip_id):
    """
    This function return a receiver tip + file information
    """
    rtip = store.find(ReceiverTip, ReceiverTip.id == rtip_id).one()
    if not rtip:
        raise errors.TipIdNotFound

    collection_dict = {'files': [], 'file_counter': 0, 'total_size': 0}

    rfiles = store.find(ReceiverFile, ReceiverFile.receivertip_id == rtip_id)
    for rf in rfiles:
        collection_dict['file_counter'] += 1
        collection_dict['total_size'] += rf.size
        collection_dict['files'].append(serialize_receiver_file(rf))

    return collection_dict


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
        files_dict = yield download_all_files(self.current_user.user_id, rtip_id)
        node_dict = yield node.admin_serialize_node(self.request.language)
        receiver_dict = yield get_receiver_from_rtip(rtip_id, self.request.language)
        rtip_dict = yield get_rtip_info(rtip_id, self.request.language)
        collection_tip_dict = yield get_collection_info(rtip_id)
        context_dict = yield context.get_context(rtip_dict['context_id'], 'en')
        notif_dict = yield notification.get_notification(self.request.language)

        """
        mock_event = Event(
            type=u'archive_description',
            trigger='Download',
            node_info=node_dict,
            receiver_info=receiver_dict,
            context_info=context_dict,
            tip_info=rtip_dict,
            subevent_info=collection_tip_dict,
            do_mail=False,
        )

        formatted_coll = Templating().format_template(notif_dict['archive_description'], mock_event).encode('utf-8')

        files_dict.append(
            {
               'buf': formatted_coll,
               'name': "COLLECTION_INFO.txt"
            }
        )
        """

        self.set_status(200)

        self.set_header('X-Download-Options', 'noopen')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Content-Disposition', 'attachment; filename=\"collection.zip\"')

        for data in ZipStream(files_dict):
            self.write(data)

        self.finish()
