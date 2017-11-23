# -*- coding: utf-8 -*-
#
# /admin/files
#  *****
#
# API handling db files upload/download/delete
import base64
import os

from twisted.internet import defer, threads

from globaleaks import models
from globaleaks.handlers.base import BaseHandler, write_upload_plaintext_to_disk
from globaleaks.orm import transact
from globaleaks.utils.utility import uuid4

@transact
def save_staticfile(store, file_desc):
    store.add(models.StaticFile(file_desc))


@transact
def delete_staticfile(store, tid, name):
    f = store.find(models.StaticFile, tid=tid, name=name).one()
    if f is not None:
        try:
            os.remove(f.path)
        except:
            pass

        store.remove(f)


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

    def post(self, id):
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            return

        if id != 'custom':
            data = uploaded_file['body'].read()
            data = base64.b64encode(data)
            d = add_file(self.request.tid, id, u'', data)
        else:
            id = uuid4()
            data = ''
            path = os.path.join(self.state.settings.files_path, id)
            d = threads.deferToThread(write_upload_plaintext_to_disk, uploaded_file, path)

            def callback(ret):
                add_file(self.request.tid, id, uploaded_file['name'], data)

            d.addCallback(callback)

        d.addBoth(lambda ignore: uploaded_file['body'].close)

        return d

    def delete(self, id):
        return models.delete(models.File, tid=self.request.tid, id=id)


class FileCollection(BaseHandler):
    check_roles = 'admin'

    def get(self):
        """
        Return the list of files and their info
        """
        return get_files(self.request.tid)
