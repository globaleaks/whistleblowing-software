
from globaleaks.transactors.base import MacroOperation

from globaleaks.models.externaltip import File
from globaleaks.models.submission import Submission
from globaleaks.rest.errors import SubmissionConcluded
from globaleaks.config import config

from storm.twisted.transact import transact
import time, json, os

class FileOperations(MacroOperation):
    """
    README.md describe pattern and reasons
    """

    @transact
    def get_files(self, submission_gus):

        file_iface = File(self.getStore())

        filelist = file_iface.get_all_by_submission(submission_gus)

        self.returnData(filelist)
        self.returnCode(200)
        return self.prepareRetVals()

    def _dump_file(self, file, submission_gus, file_gus):

        result = {}
        result['file_gus'] = file_gus
        result['name'] = file['filename']
        result['type'] = file['content_type']
        result['size'] = len(file['body'])

        # XXX verify this token what's is it
        result['token'] = submission_gus

        if not os.path.isdir(config.advanced.submissions_dir):
            print "%s does not exist. Creating it." % config.advanced.submissions_dir
            os.mkdir(config.advanced.submissions_dir)

        the_submission_dir = config.advanced.submissions_dir

        # this happen only at the first execution
        if not os.path.isdir(the_submission_dir):
            os.mkdir(the_submission_dir)

        filelocation = os.path.join(the_submission_dir, file_gus)

        print "Saving file to %s" % filelocation
        # TODO This is currently blocking. MUST be refactored to not be blocking
        # otherwise we loose...
        with open(filelocation, 'a+') as f:
            f.write(file['body'])

        return result

    @transact
    def new_files(self, submission_gus, request):

        store = self.getStore()

        submission_desc = Submission(store).get_single(submission_gus)

        if submission_desc['finalize']:
            raise SubmissionConcluded

        result_list = []

        file_array, files = request.files.popitem()

        for single_file in files:

            start_time = time.time()

            file_request = { 'filename' : single_file.get('filename'),
                             'content_type' : single_file.get('content_type'),
                             'file_size' : len(single_file['body']),
                             'submission_gus' : submission_gus,
                             'context_gus' : submission_desc['context_gus'],
                             'description' : ''
            }

            file_iface = File(store)
            file_desc = file_iface.new(file_request)

            print "Created file from %s with file_gus %s" % (file_request['filename'], file_desc['file_gus'])

            result = self._dump_file(single_file, submission_gus, file_desc['file_gus'])
            result['elapsed_time'] = time.time() - start_time
            result_list.append(result)

        self.returnData(result_list)
        self.returnCode(200)
        return self.prepareRetVals()

