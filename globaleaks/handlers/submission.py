# -*- coding: UTF-8
#   submission
#   **********
#
#   Implements a GlobaLeaks submission, then the operations performed
#   by an HTTP client in /submission URI

from twisted.internet.defer import inlineCallbacks
from cyclone.web import asynchronous
from globaleaks.settings import transact
from globaleaks.models import WhistleblowerTip, Receiver, Context, InternalTip, InternalFile
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import requests
from globaleaks.utils import idops, gltime
from globaleaks.rest.errors import InvalidInputFormat, SubmissionGusNotFound,\
    ContextGusNotFound, SubmissionFailFields, SubmissionConcluded, ReceiverGusNotFound, FileGusNotFound


def wb_serialize_internaltip(internaltip):
    response = {
        'id' : unicode(internaltip.id),
        'context_gus': unicode(internaltip.context_id),
        #'creation_date' : unicode(gltime.prettyDateTime(internaltip.creation_date)),
        #'expiration_date' : unicode(gltime.prettyDateTime(internaltip.creation_date)),
        'fields' : dict(internaltip.fields or {}),
        'download_limit' : int(internaltip.download_limit),
        'access_limit' : int(internaltip.access_limit),
        'mark' : unicode(internaltip.mark),
        'pertinence' : unicode(internaltip.pertinence_counter),
        'escalation_threshold' : unicode(internaltip.escalation_threshold),
        'files' : dict(internaltip.files) if internaltip.files else {},
        'receivers' : list(internaltip.receivers) if internaltip.receivers else [],
    }
    return response

@transact
def create_whistleblower_tip(store, submission):
    wbtip = WhistleblowerTip(submission)
    wbtip.receipt = idops.random_receipt()
    store.add(wbtip)
    return wbtip.receipt


def import_receivers(store, submission, receivers, context):
    # As first we check if Context has some policies
    if not context.selectable_receiver:
        for receiver in context.receivers:
            # XXX convert to reference set
            #submission.receivers.add(receiver)
            submission.receivers.append(receiver.id)
        return

    # If not, import WB requests
    for receiver_id in receivers:
        receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
        # XXX convert to reference set
        #submission.receivers.add(receiver)
        if not receiver:
            raise ReceiverGusNotFound
        submission.receivers.append(receiver.id)

def import_files(store, submission, files):

    for file_id in files:
        file = store.find(InternalFile, InternalFile,id == unicode(file_id)).one()
        if not file:
            raise FileGusNotFound

        submission.files.add(file)

def import_fields(store, submission, fields, expected_fields):
    """
    @param submission: the Storm object
    @param fields: the received fields
    @param expected_fields: the Context defined fields
    @return: update the object of raise an Exception if a required field
        is missing, or if received field do not match the expected shape
    """

    for entry in expected_fields:
        if entry['required']:
            if not fields.has_key(entry['name']):
                raise SubmissionFailFields("Missing field '%s': Required" % entry['name'])

    submission.fields = {}
    for key, value in fields.iteritems():
        key_exists = False

        for entry in expected_fields:
            if key == entry['name']:
                key_exists = True
                break

        if not key_exists:
            raise SubmissionFailFields("Submitted field '%s' not expected in context" % k)

        submission.fields.update({key: value})


@transact
def create_submission(store, request):
    context = store.find(Context, Context.id == unicode(request['context_gus'])).one()

    if not context:
        raise ContextGusNotFound
    
    # These are set from the internal tip
    request['escalation_threshold'] = context.escalation_threshold
    request['access_limit'] = context.tip_max_access
    request['download_limit'] = context.file_max_download
    request['expiration_date'] = gltime.utcFutureDate(hours=(context.tip_timetolive * 24))
    request['pertinence_counter'] = 0
    request['mark'] = InternalTip._marker[0]
    request['context_id'] = context.id

    submission = InternalTip(request)
   
    receivers = request.get('receivers')
    del request['receivers']
    import_receivers(store, submission, receivers, context)

    files = request.get('files')
    del request['files']
    import_files(store, submission, files)

    fields = request.get('wb_fields')
    del request['wb_fields']
    import_fields(store, submission, fields, context.fields)

    store.add(submission)
    submission_dict = wb_serialize_internaltip(submission)
    submission_dict['submission_gus'] = unicode(submission.id)
    return submission_dict

@transact
def update_submission(store, id, request):
    submission = store.find(InternalTip, InternalTip.id == unicode(id)).one()

    if not submission:
        raise SubmissionGusNotFound

    if submission.mark != InternalTip._marker[0]:
        raise SubmissionConcluded
   
    context = store.find(Context, Context.id == unicode(request['context_gus'])).one()
   
    if not context:
        raise ContextGusNotFound()

    # Can't be changed context in the middle of a Submission
    if submission.context_id != context.id:
        raise ContextGusNotFound()

    receivers = request.get('receivers')
    del request['receivers']
    import_receivers(store, submission, receivers, context)

    files = request.get('files')
    del request['files']
    import_files(store, submission, files)

    fields = request.get('wb_fields')
    del request['wb_fields']
    import_fields(store, submission, fields, context.fields)

    # TODO update_model
    return wb_serialize_internaltip(submission)

@transact
def get_submission(store, id):

    submission = store.find(InternalTip, InternalTip.id == unicode(id)).one()
    if not submission:
        raise SubmissionGusNotFound

    return wb_serialize_internaltip(submission)

@transact
def delete_submission(store, id):

    submission = store.find(InternalTip, InternalTip.id == unicode(id)).one()

    if not submission:
        raise SubmissionGusNotFound

    if submission.mark != submission._marked[0]:
        raise SubmissionConcluded

    store.delete(submission)

@transact
def finalize_submission(store, id):
    submission = store.find(InternalTip, InternalTip.id == unicode(id)).one()
    submission.mark = u'finalize'

class SubmissionCreate(BaseHandler):
    """
    U2
    This class create the submission, receiving a partial wbSubmissionDesc, and
    returning a submission_gus, usable in update operation.
    """

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

        request = self.validate_message(self.request.body, requests.wbSubmissionDesc)

        status = yield create_submission(request)

        if request['finalize']:
            receipt = yield create_whistleblower_tip(status)
            status.update({'receipt': receipt})
            yield finalize_submission(status['id'])
        else:
            status.update({'receipt' : ''})

        self.set_status(201) # Created
        self.finish(status)


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
        submission = yield get_submission(submission_gus)

        self.set_status(200)
        self.finish(submission)

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

        request = self.validate_message(self.request.body, requests.wbSubmissionDesc)

        status = yield update_submission(submission_gus, request)

        if request['finalize']:
            receipt = yield create_whistleblower_tip(status)
            status.update({'receipt': receipt})
            yield finalize_submission(status['id'])
        else:
            status.update({'receipt' : ''})

        self.set_status(202) # Updated
        self.finish(status)


    @asynchronous
    @inlineCallbacks
    def delete(self, submission_gus, *uriargs):
        """
        Parameter: submission_gus
        Request:
        Response: None
        Errors: SubmissionGusNotFound, SubmissionConcluded

        A whistleblower is deleting a Submission because has understand that won't really be an hero. :P
        """

        yield delete_submission(submission_gus)

        self.set_status(200) # Accepted
        self.finish()


