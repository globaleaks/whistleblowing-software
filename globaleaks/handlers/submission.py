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


class SubmissionRoot(BaseHandler):
    """
    U2
    This is the interface for push data in the submission
    """

    log.debug("[D] %s %s " % (__file__, __name__), "Class SubmissionRoot", "BaseHandler", BaseHandler)

    @asynchronous
    @inlineCallbacks
    def get(self, context_gus, *uriargs):
        """
            * Request
              GET /submission/<$context_gus>/new

        This creates an empty submission for the requested context,
        and returns a GlobaLeaks Uniqe String, to be used during the submission
        procedure.
        sessionGUS is used as authentication secret for the next interaction.
        expire after the time set by Admin, in the Context

            * Response:
              {
                  'submission_gus': 'sessionID',
                  'creation_time': 'Time'
              }
              Status code: 201 (Created)
        """
        log.debug("[D] %s %s " % (__file__, __name__), "SubmissionRoot", "GET / context = ", context_gus)

        submission = Submission()

        try:
            output = yield submission.new(context_gus)
            self.set_status(201)
            self.write(output)

        except InvalidContext, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

class SubmissionStatus(BaseHandler):
    """
    U3
    This interface represent the state of the submission. Will show the current
    uploaded data, selected context, file uploaded.
    permit to update fields content, context selection, and if supported, specify receivers
    """

    log.debug("[D] %s %s " % (__file__, __name__), "Class SubmissionStatus", "BaseHandler", BaseHandler)

    @asynchronous
    @inlineCallbacks
    def get(self, submission_gus):
        """
        Returns the currently submitted fields, selected context, and time to live of the
        submission

        * Response:
          {
            'fields': [ '$formFieldsDict' ],
            'receivers_selected': [ '$receiverDescriptionDict' ],
            'creation_time': 'Time'
            'expiration_time': 'Time'
          }
        """
        log.debug("[D] %s %s " % (__file__, __name__), "SubmissionStatus", "get", "submission_gus", submission_gus )

        submission = Submission()

        try:
            status = yield submission.status(submission_gus)
            self.set_status(200)
            self.write(status)

        except SubmissionNotFoundError, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def post(self, submission_gus, *uriargs):
        """
        * Request:
          {
            'fields': [ '$formFieldsDict' ]
            'receiver_selected': [ 'receiverID', 'receiverID' ]
            'context_selected': 'contextID'
          }

        * Response:
          Status Code: 202 (accepted)

        * Error handling:
          As per "common behaviour in /submission/<submission_$ID/*"
          If receiver ID is invalid:
            { 'error_code': 'Int', 'error_message': 'receiver selected ID is invalid' }
          a receiver ID is invalid if:
            . receiver do not match in the context
          If the property of "receiver selection" is not set, the receiver_selected value
          is IGNORED.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "SubmissionStatus", "post", "submission_gus", submission_gus)
        #request = messages.validateMessage(self.request.body,
        #                            messages.requests.submissionStatus)

        request = json.loads(self.request.body)

        submission = Submission()

        # set a Bad Request return value, that is not override if fields or
        # context is not present. TODO: fields or receivers.
        self.set_status(400)

        if 'fields' in request and request['fields']:
            log.debug("Updating fields with %s" % request['fields'])
            yield submission.update_fields(submission_gus, request['fields'])
            self.set_status(202)

        if 'receiver_selected' in request and request['receiver_selected']:
            log.debug("Receiver selection in %s" % submission_gus)
            yield submission.select_receiver(submission_gus, request['receiver_selected'])
            # TODO handle errors: a context may not permit receivers selection
            self.set_status(202)

        self.finish()


class SubmissionFinalize(BaseHandler):
    """
    U4
    This interface cause the ending of the submnission process, need to be
    merged with whatever TODO.
    """

    @asynchronous
    @inlineCallbacks
    def post(self, submission_gus, *uriargs):
        """
        checks if all the 'Required' fields are present, then
        completes the submission in progress and returns a receipt.
        The WB may propose a receipt (because is a personal secret
        like a password, afterall)

        * Request (optional, see "Rensponse Variant" below):
          {
            'proposed_receipt': 'string'
            'folder_name': 'string'
            'folder_description': 'string'
          }

        * Response (HTTP code 412, Precondition Failed):
          If one of the fileDict is not complete, the finalize can't be performed.
          { 'error_code': 'Int', 'error_message': 'The upload appears not yet complete' }

        * Response (HTTP code 200):
          If the receipt is acceptable, the node can't know what's the original
          password value, because is generated by an hashing function. If the node
          permit to the whistleblower to configure their receipt, is
          during the context configuration), i saved as authenticative secret for
          the WB Tip, is echoed back to the client Status Code: 201 (Created)

          Status Code: 200 (OK)
          { 'receipt': 'string (with receipt EQUAL to proposed-receipt)' }

        * Response (HTTP code 201):
          If the receipt do not fit node prerequisite, or is missing,
          the submission is finalized, and the server create a receipt.
          The client print back the receipt to the WB.

          Status Code: 201 (Created)
          { 'receipt': 'string' }

        Both response finalize the submission and the only difference is in the
        HTTP return code. This has been discussed (or would be discussed)
        [issue #19, Receipt, proposal of expansion](https://github.com/globaleaks/GLBackend/issues/19)
        * Error handling:
          As per "common behaviour in /submission/<submission_$GUS/*"

          If the field check fail
          Status Code: 406 (Not Acceptable)
          { 'error_code': 'Int', 'error_message': 'fields requirement not respected' }

        """
        log.debug("[D] %s %s " % (__file__, __name__), "SubmissionFinalize", "post", "submission_gus", submission_gus)

        request = json.loads(self.request.body)

        wb_proposal = None
        if 'proposed_receipt' in request and request['proposed_receipt']:
            wb_proposal = request['proposed_receipt']

        submission = Submission()

        try:
            receipt_used = yield submission.complete_submission(submission_gus, wb_proposal)
            # complete_submission may return a receipt, if the node is not
            # configured for accept remote proposal

            if receipt_used == wb_proposal:
                self.set_status(200) # OK, receipt accepted
            else:
                self.set_status(201) # Created new receipt
                self.write({ "receipt" : receipt_used})

        except SubmissionNotFoundError, e:
            self.set_status(e.http_status) # all error need to be managed with different code
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


