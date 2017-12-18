# -*- coding: utf-8 -*-
#
# /admin/files
#  *****
#
# API handling db files upload/download/delete
import base64
import os

from twisted.internet import threads

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.security import directory_traversal_check
from globaleaks.utils.utility import uuid4

@transact
def get_files(store, tid):
    ret = []

    for sf in store.find(models.File, models.File.name != u"", tid=tid):
        ret.append({
            'id': sf.id,
            'name': sf.name,
            'data': sf.data,
        })

    return ret


def db_add_file(store, tid, id, name, data):
    file_obj = None
    if id is not None:
        file_obj = store.find(models.File, tid=tid, id=id).one()

    if file_obj is None:
        file_obj = models.File()
        file_obj.tid = tid

        if id is not None:
            file_obj.id = id

        store.add(file_obj)

    file_obj.name = name
    file_obj.data = data


@transact
def add_file(store, tid, id, name, data):
    return db_add_file(store, tid, id, name, data)


def db_get_file(store, tid, id):
    file_obj = store.find(models.File, tid=tid, id=id).one()

    return file_obj.data if file_obj is not None else ''


@transact
def get_file(store, tid, id):
    return db_get_file(store, tid, id)


class FileInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True
    upload_handler = True

    def post(self, id):
        if id != 'custom':
            data = self.uploaded_file['body'].read()
            data = base64.b64encode(data)
            d = add_file(self.request.tid, id, u'', data)
        else:
            id = uuid4()
            path = os.path.join(self.state.settings.files_path, id)
            d = threads.deferToThread(self.write_upload_plaintext_to_disk, path)
            d.addCallback(lambda x: add_file(self.request.tid, id, self.uploaded_file['name'], u''))

        return d

    def delete(self, id):
        path = os.path.join(self.state.settings.files_path, id)
        directory_traversal_check(self.state.settings.files_path, path)
        if os.path.exists(path):
            os.remove(path)

        return models.delete(models.File, tid=self.request.tid, id=id)


class FileCollection(BaseHandler):
    check_roles = 'admin'

    def get(self):
        """
        Return the list of files and their info
        """
        return get_files(self.request.tid)
