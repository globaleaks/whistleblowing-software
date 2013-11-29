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
from Crypto.Hash import SHA256

from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.files import download_all_files
from globaleaks.handlers.authentication import authenticated
from globaleaks.rest import errors
from globaleaks.settings import GLSetting
from globaleaks.utils.zipstream import ZipStream, ZIP_STORED, ZIP_DEFLATED
from globaleaks.security import access_tip

class CollectionStreamer(object):
    def __init__(self, handler):
        self.handler = handler

    def write(self, data):
        if len(data) > 0:
          self.handler.write(data)

class CollectionDownload(BaseHandler):
    auth_type = "COOKIE"

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

        info  = "This is an archive of files downloaded from a GlobaLeaks node\n"
        info += "[Some operational security tips will go here]\n\n"

        sha = SHA256.new()

        info += "%s%s%s%s%s\n" % ("Filename",
                                  " "*(40-len("Filename")),
                                  "Size (Bytes)",
                                  " "*(15-len("Size (Bytes)")),
                                  "SHA256")

        total_size = 0
        for filedesc in files_dict:

            sha.update(filedesc['name'])

            length1 = 40 - len(filedesc['name'])
            length2 = 15 - len(str(filedesc['size']))

            info += "%s%s%i%s%s\n" % (filedesc['name'],
                                      " "*length1,
                                      filedesc['size'],
                                      " "*length2,
                                      filedesc['sha2sum'])

            total_size += filedesc['size']

            filedesc['name'] = filedesc['name'].encode('utf-8')

            # Update all the path with the absolute path
            filedesc['path'] = os.path.join(GLSetting.submission_path, filedesc['path'])

        info += "\nTotal size is: %s Bytes" % total_size

        files_dict.append({ 'buf'  : info,
                            'name' : "COLLECTION_INFO.txt" })

        self.set_status(200)

        self.set_header('X-Download-Options', 'noopen')
        self.set_header('Content-Type', 'application/octet-stream')
        self.set_header('Etag', '"%s"' % sha.hexdigest())
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
