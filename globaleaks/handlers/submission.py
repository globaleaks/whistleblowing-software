# -*- coding: UTF-8
#   submission
#   **********
#
#   Implements a GlobaLeaks submission, then the operations performed
#   by an HTTP client in /submission URI

from twisted.internet.defer import inlineCallbacks
from cyclone.web import asynchronous
from globaleaks.models.submission import Submission
from globaleaks.models.context import Context
from globaleaks.utils import log
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import requests, responses
from globaleaks.rest.base import validateMessage
from globaleaks.rest.errors import InvalidInputFormat, SubmissionGusNotFound,\
    ContextGusNotFound, SubmissionFailFields

class SubmissionCreate(BaseHandler):
    """
    U2
    This class create the submission, receiving a partial wbSubmissionDesc, and
    returning a submission_gus, usable in update operation.
    """

    @asynchronous
    @inlineCallbacks
    def post(self, *uriargs):
        """
        Request: wbSubmissionDesc
        Response: wbSubmissionDesc
        Errors: ContextGusNotFound, InvalidInputFormat, SubmissionFailFields

        This creates an empty submission for the requested context,
        and returns submissionStatus with empty fields and a Submission Unique String,
        This is the unique token used during the submission procedure.
        sessionGUS is used as authentication secret for the next interaction.
        expire after the time set by Admin (Context dependent setting)
        """

        try:
            request = validateMessage(self.request.body, requests.wbSubmissionDesc)

            submission_iface = Submission()
            context_iface = Context()

            context_info = yield context_iface.public_get_single(request['context_gus'])
            # use requested context, for defaults and so on

            status = yield submission_iface.new(request['context_gus'])
            submission_gus = status['submission_gus']

            if request.has_key('fields'):
                log.debug("Fields present in creation: %s" % request['fields'])
                yield submission_iface.update_fields(submission_gus, request['fields'])

            if request.has_key('receivers'):
                yield submission_iface.select_receiver(submission_gus, request['receivers'])

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

        except AssertionError:

            self.set_status(415)
            self.write({'error_message': "KeyError", 'error_code' : 12345})

        self.finish()


class SubmissionInstance(BaseHandler):
    """
    U3
    This is the interface for create, populate and complete a submission.
    Relay in the client-server update and exchange of the submissionStatus message.
    """

    @asynchronous
    @inlineCallbacks
    def get(self, submission_gus, *uriargs):
        """
        Parameters: submission_gus
        Response: wbSubmissionDesc
        Errors: SubmissionGusNotFound, InvalidInputFormat

        Get the status of the current submission.
        """
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
    def put(self, submission_gus, *uriargs):
        """
        Parameter: submission_gus
        Request: wbSubmissionDesc
        Response: wbSubmissionDesc
        Errors: ContextGusNotFound, InvalidInputFormat, SubmissionFailFields, SubmissionGusNotFound

        PUT finalize and complete the Submission
        """

        try:
            request = validateMessage(self.request.body, requests.wbSubmissionDesc)
            submission = Submission()

            if request.has_key('fields'):
                log.debug("Updating fields with %s" % request['fields'])
                yield submission.update_fields(submission_gus, request['fields'])

            if request.has_key('receivers'):
                log.debug("processing receiver selected: %s" % request['receivers'])
                yield submission.select_receiver(submission_gus, request['receivers'])

            if request.has_key('receipt'):
                yield submission.receipt_proposal(submission_gus, request['receipt'])

            status = yield submission.complete_submission(submission_gus)

            self.set_status(202) # Updated
            # TODO - output processing
            self.write(status)

        except ContextGusNotFound, e:
            # XXX ITS wrong, if a submission start with a context, you can't change them.

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

        except KeyError:

            self.set_status(410)
            self.write({'error_message': "Error not handled", 'error_code' : 12345})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def delete(self, submission_gus, *uriargs):
        """
        Parameter: submission_gus
        Request: wbSubmissionDesc
        Response: None
        Errors: SubmissionGusNotFound, InvalidInputFormat

        A whistleblower is deleting a Submission because has understand that won't really be an hero. :P
        """

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


