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

class Submission(Processor):
    handler = None
    model = models.Submission()
    transactor = transactor

    def root_GET(self, *arg, **kw):
        """
        Creates an empty submission and returns the ID to the WB.
        """
        self.handler.status_code = 201
        return {'submission_id': random_submission_id()}

    """
    GET operation is called as return values of other API,
    then nothing has to be *written* then the codeflow
    run here
    """
    def status_GET(self, submission_id, *arg, **kw):
        from datetime import datetime
        status_dict = { 'fields': {'foo': 1234},
                        'groups': ['A', 'B'],
                        'files': [{'name': 'fileA', 'location': '/tmp/foo', 'percent': 100},
                                 {'name': 'fileB', 'location': '/tmp/foo', 'percent': 100},
                                 {'name': 'fileC', 'location': '/tmp/foo', 'percent': 100}],
                        'creation_time': str(datetime.now())
                      }
        return status_dict

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
        print arg
        print kw, "return as GET"
        return status_GET(submission_id, *arg, **kw)

    def files_GET(self, submission_id, *arg, **kw):
        """
        retrive the status of the file uploaded, the 
        submission_id has only one folder during the first
        submission

        XXX remind: in the API-interface is not yet defined
        """
        return {'submission_id': submission_id}

    def files_PUT(self, submission_id, *arg, **kw):
        """
        Take the new data and append to the file, contain sync,
        need to be checked prorperly
        """
        return files_GET(submission_id, *arg, **kw)

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

