# -*- coding: UTF-8
#   submission
#   **********
#
#   Implements a GlobaLeaks submission, then the operations performed
#   by an HTTP client in /submission URI

from twisted.internet.defer import inlineCallbacks
from globaleaks.settings import transact
from globaleaks.models import *
from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.jobs.notification_sched import APSNotification
from globaleaks.jobs.delivery_sched import APSDelivery
from globaleaks.runner import GLAsynchronous
from globaleaks.rest import requests
from globaleaks.utils import random_string, log, utcFutureDate, prettyDateTime
from globaleaks.rest.errors import *


def wb_serialize_internaltip(internaltip):
    response = {
        'id' : unicode(internaltip.id),
        # compatibility! until client is not patched.
        'submission_gus' : unicode(internaltip.id),
        'context_gus': unicode(internaltip.context_id),
        'creation_date' : unicode(prettyDateTime(internaltip.creation_date)),
        #'expiration_date' : unicode(utils.prettyDateTime(internaltip.creation_date)),
        'wb_fields' : dict(internaltip.wb_fields or {}),
        'download_limit' : int(internaltip.download_limit),
        'access_limit' : int(internaltip.access_limit),
        'mark' : unicode(internaltip.mark),
        'pertinence' : unicode(internaltip.pertinence_counter),
        'escalation_threshold' : unicode(internaltip.escalation_threshold),
        'files' : [],
        'receivers' : []
    }
    for receiver in internaltip.receivers:
        response['receivers'].append(receiver.id)

    for internalfile in internaltip.internalfiles:
        response['files'].append(internalfile.id)

    return response

@transact
def create_whistleblower_tip(store, submission):
    assert submission is not None and submission.has_key('id')

    wbtip = WhistleblowerTip()
    wbtip.receipt = unicode(random_string(10, 'a-z,A-Z,0-9'))
    wbtip.access_counter = 0
    wbtip.internaltip_id = submission['id']
    store.add(wbtip)
    return wbtip.receipt


def import_receivers(store, submission, receiver_id_list, context, required=False):
    # As first we check if Context has some policies
    if not context.selectable_receiver:
        for receiver in context.receivers:
            # this odd checks, is required! but client do not yet use this piece of code,
            # only unitTest does
            check = store.find(ReceiverInternalTip,
                ( ReceiverInternalTip.receiver_id == receiver.id,
                  ReceiverInternalTip.internaltip_id == submission.id) ).one()
            if not check:
                submission.receivers.add(receiver)
            else:
                log.debug("ContextBased: %s It's already present" % receiver.id)

        store.commit()

        reloaded_submission = store.find(InternalTip, InternalTip.id == submission.id).one()
        log.debug("Fixed receivers corpus by Context (%d) on %s" %\
                (reloaded_submission.receivers.count(), submission.id) )
        return

    # Clean the previous list of selected Receiver
    for prevrec in submission.receivers:
        submission.receivers.remove(prevrec)

    # without contexts policies, import WB requests and checks consistency
    for receiver_id in receiver_id_list:
        try:
            receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
        except Exception, e:
            log.err("Storm/SQL Error: %s (import_receivers)" % e)
            raise e

        if not receiver:
            log.err("Receiver requested do not exist: %s", receiver_id)
            raise ReceiverGusNotFound

        if not context in receiver.contexts:
            raise InvalidInputFormat("Forged receiver selection, you fuzzer! <:")

        submission.receivers.add(receiver)
        log.debug("+receiver [%s] In tip (%s) #%d" %\
                (receiver.name, submission.id, submission.receivers.count() ) )

    if required and submission.receivers.count() == 0:
        log.err("Receivers required to be selected, not empty")
        raise SubmissionFailFields("Receivers required to be completed")


def import_files(store, submission, files):
    for file_id in files:
        try:
            ifile = store.find(InternalFile, InternalFile.id == unicode(file_id)).one()
        except Exception, e:
            log.err("Storm/SQL Error: %s (import_files)" % e)
            raise e
        if not ifile:
            log.err("Invalid File requested %s" % file_id)
            raise FileGusNotFound

        # It's a reference set!
        ifile.internaltip_id = submission.id

    # commit before return
    store.commit()

    reloaded_submission = store.find(InternalTip, InternalTip.id == submission.id).one()
    log.debug("In Submission %s associated files number: %d" %\
              (submission.id, reloaded_submission.internalfiles.count() ))


