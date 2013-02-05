# -*- coding: UTF-8
#   submission
#   **********
#
#   Implements a GlobaLeaks submission, then the operations performed
#   by an HTTP client in /submission URI

from twisted.internet.defer import inlineCallbacks
from cyclone.web import asynchronous
from globaleaks.utils import log
from globaleaks.handlers.base import BaseHandler
from globaleaks.transactors.crudoperations import CrudOperations
from globaleaks.rest import requests, responses
from globaleaks.rest.base import validateMessage
from globaleaks.rest.errors import InvalidInputFormat, SubmissionGusNotFound,\
    ContextGusNotFound, SubmissionFailFields, SubmissionConcluded, ReceiverGusNotFound


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

            answer = yield CrudOperations().new_submission(request)

            # TODO - output processing
            self.set_status(answer['code'])
            self.json_write(answer['data'])

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except SubmissionFailFields, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

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

        try:
            # validateParameter(submission_gus, requests.submissionGUS)
            answer = yield CrudOperations().get_submission(submission_gus)

            # TODO - output processing
            self.set_status(answer['code'])
            self.json_write(answer['data'])

        except SubmissionGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()

    @asynchronous
    @inlineCallbacks
    def put(self, submission_gus, *uriargs):
        """
        Parameter: submission_gus
        Request: wbSubmissionDesc
        Response: wbSubmissionDesc
        Errors: ContextGusNotFound, InvalidInputFormat, SubmissionFailFields, SubmissionGusNotFound, SubmissionConcluded

        PUT update the submission and finalize if requested.
        """

        try:
            # validateParameter(submission_gus, requests.submissionGUS)
            request = validateMessage(self.request.body, requests.wbSubmissionDesc)

            answer = yield CrudOperations().update_submission(submission_gus, request)

            # TODO - output processing
            self.set_status(answer['code'])
            self.json_write(answer['data'])

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except SubmissionFailFields, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except SubmissionGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except SubmissionConcluded, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


    @asynchronous
    @inlineCallbacks
    def delete(self, submission_gus, *uriargs):
        """
        Parameter: submission_gus
        Request: 
        Response: None
        Errors: SubmissionGusNotFound, InvalidInputFormat, SubmissionConcluded

        A whistleblower is deleting a Submission because has understand that won't really be an hero. :P
        """

        try:
            # validateParameter(submission_gus, requests.submissionGUS)

            answer = yield CrudOperations().delete_submission(submission_gus)

            self.set_status(answer['code'])

        except SubmissionGusNotFound, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        except SubmissionConcluded, e:

            self.set_status(e.http_status)
            self.json_write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


