# -*- coding: utf-8 -*-
#
# /admin/files
#  *****
#
# API handling db files upload/download/delete
import base64
import os

from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.user import can_edit_general_settings_or_raise
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.utils.fs import directory_traversal_check
from globaleaks.utils.utility import uuid4


@transact
def get_files(session, tid):
    ret = []

    for sf in session.query(models.File).filter(models.File.name != u"", models.File.tid == tid):
        ret.append({
            'id': sf.id,
            'name': sf.name,
            'data': sf.data,
        })

    return ret


def db_add_file(session, tid, id, name, data):
    if id is not None:
        file_obj = session.query(models.File).filter(models.File.tid == tid, models.File.id == id).one_or_none()

    if file_obj is None:
        file_obj = models.File()
        file_obj.tid = tid

        if id is not None:
            file_obj.id = id

        session.add(file_obj)

    file_obj.name = name
    file_obj.data = data


@transact
def add_file(session, tid, id, name, data):
    return db_add_file(session, tid, id, name, data)


def db_get_file(session, tid, id):
    file_obj = session.query(models.File).filter(models.File.tid == tid, models.File.id == id).one_or_none()

    return file_obj.data if file_obj is not None else ''


@transact
def get_file(session, tid, id):
    return db_get_file(session, tid, id)


class FileInstance(BaseHandler):
    check_roles =  {'admin', 'receiver', 'custodian'}
    invalidate_cache = True
    upload_handler = True

    def permission_check(self, id):
        if self.current_user.user_role == 'admin' or id == 'logo':
            return can_edit_general_settings_or_raise(self)

        raise errors.InvalidAuthentication

    @inlineCallbacks
    def post(self, id):
        yield self.permission_check(id)

        if id != 'custom':
            sf = self.state.get_tmp_file_by_name(self.uploaded_file['filename'])
            with sf.open('r') as encrypted_file:
                data = encrypted_file.read()

            data = base64.b64encode(data).decode()
            d = yield add_file(self.request.tid, id, u'', data)
        else:
            id = uuid4()
            path = os.path.join(self.state.settings.files_path, id)
            d = yield self.write_upload_plaintext_to_disk(path)
            yield add_file(self.request.tid, id, self.uploaded_file['name'], u'')

        returnValue(d)

    @inlineCallbacks
    def delete(self, id):
        yield self.permission_check(id)

        path = os.path.join(self.state.settings.files_path, id)
        directory_traversal_check(self.state.settings.files_path, path)
        if os.path.exists(path):
            os.remove(path)

        result = yield models.delete(models.File, models.File.tid == self.request.tid, models.File.id == id)
        returnValue(result)


class FileCollection(BaseHandler):
    check_roles =  {'admin', 'receiver', 'custodian'}

    def get(self):
        """
        Return the list of files and their info
        """
        return get_files(self.request.tid)