def import_fields(submission, fields, expected_fields, strict_validation=False):
    """
    @param submission: the Storm object
    @param fields: the received fields
    @param expected_fields: the Context defined fields
    @return: update the object of raise an Exception if a required field
        is missing, or if received field do not match the expected shape

    strict_validation = required the presence of 'required' fields. Is not enforced
    if Submission would not be finalized yet.
    """
    if strict_validation:

        if not fields:
            log.err("Missing submission in 'finalize' request")
            raise SubmissionFailFields("Missing submission!")

        for entry in expected_fields:
            if entry['required']:
                if not fields.has_key(entry['name']):
                    log.err("Submission has a required field (%s) missing" % entry['name'])
                    raise SubmissionFailFields("Missing field '%s': Required" % entry['name'])

    if not fields:
        return

    imported_fields = {}
    for key, value in fields.iteritems():
        key_exists = False

        for entry in expected_fields:
            if key == entry['name']:
                key_exists = True
                break

        if not key_exists:
            log.err("Submission contain an unexpected field %s" % key)
            raise SubmissionFailFields("Submitted field '%s' not expected in context" % key)

        imported_fields.update({key: value})

    submission.wb_fields = imported_fields


def force_schedule():
    # force mail sending, is called force_execution to be sure that Scheduler
    # run the Notification process, and not our callback+user event.
    # after two second create the Receiver tip, after five loop over the emails
    DeliverySched = APSDelivery()
    DeliverySched.force_execution(GLAsynchronous, seconds=2)
    NotifSched = APSNotification()
    NotifSched.force_execution(GLAsynchronous, seconds=5)


@transact
def create_submission(store, request, finalize):
    context = store.find(Context, Context.id == unicode(request['context_gus'])).one()

    if not context:
        log.err("Context requested %s do not exist" % request['context_gus'])
        raise ContextGusNotFound

    submission = InternalTip()

    submission.escalation_threshold = context.escalation_threshold
    submission.access_limit = context.tip_max_access
    submission.download_limit = context.file_max_download
    submission.expiration_date = utcFutureDate(hours=(context.tip_timetolive * 24))
    submission.pertinence_counter = 0
    submission.context_id = context.id
    submission.creation_date = models.now()

    if finalize:
        submission.mark = InternalTip._marker[1] # Finalized
    else:
        submission.mark = InternalTip._marker[0] # Submission

    try:
        store.add(submission)
    except Exception, e:
        log.err("Storm/SQL Error: %s (create_submission)" % e)
        raise e

    receivers = request.get('receivers', [])
    import_receivers(store, submission, receivers, context, required=finalize)

    files = request.get('files', [])
    import_files(store, submission, files)

    fields = request.get('wb_fields', [])
    import_fields(submission, fields, context.fields, strict_validation=finalize)

    submission_dict = wb_serialize_internaltip(submission)
    return submission_dict

@transact
def update_submission(store, id, request, finalize):
    submission = store.find(InternalTip, InternalTip.id == unicode(id)).one()

    if not submission:
        log.err("Invalid Submission requested %s in PUT" % id)
        raise SubmissionGusNotFound

    if submission.mark != InternalTip._marker[0]:
        log.err("Submission %s do not permit update (status %s)" % (id, submission.mark))
        raise SubmissionConcluded

    context = store.find(Context, Context.id == unicode(request['context_gus'])).one()
    if not context:
        log.err("Context requested %s do not exist in UPDATE" % request['context_gus'])
        raise ContextGusNotFound

    # Can't be changed context in the middle of a Submission
    if submission.context_id != context.id:
        log.err("Context can't be changed in the middle (before %s, now %s)" %\
                (submission.context_id, context.id))
        raise ContextGusNotFound

    receivers = request.get('receivers', [])
    import_receivers(store, submission, receivers, context, required=finalize)

    files = request.get('files', [])
    import_files(store, submission, files)

    fields = request.get('wb_fields', [])
    import_fields(submission, fields, submission.context.fields, strict_validation=finalize)

    if finalize:
        submission.mark = InternalTip._marker[1] # Finalized

    submission_dict = wb_serialize_internaltip(submission)
    return submission_dict


@transact
def get_submission(store, id):
    submission = store.find(InternalTip, InternalTip.id == unicode(id)).one()
    if not submission:
        log.err("Invalid Submission requested %s in GET" % id)
        raise SubmissionGusNotFound

    return wb_serialize_internaltip(submission)

@transact
def delete_submission(store, id):
    submission = store.find(InternalTip, InternalTip.id == unicode(id)).one()

    if not submission:
        log.err("Invalid Submission requested %s in DELETE" % id)
        raise SubmissionGusNotFound

    if submission.mark != submission._marked[0]:
        log.err("Submission %s already concluded (%s)" % (id, submission.mark))
        raise SubmissionConcluded

    store.delete(submission)


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

        if request['finalize']:
            finalize = True
        else:
            finalize = False

        status = yield create_submission(request, finalize)

        if finalize:
            receipt = yield create_whistleblower_tip(status)
            status.update({'receipt': receipt})
            force_schedule()
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

        if request['finalize']:
            finalize = True
        else:
            finalize = False

        status = yield update_submission(submission_gus, request, finalize)

        if finalize:
            receipt = yield create_whistleblower_tip(status)
            status.update({'receipt': receipt})
            force_schedule()
        else:
            status.update({'receipt' : ''})

        self.set_status(202) # Updated
        self.finish(status)


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


