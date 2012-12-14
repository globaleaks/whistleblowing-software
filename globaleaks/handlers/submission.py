# -*- coding: UTF-8
#   submission
#   **********
#
#   Implements a GlobaLeaks submission, then the operations performed
#   by an HTTP client in /submission URI

import json

from twisted.internet.defer import inlineCallbacks
from cyclone.web import asynchronous
from globaleaks.models.submission import Submission
from globaleaks.utils import log
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import requests, responses
from globaleaks.rest.base import validateMessage
from globaleaks.rest.errors import InvalidInputFormat, SubmissionGusNotFound,\
    ContextGusNotFound, SubmissionFailFields

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
        Parameters: submission_gus
        Response: wbSubmissionDesc
        Errors: SubmissionGusNotFound, InvalidInputFormat

        Get the status of the current submission.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "SubmissionCrud GET")

        submission = Submission()

        try:

            requested_sg = self.get_argument('submission_gus')
            # TODO perform validation of single GLtype

            status = yield submission.status(requested_sg)
            self.set_status(200)
            self.write(status)

        except SubmissionGusNotFound, e:

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
        Request: wbSubmissionDesc
        Response: wbSubmissionDesc
        Errors: ContextGusNotFound, InvalidInputFormat, SubmissionFailFields

        This creates an empty submission for the requested context,
        and returns submissionStatus with empty fields and a Submission Uniqe String,
        This is the unique token used during the submission procedure.
        sessionGUS is used as authentication secret for the next interaction.
        expire after the time set by Admin (Context dependent setting)
        """
        log.debug("[D] %s %s " % (__file__, __name__), "SubmissionCrud POST")

        try:
            request = validateMessage(self.request.body, requests.wbSubmissionDesc)
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

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except SubmissionFailFields, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

    def put(self, *uriargs):
        """
        Request: wbSubmissionDesc
        Response: wbSubmissionDesc
        Errors: ContextGusNotFound, InvalidInputFormat, SubmissionFailFields, SubmissionGusNotFound

        Update a Submission resource with the appropriate data
        """
        log.debug("[D] %s %s " % (__file__, __name__), "SubmissionCrud PUT")

        try:
            request = validateMessage(self.request.body, requests.wbSubmissionDesc)
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

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except SubmissionFailFields, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except SubmissionGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    def delete(self, *uriargs):
        """
        Request: wbSubmissionDesc
        Response: None
        Errors: SubmissionGusNotFound, InvalidInputFormat

        A whistleblower is deleting a Submission because has understand that won't really be an hero. :P
        """
        log.debug("[D] %s %s " % (__file__, __name__), "SubmissionCrud DELETE")

        try:
            request = validateMessage(self.request.body, requests.wbSubmissionDesc)
            submission = Submission()

            submission.submission_delete(request.submission_gus)

        except SubmissionGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()
