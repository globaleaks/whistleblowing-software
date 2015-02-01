# -*- coding: UTF-8
#
#   v2submission
#   ************
#
#   Implements a GlobaLeaks submission, then the operations performed
#   by an HTTP client in /submission/context_id URI
#
#   This implementation

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import transact, GLSetting
from globaleaks.models import *
from globaleaks import security
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import transport_security_check, unauthenticated
from globaleaks.rest import requests
from globaleaks.utils.utility import log, utc_future_date, datetime_now, datetime_to_ISO8601
from globaleaks.utils.structures import Fields
from globaleaks.third_party import rstr
from globaleaks.rest import errors
from globaleaks.anomaly import Alarm

def wb_serialize_internaltip(internaltip):

    response = {
        'id' : internaltip.id,
        'context_id': internaltip.context_id,
        'creation_date' : datetime_to_ISO8601(internaltip.creation_date),
        'expiration_date' : datetime_to_ISO8601(internaltip.expiration_date),
        'wb_fields' : internaltip.wb_fields,
        'download_limit' : internaltip.download_limit,
        'access_limit' : internaltip.access_limit,
        'mark' : internaltip.mark,
        'pertinence' : internaltip.pertinence_counter,
        'escalation_threshold' : internaltip.escalation_threshold,
                  # list is needed because .values returns a generator
        'files' : list(internaltip.internalfiles.values(InternalFile.id)),
                      # list is needed because .values returns a generator
        'receivers' : list(internaltip.receivers.values(Context.id)),
    }

    return response

@transact
def create_whistleblower_tip(store, submission_desc):
    """
    The plaintext receipt is returned only now, and then is
    stored hashed in the WBtip table
    """
    assert submission_desc is not None and submission_desc.has_key('id')

    wbtip = WhistleblowerTip()

    node = store.find(Node).one()

    return_value_receipt = unicode( rstr.xeger(node.receipt_regexp) )
    wbtip.receipt_hash = security.hash_password(return_value_receipt, node.receipt_salt)

    wbtip.access_counter = 0
    wbtip.internaltip_id = submission_desc['id']
    store.add(wbtip)

    return return_value_receipt


# Remind: has a store between arguments because called by a @ŧransact
# TODO refactor this in a more cleaned approach + keep in mind the future Receiver properties
# TODO remind that CLClient don't support the 'not selectable receiver'
def import_receivers(store, submission, receiver_id_list, required=False):
    context = submission.context

    # As first we check if Context has some policies
    if not context.selectable_receiver:
        for receiver in context.receivers:
            # Skip adding receivers that don't have PGP enabled if encrypted only.
            if not GLSetting.memory_copy.allow_unencrypted and \
                    receiver.gpg_key_status != u'Enabled':
                continue
            # Add only the receiver not yet associated in Many-to-Many
            check = store.find(ReceiverInternalTip,
                ( ReceiverInternalTip.receiver_id == receiver.id,
                  ReceiverInternalTip.internaltip_id == submission.id) ).one()
            if not check:
                submission.receivers.add(receiver)

        reloaded_submission = store.find(InternalTip, InternalTip.id == submission.id).one()
        log.debug("Context [%s] has a fixed receivers corpus #%d SID = %s" %
                (reloaded_submission.context.name[GLSetting.memory_copy.default_language],
                 reloaded_submission.receivers.count(), submission.id) )
        return

    # Before has been handled the 'fixed receiver corpus',
    # Below we handle receiver personal selection

    # Clean the previous list of selected Receiver
    for prevrec in submission.receivers:
        try:
            submission.receivers.remove(prevrec)
        except Exception as excep:
            log.err("Unable to remove receiver from Tip, before new reassignment")
            raise excep

    # and now clean the received list and import the new Receiver set.
    receiver_id_list = set(receiver_id_list)

    if required and (not len(receiver_id_list)):
        log.err("Receivers required to be selected, not empty")
        raise errors.SubmissionFailFields("Needed almost one Receiver selected [1]")

    if context.maximum_selectable_receivers and \
                    len(receiver_id_list) > context.maximum_selectable_receivers:
        raise errors.InvalidInputFormat("Provided an invalid number of Receivers")

    for receiver_id in receiver_id_list:
        try:
            receiver = store.find(Receiver, Receiver.id == unicode(receiver_id)).one()
        except Exception as excep:
            log.err("Receiver requested (%s) can't be found: %s" %
                    (receiver_id, excep))
            raise errors.ReceiverIdNotFound

        if not context in receiver.contexts:
            raise errors.InvalidInputFormat("Forged receiver selection, you fuzzer! <:")

        try:
            if not GLSetting.memory_copy.allow_unencrypted and \
                    receiver.gpg_key_status != u'Enabled':
                log.err("Encrypted only submissions are supported. Cannot select [%s]" % receiver_id)
                continue
            submission.receivers.add(receiver)
        except Exception as excep:
            log.err("Receiver %s can't be assigned to the tip [%s]" % (receiver_id, excep) )
            continue

        log.debug("+receiver [%s] In tip (%s) #%d" %\
                (receiver.name, submission.id, submission.receivers.count() ) )
    
    if required and submission.receivers.count() == 0:
        log.err("Receivers required to be selected, not empty")
        raise errors.SubmissionFailFields("Needed at least one Receiver selected [2]")


