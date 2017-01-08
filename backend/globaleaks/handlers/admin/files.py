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


@transact
def write_ssl_file(store, content, full_path):
    filename = os.path.basename(full_path)

    with open(full_path, 'w') as f:
        f.write(content)
    NodeFactory(store).set_val('ssl_%s_set' % filename, True)


@transact
def delete_ssl_file(store, full_path):
    filename = os.path.basename(full_path)

    overwrite_and_remove(full_path)
    NodeFactory(store).set_val('ssl_%s_set' % filename, False)


class SSLFileInstance(BaseHandler):

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self, filename):
        file_path = os.path.join(GLSettings.ssl_file_path, filename)
        directory_traversal_check(GLSettings.ssl_file_path, file_path)

        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            self.set_status(201)
            return
        try:
            yield write_ssl_file(uploaded_file['body'].read(), file_path)
        finally:
            uploaded_file['body'].close()

        GLApiCache.invalidate()

        self.set_status(201)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def delete(self, filename):
        file_path = os.path.join(GLSettings.ssl_file_path, filename)
        directory_traversal_check(GLSettings.ssl_file_path, file_path)

        if os.path.exists(file_path):
            yield delete_ssl_file(file_path)
        else:
            self.set_status(404)
            return

        self.set_status(200)
