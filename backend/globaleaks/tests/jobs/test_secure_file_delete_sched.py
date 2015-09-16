# -*- coding: utf-8 -*-

import os 

from twisted.internet.defer import inlineCallbacks

from globaleaks.models import SecureFileDelete
from globaleaks.settings import GLSettings, transact
from globaleaks.tests import helpers

from globaleaks.jobs import secure_file_delete_sched


class TestSecureFileDeleteSched(helpers.TestGLWithPopulatedDB):
    @transact
    def create_two_files_and_mark_them_for_deletion(self, store):
        for i in range(0, 2):
            to_delete = os.path.join(GLSettings.submission_path, 'to_delete' + str(i))
            with open(to_delete, 'w+b') as f:
                f.write("0123456789" * 10000)
            secure_file_delete = SecureFileDelete()
            secure_file_delete.filepath = to_delete
            store.add(secure_file_delete)

    @inlineCallbacks
    def test_secure_file_delete_sched(self):
        yield self.create_two_files_and_mark_them_for_deletion()
        yield secure_file_delete_sched.SecureFileDeleteSchedule().operation()

