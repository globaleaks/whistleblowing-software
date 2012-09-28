# -*- coding: UTF-8
#   submission
#   **********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Implements a GlobaLeaks submission.

from twisted.internet.defer import returnValue, inlineCallbacks
from globaleaks.db import models, transactor
from globaleaks.db import transact
from globaleaks.utils.random import random_string
from globaleaks import Processor

from globaleaks.utils import recurringtypes as GLT
from datetime import datetime
from globaleaks.utils import dummy


"""
Move this utility in globaleaks.utils.random or globaleaks.utils.id ?
remind: ID need to be unique, and may support a prefix
"""
def random_submission_id():
    import random
    import string
    length = 50
    return ''.join(random.choice(string.ascii_letters) for x in range(length))

def random_receipt_id():
    import random
    import string
    length = 10
    return ''.join(random.choice('0123456789') for x in range(length))

class newSubmission(GLT.GLTypes):
    def __init__(self):
        GLT.GLTypes.__init__(self, self.__class__.__name__)
        self.define('submission_id', 'sessionID')

class submissionStatus(GLT.GLTypes):

    def __init__(self):

        GLT.GLTypes.__init__(self, self.__class__.__name__)

        self.define('creation_time', 'Time')
        self.define_array('fields', GLT.formFieldsDict(), 1)
        self.define_array('receivers')


class Submission(Processor):
    handler = None
    model = models.Submission()
    transactor = transactor

    # U2
    def new_GET(self, *arg, **kw):
        """
        Creates an empty submission and returns the ID to the WB.
        """
        self.handler.status_code = 201
        ret = newSubmission()

        dummy.SUBMISSION_NEW_GET(ret)

        return ret.unroll()

    """
    GET operation is called as return values of other API,
    then nothing has to be *written* then the codeflow
    run here -- U3
    """
    def status_GET(self, submission_id, *arg, **kw):

        ret = submissionStatus()

        dummy.SUBMISSION_STATUS_GET(ret)

        return ret.unroll()

    """
    status handle the group receiver selection 
        (if enabled in the context settings)
    handle the fields submission
        (import the fields in the temporary submission_id entry)
    """
    def status_POST(self, *arg, **kw):
        """
        :fields
        :group
        """
        return status_GET(arg, kw)

    # U4
    def files_GET(self, submission_id, *arg, **kw):
        """
        retrive the status of the file uploaded, the 
        submission_id has only one folder during the first
        submission

        XXX remind: in the API-interface is not yet defined
        """
        ret = GLT.fileDict()
        dummy.SUBMISSION_FILES_GET(ret)
        return ret.unroll()

    def files_PUT(self, submission_id, *arg, **kw):
        """
        Take the new data and append to the file, contain sync,
        need to be checked prorperly
        """
        return files_GET(arg, kw)

    def files_POST(self, submission_id, *arg, **kw):
        """
        :description, dict of text describig the file uploaded
         (or not yet complete) by PUT, every time a new
         files_POST is reached, all the files description is 
         updated
        """
        return files_GET(submission_id, *arg, **kw)

    def files_DELETE(self, submission_id, *arg, **kw):
        """
        :filename, remove a complete or a partial uploaded 
         file
        """
        return files_GET(submission_id, *arg, **kw)


    # U5
    @inlineCallbacks
    def finalize_POST(self, submission_id, **form_fields):
        """
        Finalize the submission and create data inside of the database.
        """
        receipt_id = unicode(random_receipt_id())
        self.handler.status_code = 201
        internal_tip = models.InternalTip()
        internal_tip.fields = form_fields

        yield internal_tip.save()

        whistleblower_tip = models.Tip()
        whistleblower_tip.internaltip_id = internal_tip.id
        whistleblower_tip.address = receipt_id

        yield whistleblower_tip.save()

        returnValue({'receipt': receipt_id})