# Remind: it's a store without @transaction because called by a @ŧransact
def import_files(store, submission, files, finalize):
    """
    @param submission: the Storm obj
    @param files: the list of InternalFiles UUIDs
    @return:
        Look if all the files specified in the list exist,
        Look if the context *require* almost a file, raise
            an error if missed
    """
    for file_id in files:
        try:
            ifile = store.find(InternalFile, InternalFile.id == unicode(file_id)).one()
        except Exception as excep:
            log.err("Storm error, not found %s file in import_files (%s)" %
                    (file_id, excep))
            raise errors.FileIdNotFound

        ifile.internaltip_id = submission.id

    if finalize and submission.context.file_required and not len(files):
        log.debug("Missing file for a submission in context %s" %
                  submission.context.name)
        raise errors.FileRequiredMissing


@transact
def create_submission(store, request, language=GLSetting.memory_copy.default_language):
    context = store.find(Context, Context.id == unicode(request['context_id'])).one()
    if not context:
        log.err("Context requested: [%s] not found!" % request['context_id'])
        raise errors.ContextIdNotFound

    submission = InternalTip()

    submission.escalation_threshold = context.escalation_threshold
    submission.access_limit = context.tip_max_access
    submission.download_limit = context.file_max_download
    submission.expiration_date = utc_future_date(seconds=context.tip_timetolive)
    submission.pertinence_counter = 0
    submission.context_id = context.id
    submission.creation_date = datetime_now()

    submission.mark = InternalTip._marker[1] # Finalized
    # TODO review the submission status list
    # TODO add in the internaltip the submission outcome (because are part of the statistics)

    try:
        store.add(submission)
    except Exception as excep:
        log.err("Storm/SQL Error: %s (create_submission)" % excep)
        raise errors.InternalServerError("Unable to commit on DB")

    try:
        import_files(store, submission, request['files'], True)
    except Exception as excep:
        log.err("Submission create: files import fail: %s" % excep)
        raise excep

    try:
        wb_fields = request['wb_fields']
        fo = Fields(context.localized_fields, context.unique_fields)
        fo.validate_fields(wb_fields, language, strict_validation=True)
        submission.wb_fields = wb_fields
    except Exception as excep:
        log.err("Submission create: fields validation fail: %s" % excep)
        raise excep

    try:
        import_receivers(store, submission, request['receivers'], required=True)
    except Exception as excep:
        log.err("Submission create: receivers import fail: %s" % excep)
        raise excep

    submission_dict = wb_serialize_internaltip(submission)
    return submission_dict



class SubmissionCreate(BaseHandler):
    """
    This class create the submission, receiving a partial wbSubmissionDesc, and
    returning a submission_id, usable in update operation.
    """

    @transport_security_check('wb')
    @unauthenticated
    @inlineCallbacks
    def post(self, context_id, token):
        """
        Request: wb2SubmissionDesc
        Response: { 'receipt' : $receipt }
        Errors: ContextIdNotFound, InvalidInputFormat, SubmissionFailFields, TokenError

        This is an atomic creation of submission and validation of fields + token received.
        The files associated with the same token are aggregated later.
        """
        request = self.validate_message(self.request.body, requests.wb2SubmissionDesc)

        # TODO temporary hack: I've to take ContextCache and give it to the fields validation
        # putting the field validation outside the @transact function
        # but is better await because the Fields in currently in refactor, so, *hack now think later*
        request.update({'context' : context_id })

        status = yield create_submission(request, finalize='ignored, hardcoded True')
        # Note: at the moment status is containing a serialization of the wb_itip,
        # and is not useful itself: only the receipt matter here (but, in unitTest
        # having echoed back what we ask for, is a good thing). so... I'm gonna
        # to delete status here, but not deleting the code because we've to think about.
        status = {}

        receipt = yield create_whistleblower_tip(status)
        status.update({'receipt': receipt})

        self.set_status(201) # Created
        self.finish(status)


