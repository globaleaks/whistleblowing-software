# -*- coding: UTF-8
#   submission
#   **********
#   :copyright: 2012 Hermes No Profit Association - GlobaLeaks Project
#   :author: Claudio Agosti <vecna@globaleaks.org>, Arturo Filastò <art@globaleaks.org>
#   :license: see LICENSE
#
#   Implements a GlobaLeaks submission.
import json

from twisted.internet.defer import inlineCallbacks
from cyclone.web import asynchronous
from globaleaks.models.submission import Submission, SubmissionNotFoundError
from globaleaks.utils import log
from globaleaks.handlers.base import BaseHandler
from globaleaks.models.context import InvalidContext
from globaleaks import messages
from globaleaks.messages.errors import InvalidInputFormat

class SubmissionCrud(BaseHandler):
    """
    U2
    This is the interface for create, populate and complete a submission.
    Relay in the client-server update and exchange of the submissionStatus message.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: base.submissionStatus
        Errors: SubmissionNotFoundError, InvalidInputFormat

        Get the status of the current submission.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "SubmissionCrud GET")

        submission = Submission()

        try:
            request = messages.validateMessage(self.request.body, messages.base.submissionStatus)
            status = yield submission.status(request.submission_gus)
            self.set_status(200)
            self.write(status)

        except SubmissionNotFoundError, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Request: base.submissionStatus
        Response: base.submissionStatus
        Errors: InvalidContext, InvalidInputFormat, InvalidFields

        This creates an empty submission for the requested context,
        and returns submissionStatus with empty fields and a Submission Uniqe String,
        This is the unique token used during the submission procedure.
        sessionGUS is used as authentication secret for the next interaction.
        expire after the time set by Admin (Context dependent setting)
        """
        log.debug("[D] %s %s " % (__file__, __name__), "SubmissionCrud POST")

        try:
            request = messages.validateMessage(self.request.body, messages.base.submissionStatus)
            submission = Submission()

            status = yield submission.new(request.context_gus)
            submission_gus = status['submission_gus']

            log.debug("Updating fields with %s" % request['fields'])
            if request.fields:
                yield submission.update_fields(submission_gus, request.fields)

            if request.receiver_selected:
                yield submission.select_receiver(submission_gus, request.receiver_selected)

            self.set_status(201) # Created
            # TODO - output processing
            self.write(status)

        except InvalidContext, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

    def put(self, *uriargs):
        """
        Request: base.submissionStatus
        Response: base.submissionStatus
        Errors: InvalidContext, InvalidInputFormat, InvalidSubmissionFields, SubmissionNotFound

        Update a Submission resource with the appropriate data
        """
        log.debug("[D] %s %s " % (__file__, __name__), "SubmissionCrud PUT")

        try:
            request = messages.validateMessage(self.request.body, messages.base.submissionStatus)
            submission = Submission()

            log.debug("Updating fields with %s" % request['fields'])
            if request.fields:
                yield submission.update_fields(request.submission_gus, request['fields'])

            if request.receiver_selected:
                yield submission.select_receiver(request.submission_gus, request['receiver_selected'])

            if request.receipt:
                yield submission.receipt_proposal(request.submission_gus, request.receipt)

            status = yield submission.status(request.submission_gus)

            if request.complete:
                confirmed_receipt = yield submission.complete_submission(request.submission_gus)
                status['real_receipt'] = confirmed_receipt

            self.set_status(202) # Updated
            # TODO - output processing
            self.write(status)

        except InvalidContext, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        # XXX
        # need to be split between InvalidInputFormat (used by all the REST making input
        # validation) and InvalidSubmissionFields (checks the fields list of submissionStatus)
        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except SubmissionNotFoundError, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    def delete(self, *uriargs):
        """
        Request: base.submissionStatus
        Response: None
        Errors: SubmissionNotFound. InvalidInputFormat

        A whistleblower is deleting a Submission because has understand that won't really be an hero. :P
        """
        log.debug("[D] %s %s " % (__file__, __name__), "SubmissionCrud DELETE")

        try:
            request = messages.validateMessage(self.request.body, messages.base.submissionStatus)
            submission = Submission()

            submission.submission_delete(request.submission_gus)

        except SubmissionNotFoundError, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()
