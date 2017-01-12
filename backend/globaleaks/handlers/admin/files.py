# -*- coding: utf-8 -*-
#
# /admin/files
#  *****
#
# API handling db files upload/download/delete

import base64
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest.apicache import GLApiCache
from globaleaks.security import overwrite_and_remove, directory_traversal_check
from globaleaks.settings import GLSettings
from globaleaks.models.config import NodeFactory


def db_add_file(store, data, key = None):
    file_obj = None
    if key is not None:
        file_obj = store.find(models.File, models.File.id == key).one()

    if file_obj is None:
        file_obj = models.File()
        if key is not None:
            file_obj.id = key
        store.add(file_obj)

    file_obj.data = base64.b64encode(data)


@transact
def add_file(store, data, key = None):
    return db_add_file(store, data, key)


def db_get_file(store, key):
    file_obj = store.find(models.File, models.File.id == key).one()

    if file_obj is None:
        return ''

    return file_obj.data


@transact
def get_file(store, key):
    return db_get_file(store, key)


@transact
def del_file(store, key):
    file_obj = store.find(models.File, models.File.id == key).one()
    if file_obj is not None:
        store.remove(file_obj)


class FileInstance(BaseHandler):
    key = None

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self, key):
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            self.set_status(201)
            return

        try:
            yield add_file(uploaded_file['body'].read(), key)
        finally:
            uploaded_file['body'].close()

        GLApiCache.invalidate()

        self.set_status(201)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def delete(self, key):
        yield del_file(key)

        GLApiCache.invalidate()
