# -*- coding: utf-8 -*-
import base64
import os

from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.user import can_edit_general_settings_or_raise
from globaleaks.orm import transact, tw
from globaleaks.rest import errors
from globaleaks.utils.fs import directory_traversal_check
from globaleaks.utils.utility import uuid4


@transact
def get_files(session, tid):
    """
    Transaction to retrieve the list of files configured on a tenant

    :param session: An ORM session
    :param tid: The tenant ID on which perform the lookup
    :return: A list of descriptors of the configured files
    """
    ret = []

    for sf in session.query(models.File).filter(models.File.name != "", models.File.tid == tid):
        ret.append({
            'id': sf.id,
            'name': sf.name,
            'data': sf.data,
        })

    return ret


def db_add_file(session, tid, file_id, name, data):
    """
    Transaction to register a file on a tenant

    :param session: An ORM session
    :param tid: The tenant ID
    :param file_id: The ID of the file to be added
    :param name: The file name
    :param data: The file content
    """
    file_obj = models.File()
    file_obj.tid = tid
    file_obj.id = file_id
    file_obj.name = name
    file_obj.data = data
    session.merge(file_obj)


def db_get_file(session, tid, file_id):
    """
    Transaction thecontent of the file identified by the specified id

    :param session: An ORM session
    :param tid: A tenant ID
    :param file_id: A file ID
    :return: The content of the file
    """
    file_obj = session.query(models.File).filter(models.File.tid == tid, models.File.id == file_id).one_or_none()

    return file_obj.data if file_obj is not None else ''


class FileInstance(BaseHandler):
    check_roles = 'user'
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
            d = yield tw(db_add_file, self.request.tid, id, '', data)
        else:
            id = uuid4()
            path = os.path.join(self.state.settings.files_path, id)
            d = yield self.write_upload_plaintext_to_disk(path)
            yield tw(db_add_file, self.request.tid, id, self.uploaded_file['name'], '')

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
    check_roles = 'user'

    def get(self):
        """
        Return the list of files and their info
        """
        return get_files(self.request.tid)
