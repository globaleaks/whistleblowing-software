# -*- coding: UTF-8
#   submission
#   **********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Implements a GlobaLeaks submission.

from twisted.internet.defer import returnValue, inlineCallbacks

from globaleaks import models
from globaleaks.db import transactor
from globaleaks.utils import idops

from globaleaks.rest import answers
from globaleaks.rest.errors import GLErrorCode

from cyclone.web import RequestHandler, asynchronous, HTTPError

def mydirtydebug(whoami, safereq, uriargs, args, kw):
    print "[:>]", whoami, safereq, type(uriargs), uriargs, args, kw


class SubmissionRoot(RequestHandler):
    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        U2, Creates an empty submission and returns the ID to the WB.
        """
        # XXX do sanitization and validation here

        self.set_status(201)

        new_submission = models.base.Submission()
        new_submission.submission_id = unicode(idops.random_submission_id(False))
        new_submission.folder_id = 0

        # --------------------------------------
        # In a stable implementation, .fields would be set with the
        # default taken by context
        # In this case, are used the dummy values
        # 'fields' and 'receivers' both
        from globaleaks.messages.dummy import base, answers, requests

        fake_submission = requests.submissionStatusPost
        new_submission.fields = fake_submission['fields']

        fake_receivers = [idops.random_receiver_id(),
                          idops.random_receiver_id(),
                          idops.random_receiver_id(),
                          idops.random_receiver_id()]
        new_submission.receivers = fake_receivers

        output = {"submission_id": new_submission.submission_id}

        yield new_submission.save()
        self.write(output)
        self.finish()
        # dummy.SUBMISSION_NEW_GET(output)

class SubmissionStatus(RequestHandler):
    @asynchronous
    @inlineCallbacks
    def get(self, submission_id):
        """
        U3, refresh whistleblower client with the previously uploaded data
        """
        submission = models.base.Submission()
        status = yield submission.status(submission_id)

        self.set_status(200)

        self.write(status)

        self.finish()

    """
    status handle the group receiver selection
        (if enabled in the context settings)
    handle the fields submission
        (import the fields in the temporary submission_id entry)
    """

    @asynchronous
    @inlineCallbacks
    def post(self, submission_id, *uriargs):
        """
        U3, update the whistleblower stored data, expect in safereq
        fields: an array of formFieldsDict
        receivers: an array of receiverID
        verify in the local settings if the receivers shall be choosen by WB
        if some fields are required, is not check here.
        """
        yield self.get(submission_id, *uriargs)


class SubmissionFinalize(RequestHandler):
    @asynchronous
    @inlineCallbacks
    def post(self, submission_id, *uriargs):
        """
        Finalize the submission and create data inside of the database,
        perform checks if the required fiels has been set
        """
        receipt_id = unicode(idops.random_receipt_id())

        submission = models.base.Submission()
        yield submission.create_tips(submission_id, receipt_id)

        self.set_status(201)

        receipt = {"receipt": receipt_id}
        self.write(receipt)
        self.finish()

class SubmissionFiles(RequestHandler):
    # U5
    def get(self, submission_id, *uriarg):
        """
        retrive the status of the file uploaded, the
        submission_id has only one folder during the first
        submission

        XXX remind: in the API-interface is not yet defined
        """
        from globaleaks.messages.dummy import base, answers, requests

        return base.fileDicts[0]

    def put(self, submission_id, *uriarg):
        """
        Take the new data and append to the file, contain sync,
        need to be checked prorperly
        """
        return self.get(submission_id, *uriarg)

    def post(self, submission_id, *uriarg):
        """
        :description, dict of text describig the file uploaded
         (or not yet complete) by PUT, every time a new
         files_POST is reached, all the files description is
         updated
        """
        return self.get(submission_id, *uriarg)

    def delete(self, submission_id, *arg, **kw):
        """
        :filename, remove a complete or a partial uploaded
         file
        """
        return self.get(submission_id, *uriarg)
