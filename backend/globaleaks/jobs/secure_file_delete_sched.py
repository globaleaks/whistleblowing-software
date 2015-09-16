
#
#   secure_file_delete
#   ***************
#
# Implements periodic deletion of files marked for secure removal
#
import time

from twisted.internet.defer import inlineCallbacks
from globaleaks.jobs.base import GLJob
from globaleaks.models import SecureFileDelete
from globaleaks.security import overwrite_and_remove
from globaleaks.settings import transact
from globaleaks.utils.utility import log


__all__ = ['SecureFileDeleteSchedule']


class SecureFileDeleteSchedule(GLJob):
    name = "Secure File Delete"

    @transact
    def get_files_to_secure_delete(self, store):
        files_to_delete = store.find(SecureFileDelete)
        return [file_to_delete.filepath for file_to_delete in files_to_delete]

    @transact
    def commit_file_deletion(self, store, filepath):
        file_to_delete = store.find(SecureFileDelete, SecureFileDelete.filepath == filepath)
        if file_to_delete:
            file_to_delete.remove()

    @inlineCallbacks
    def operation(self):
        files_to_delete = yield self.get_files_to_secure_delete()

        for file_to_delete in files_to_delete:
            self.start_time = time.time()
            log.debug("Starting secure delete of file %s" % file_to_delete)
            overwrite_and_remove(file_to_delete)
            self.commit_file_deletion(file_to_delete)
            current_run_time = time.time() - self.start_time
            log.debug("Ending secure delete of file %s (execution time: %.2f)" % (file_to_delete, current_run_time))
