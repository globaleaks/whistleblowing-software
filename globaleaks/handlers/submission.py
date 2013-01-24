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
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.externaltip import WhistleblowerTip
from globaleaks.utils import log
from globaleaks.handlers.base import BaseHandler
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

        context_iface = Context()
        try:
            request = validateMessage(self.request.body, requests.wbSubmissionDesc)

            # XXX DUMMY PATCH CLIENT USAGE -- open tiket in GLClient
            print "Before", request
            if not request.has_key('wb_fields'):
                request.update({'wb_fields' : ''})
            if not request.has_key('receivers'):
                request.update({'receivers' : []})
            if not request.has_key('files'):
                request.update({'files' : []})
            if not request.has_key('finalize'):
                request.update({'finalize' : False })
            print "After ", request
            # XXX DUMMY PATCH CLIENT USAGE -- open tiket in GLClient

            context_desc = yield context_iface.get_single(request['context_gus'])

            submission_iface = Submission()
            submission_desc = yield submission_iface.new(request)

            if not context_desc['selectable_receiver']:
                submission_iface.receivers = context_iface.receivers

            if submission_desc['finalize']:

                internaltip_iface = InternalTip()
                wb_iface = WhistleblowerTip()

                internaltip_desc = yield internaltip_iface.new(submission_desc)
                wbtip_desc = yield wb_iface.new(internaltip_desc)

                submission_desc.update({'receipt' : wbtip_desc['receipt']})
            else:
                submission_desc.update({'receipt' : ''})

            self.set_status(201) # Created
            # TODO - output processing
            self.write(submission_desc)

        except ContextGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except SubmissionFailFields, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

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
            # TODO perform validation of single GLtype

            status = yield submission.get_single(submission_gus)

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
        Errors: ContextGusNotFound, InvalidInputFormat, SubmissionFailFields, SubmissionGusNotFound, SubmissionConcluded

        PUT update the submission and finalize if requested.
        """

        context_iface = Context()
        try:
            request = validateMessage(self.request.body, requests.wbSubmissionDesc)

            context_desc = yield context_iface.get_single(request['context_gus'])

            submission_iface = Submission()
            submission_desc = yield submission_iface.update(submission_gus, request)

            if not context_desc['selectable_receiver']:
                submission_iface.receivers = context_iface.receivers

            if submission_desc['finalize']:

                internaltip_iface = InternalTip()
                wb_iface = WhistleblowerTip()

                internaltip_desc = yield internaltip_iface.new(submission_desc)
                wbtip_desc = yield wb_iface.new(internaltip_desc)

                submission_desc.update({'receipt' : wbtip_desc['receipt']})
            else:
                submission_desc.update({'receipt' : ''})

            self.set_status(202) # Updated
            # TODO - output processing
            self.write(submission_desc)

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

        except SubmissionConcluded, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except ReceiverGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

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

        submission_iface = Submission()
        try:
            # TODO perform validation of submission_gus format

            yield submission_iface.submission_delete(submission_gus)

            # TODO Delete file associated with submission

            self.set_status(200)

        except SubmissionGusNotFound, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except InvalidInputFormat, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        except SubmissionConcluded, e:

            self.set_status(e.http_status)
            self.write({'error_message': e.error_message, 'error_code' : e.error_code})

        self.finish()


