# -*- coding: utf-8 -*-
#
#  collection
#  *****
#
# File Collections handlers and utils

from twisted.internet.defer import inlineCallbacks

import os
import tarfile
import StringIO

from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.files import download_all_files, serialize_file
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.handlers import admin
from globaleaks.rest import errors
from globaleaks.settings import GLSetting, transact_ro
from globaleaks.utils.zipstream import ZipStream, ZIP_STORED, ZIP_DEFLATED
from globaleaks.plugins.base import Event
from globaleaks.jobs.notification_sched import serialize_receivertip
from globaleaks.models import ReceiverTip
from globaleaks.utils.utility import log
from globaleaks.utils.templating import Templating


@transact_ro
def get_collection_info(store, rtip_id):
    """
    This function return a receiver tip + file information
    """

    rtip = store.find(ReceiverTip, ReceiverTip.id == rtip_id).one()

    if not rtip:
        log.err("Download of a Zip file without ReceiverTip associated!")
        raise errors.TipGusNotFound

    rtip_dict = serialize_receivertip(rtip)

    rtip_dict['files'] = []
    rtip_dict['files_number'] = 0
    rtip_dict['total_size'] = 0
    for internalf in rtip.internaltip.internalfiles:
        rtip_dict['files_number'] += 1
        rtip_dict['total_size'] += internalf.size
        rtip_dict['files'].append(serialize_file(internalf))

    rtip_dict['etag_hash'] = unicode(str(rtip_dict['total_size'] * rtip_dict['files_number']))
    return rtip_dict


class CollectionStreamer(object):
    def __init__(self, handler):
        self.handler = handler

    def write(self, data):
        if len(data) > 0:
          self.handler.write(data)


class CollectionDownload(BaseHandler):
    auth_type = "COOKIE"

    @transport_security_check('wb')
    @authenticated('receiver')
    @inlineCallbacks
    def get(self, tip_gus, path, compression):

        if compression is None:
            # Forcing the default to be zip without compression
            compression = 'zipstored'

        if compression == 'zipstored':
            opts = { 'filename'         : 'collection.zip',
                     'compression_type' : ZIP_STORED}

        elif compression == 'zipdeflated':
            opts = { 'filename'         : 'collection.zip',
                     'compression_type' : ZIP_DEFLATED}

        elif compression == 'tar':
            opts = { 'filename'         : 'collection.tar',
                     'compression_type' : ''}

        elif compression == 'targz':
            opts = { 'filename'         : 'collection.tar.gz',
                     'compression_type' : 'gz'}

        elif compression == 'tarbz2':
            opts = { 'filename'         : 'collection.tar.bz2',
                     'compression_type' : 'bz2'}
        else:
            # just to be sure; by the way
            # the regexp of rest/api.py should prevent this.
            raise errors.InvalidInputFormat("collection compression type not supported")

        files_dict = yield download_all_files(self.current_user['user_id'], tip_gus)

        if not files_dict:
            raise errors.DownloadLimitExceeded

        node_dict = yield admin.get_node()
        receiver_dict = yield admin.get_receiver(self.current_user['user_id'])
        collection_tip_dict = yield get_collection_info(tip_gus)
        context_dict = yield admin.get_context(collection_tip_dict['context_id'])
        notif_dict = yield admin.get_notification()

        mock_event = Event(
            type = u'zip_collection',
            trigger = 'Download',
            notification_settings = notif_dict,
            node_info = node_dict,
            receiver_info = receiver_dict,
            context_info = context_dict,
            plugin = None,
            trigger_info = collection_tip_dict
        )

        for filedesc in files_dict:
            # Update all the path with the absolute path
            filedesc['path'] = os.path.join(GLSetting.submission_path, filedesc['path'])
        formatted_coll = Templating().format_template(notif_dict['zip_description'], mock_event)
        print formatted_coll
        files_dict.append(
            { 'buf'  : formatted_coll,
              'name' : "COLLECTION_INFO.txt"
            })

        self.set_status(200)

        self.set_header('X-Download-Options', 'noopen')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Etag', '"%s"' % collection_tip_dict['etag_hash'] )
        self.set_header('Content-Disposition','attachment; filename=\"' + opts['filename'] + '\"')

        if compression in ['zipstored', 'zipdeflated']:
            for data in ZipStream(files_dict, opts['compression_type']):
                self.write(data)

        elif compression in ['tar', 'targz', 'tarbz2']:
            collectionstreamer = CollectionStreamer(self)
            tar = tarfile.open("collection.tar.gz", 'w|'+opts['compression_type'], collectionstreamer)
            for f in files_dict:
                if 'path' in f:
                    tar.add(f['path'], f['name'])

                elif 'buf' in f:
                    tarinfo = tarfile.TarInfo(f['name'])
                    tarinfo.size = len(f['buf'])
                    tar.addfile(tarinfo, StringIO.StringIO(info))

            tar.close()


        self.finish()
