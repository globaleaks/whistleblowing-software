# -*- coding: utf-8 -*-
#
# /admin/files
#  *****
#
# API handling db files upload/download/delete
import base64

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact

XTIDX = 1

def db_add_file(store, tid, data, key=None):
    file_obj = None
    if key is not None:
        file_obj = store.find(models.File, tid=tid, id=key).one()

    if file_obj is None:
        file_obj = models.File()
        file_obj.tid = tid

        if key is not None:
            file_obj.id = key

        store.add(file_obj)

    file_obj.data = base64.b64encode(data)


@transact
def add_file(store, tid, data, key=None):
    return db_add_file(store, tid, data, key)


def db_get_file(store, tid, key):
    file_obj = store.find(models.File, tid=tid, id=key).one()

    return file_obj.data if file_obj is not None else ''


@transact
def get_file(store, tid, key):
    return db_get_file(store, tid, key)


class FileInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    key = None

    def post(self, key):
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            return

        d = add_file(XTIDX, uploaded_file['body'].read(), key)
        d.addBoth(lambda ignore: uploaded_file['body'].close)
        return d

    def delete(self, key):
        return models.delete(models.File, tid=XTIDX, id=key)
