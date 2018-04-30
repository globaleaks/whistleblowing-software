# -*- coding: utf-8 -*-
#
# Handlers exposing customization files
import os

from six import text_type
from twisted.internet import defer

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact

@transact
def get_file_id(session, tid, name):
    return models.db_get(session, models.File, models.File.tid == tid, models.File.name == text_type(name)).id


class FileHandler(BaseHandler):
    check_roles = '*'

    @defer.inlineCallbacks
    def get(self, name):
        id = yield get_file_id(self.request.tid, name)

        path = os.path.abspath(os.path.join(self.state.settings.files_path, id))

        yield self.write_file(name, path)
