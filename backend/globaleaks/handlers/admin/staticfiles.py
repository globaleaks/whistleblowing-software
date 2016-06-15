from __future__ import with_statement
import base64
import re
from twisted.internet import threads
from cyclone.web import os
from twisted.internet.defer import inlineCallbacks
from globaleaks import models
from globaleaks.orm import transact_ro, transact
from globaleaks.settings import GLSettings
from globaleaks.handlers.base import BaseHandler
from globaleaks.utils.utility import log
from globaleaks.rest import errors, requests
from globaleaks.rest.apicache import GLApiCache
from globaleaks.rest.requests import receiver_img_regexp
from globaleaks.security import directory_traversal_check

def get_description_by_stat(statstruct, name):
    return {
      'filename': name,
      'size': statstruct.st_size
    }


def get_stored_files():
    stored_list = []
    for fname in os.listdir(GLSettings.static_path):
        filepath = os.path.join(GLSettings.static_path, fname)
        if os.path.isfile(filepath):
            statinfo = os.stat(filepath)
            stored_list.append(get_description_by_stat(statinfo, fname))

    return stored_list


def get_file_info(uploaded_file, filelocation):
    """
    @param uploaded_file: the bulk of Cyclone upload data
           filelocation: the absolute path where the file goes
    @return: list of files with content_type and size.
    """
    return {
        'filename': uploaded_file['filename'],
         'content_type': uploaded_file['content_type'],
         'size': uploaded_file['body_len'],
         'filelocation': filelocation
    }


def dump_static_file(uploaded_file, filelocation):
    """
    @param uploadedfile: uploaded_file
    @return: a relationship dict linking the filename with the random
        filename saved in the disk
    """
    try:
        if os.path.exists(filelocation):
            log.err('Overwriting file %s with %d bytes' % (filelocation, uploaded_file['body_len']))
        else:
            log.debug('Creating file %s with %d bytes' % (filelocation, uploaded_file['body_len']))

        with open(filelocation, 'w+') as fd:
            uploaded_file['body'].seek(0, 0)
            data = uploaded_file['body'].read(4000)
            while data != '':
                os.write(fd.fileno(), data)
                data = uploaded_file['body'].read(4000)

    finally:
        uploaded_file['body'].close()

    return get_file_info(uploaded_file, filelocation)


def db_add_file(store, data, key = None):
    file_obj = None
    if key != None:
        file_obj = store.find(models.File, models.File.id == key).one()

    if file_obj is None:
        file_obj = models.File()
        if key != None:
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


@transact_ro
def get_file(store, key):
    return db_get_file(store, key)


@transact
def del_file(store, key):
    file_obj = store.find(models.File, models.File.id == key).one()
    if file_obj is not None:
        store.remove(file_obj)


def db_get_model_img(store, model, obj_id):
    picture = store.find(model, model.id == obj_id).one().picture
    return picture.data if picture is not None else ''


@transact_ro
def get_model_img(store, model, obj_id):
    return db_get_model_img(store, model, obj_id)



@transact
def add_model_img(store, model, obj_id, data):
    obj = store.find(model, model.id == obj_id).one()
    if obj:
        if obj.picture is None:
            obj.picture = models.File()

        obj.picture.data = data


@transact
def del_model_img(store, model, obj_id):
    obj = store.find(model, model.id == obj_id).one()
    if obj is not None and obj.picture is not None:
        store.remove(obj.picture)


class StaticFileInstance(BaseHandler):
    """
    Handler for files stored on the filesystem
    """
    handler_exec_time_threshold = 3600
    filehandler = True

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self, filename):
        """
        Upload a new file
        """
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            self.set_status(201)
            return

        if filename == 'upload':
            filename = uploaded_file['filename']

        path = os.path.join(GLSettings.static_path, filename)
        directory_traversal_check(GLSettings.static_path, path)

        try:
            dumped_file = yield threads.deferToThread(dump_static_file, uploaded_file, path)
        except Exception as excpd:
            log.err('Error while creating static file %s: %s' % (path, excpd))
            raise errors.InternalServerError(excpd.message)
        finally:
            uploaded_file['body'].close()

        log.debug('Admin uploaded new static file: %s' % dumped_file['filename'])
        self.set_status(201)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def delete(self, filename):
        """
        Parameter: filename
        Errors: StaticFileNotFound
        """
        path = os.path.join(GLSettings.static_path, filename)
        directory_traversal_check(GLSettings.static_path, path)
        if not os.path.exists(path):
            raise errors.StaticFileNotFound

        os.remove(path)


class StaticFileList(BaseHandler):
    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    def get(self):
        """
        Return the list of static files, with few filesystem info
        """
        self.write(get_stored_files())


class FileInstance(BaseHandler):
    key = None

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
        if self.key is None:
            return

        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            self.set_status(201)
            return

        try:
            yield add_file(uploaded_file['body'].read(), self.key)
        except:
            pass
        finally:
            uploaded_file['body'].close()

        GLApiCache.invalidate()

        self.set_status(201)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def delete(self):
        if self.key is None:
            return

        yield del_file(self.key)

        GLApiCache.invalidate()


class NodeLogoInstance(FileInstance):
    key = u'logo'


class NodeCSSInstance(FileInstance):
    key = u'custom_stylesheet'


class ModelImgInstance(BaseHandler):
    model = None

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self, obj_id):
        uploaded_file = self.get_file_upload()
        if uploaded_file is None:
            self.set_status(201)
            return

        try:
            yield add_model_img(self.model, obj_id, uploaded_file['body'].read())
        except:
            pass
        finally:
            uploaded_file['body'].close()

        GLApiCache.invalidate()

        self.set_status(201)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def delete(self, obj_id):
        yield del_model_img(self.model, obj_id)

        GLApiCache.invalidate()


class UserImgInstance(ModelImgInstance):
    model = models.User


class ContextImgInstance(ModelImgInstance):
    model = models.Context
