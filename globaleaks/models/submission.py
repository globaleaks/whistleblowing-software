# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

from storm.twisted.transact import transact
from storm.locals import Int, Pickle, DateTime, Unicode, Reference
from storm.exceptions import NotOneError

from globaleaks.utils import idops, gltime, random
from globaleaks.models.base import TXModel, ModelError
from globaleaks.models.externaltip import File, Folder, WhistleblowerTip
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.context import Context, InvalidContext
from globaleaks.models.receiver import Receiver

from globaleaks.utils import log

__all__ = ['Submission']

class SubmissionNotFoundError(ModelError):

    def __init__(self):
        ModelError.error_message = "Invalid Submission addressed with submission_gus"
        ModelError.error_code = 1 # need to be resumed the table and come back in use them
        ModelError.http_status = 400 # Bad Request

# may it exists ? I've used that for wrap eventually "database is locked", but
# we've see that database locked is an effect of a programmer bug, not a
# common behavior, also in multiple requests
class SubmissionGenericError(ModelError):

    def __init__(self):
        ModelError.error_message = " Submission internal error: sorry!"
        ModelError.error_code = 1 # need to be resumed the table and come back in use them
        ModelError.http_status = 500 # Server Error


# TODO - would be an error when we start to check presence of required fields
class SubmissionFailRequiremers(ModelError):
    pass

class Submission(TXModel):
    """
    This represents a temporary submission. Submissions should be stored here
    until they are transformed into a Tip.
    """
    log.debug("[D] %s %s " % (__file__, __name__), "Class Submission")
    __storm_table__ = 'submission'

    submission_gus = Unicode(primary=True)

    fields = Pickle()
    creation_time = DateTime()
    expiration_time = DateTime()

    receivers_gus_list = Pickle()

    folder_gus = Unicode()
    folder = Reference(folder_gus, Folder.folder_gus)

    context_gus = Unicode()
    context = Reference(context_gus, Context.context_gus)

    @transact
    def new(self, context_gus):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "new in %s", context_gus)
        store = self.getStore('new submission')

        try:
            associated_c = store.find(Context, Context.context_gus == context_gus).one()
        except NotOneError:
            store.close()
            raise InvalidContext
        if associated_c is None:
            store.close()
            raise InvalidContext

        submission = Submission()
        submission.submission_gus = idops.random_submission_gus(False)

        submission.context_gus = context_gus
        submission.context = associated_c

        submission.receivers_gus_list = associated_c.get_receivers('public')
        # TODO submission.context.update_stats()

        submission.creation_time = gltime.utcDateNow()
        submission.expiration_time = gltime.utcFutureDate(seconds=1, minutes=1, hours=1)

        store.add(submission)
        store.commit()

        submissionDesc = submission._description_dict()
        log.debug("[D] submission created", submission._description_dict())
        submissionDesc.pop('folder_gus')

        store.close()

        return submissionDesc

    # XXX ---
    # need to be refactored with delivery schedule ops
    # XXX ---
    @transact
    def add_file(self, submission_gus, file_name=None):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "add_file", "submission_gus", submission_gus , "file_name", file_name )
        store = self.getStore('add_file')
        submission = store.find(Submission, Submission.submission_gus==submission_gus).one()

        if not submission:
            store.rollback()
            store.close()
            raise SubmissionNotFoundError

        """
        this part of code was in new(), now having a Folder is not mandatory in a submission,
        Folder need a Storm obj + skeleton providing InputFilter and Delivery supports.

        folder = Folder()
        folder.folder_gus = idops.random_folder_gus()
        store.add(folder)
        submission.folder = folder
        """


        new_file_gus = idops.random_file_gus()
        log.debug("Generated this file id %s" % new_file_gus)
        new_file = File()

        new_file.folder_gus = submission.folder_gus
        new_file.file_gus = unicode(new_file_gus)
        store.add(new_file)

        try:
            store.commit()
        except Exception, e:
            log.exception("[E]: %s %s " % (__file__, __name__), "Submission", "add_file", "submission_gus", submission_gus, "file_name", file_name )
            store.rollback()
            store.close()
            raise SubmissionGenericError

        log.debug("Added file %s to %s" % (submission_gus, file_name))
        store.close()
        return new_file_gus

    @transact
    def update_fields(self, submission_gus, fields):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "update_fields", "submission_gus", submission_gus, "fields", fields )

        store = self.getStore('update_fields')
        try:
            s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError, e:
            # XXX these log lines will be removed in the near future
            log.err("[E] update_fields: Problem looking up %s" % submission_gus)
            log.err(e)
            store.rollback()
            store.close()
            raise SubmissionNotFoundError

        if not s:
            store.rollback()
            store.close()
            raise SubmissionNotFoundError

        if not s.fields:
            s.fields = {}

        for k, v in fields.items():
            s.fields[k] = v

        try:
            store.commit()
        except Exception, e:
            log.exception("[E]: %s %s " % (__file__, __name__), "Submission", "update_fields", "submission_gus", submission_gus, "fields", fields )
            store.rollback()
            store.close()
            raise SubmissionGenericError

        store.close()

    @transact
    def select_receiver(self, submission_gus, receivers_gus_list):

        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "select_receiver", "submission_gus",\
            submission_gus, "receiver_gus_list", receivers_gus_list, "NOT IMPLEMENTED ATM" )

        store = self.getStore('select_receiver')

        try:
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            # its not possible: is a primary key
            store.close()
            raise SubmissionNotFoundError
        if requested_s is None:
            store.close()
            raise SubmissionNotFoundError

        store.commit()
        store.close()

    @transact
    def status(self, submission_gus):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "status", "submission_gus", submission_gus )

        store = self.getStore('status')

        try:
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            # its not possible: is a primary key
            store.close()
            raise SubmissionNotFoundError
        if requested_s is None:
            store.close()
            raise SubmissionNotFoundError

        statusDict = requested_s._description_dict()

        # strip internal/incomplete/reserved information
        statusDict.pop('folder_gus')

        store.close()
        return statusDict

    @transact
    def complete_submission(self, submission_gus, proposed_receipt):
        """
        Need to be refactored in Tip the Folder thing
        """
        log.debug("[D] ",__file__, __name__, "Submission complete_submission", submission_gus, "proposed_receipt", proposed_receipt)

        store = self.getStore('complete_submission')

        try:
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            store.close()
            raise SubmissionNotFoundError
        if requested_s is None:
            store.close()
            raise SubmissionNotFoundError

        log.debug("Creating internal tip in", requested_s.context_gus, requested_s.submission_gus)

        internal_tip = InternalTip()

        # Initialize all the Storm fields inherit by Submission and Context
        internal_tip.initialize(requested_s)

        # here is created the table with receiver selected (an information stored only in the submission)
        # and the threshold escalation. Is not possible have a both threshold and receiver
        # selection in this moment (other complications can derived from use them both)
        for single_r in requested_s.receivers_gus_list:

            receiver_gus = single_r.get('receiver_gus')
            selected_r = store.find(Receiver, Receiver.receiver_gus == receiver_gus).one()
            internal_tip.associate_receiver(selected_r)

        try:
            store.add(internal_tip)
        except Exception, e:
            log.err(e)
            store.rollback()
            store.close()
            raise SubmissionGenericError

        log.debug("Created internal tip %s" % internal_tip.context_gus)

        # this is wrong, we need to check if some file has been added TODO
        # temporary fail in this check, folder would be associated in internaltip, but
        # marked coherently with the asynchronous delivery logic
        if requested_s.folder and 1 == 0:
            log.debug("Creating submission folder table %s" % requested_s.folder_gus)
            folder = requested_s.folder
            folder.internaltip = internal_tip

            store.add(folder) 
            store.commit()

            log.debug("Submission folder created without error")

            # XXX, and I don't get why folder_gus is returned by new():
            # because file uploader # use submission_gus as reference, do not need folder_gus too.
            # because if someone want restore an upload, use the file_gus instead of folder_gus

        log.debug("Creating tip for whistleblower")
        whistleblower_tip = WhistleblowerTip()
        whistleblower_tip.internaltip_id = internal_tip.id
        # whistleblower_tip.internaltip = internal_tip

        used_receipt = proposed_receipt + '-' + random.random_string(5, 'A-Z,0-9')
        whistleblower_tip.receipt = used_receipt
        # whistleblower_tip.authoptions would be filled here

        store.add(whistleblower_tip)
        log.debug("Created tip with address %s" % whistleblower_tip.receipt)

        log.debug("created_InternalTip", internal_tip.id," and WhistleBlowerTip, removed submission")

        store.remove(requested_s)
        store.commit()
        store.close()

        return used_receipt

    @transact
    def admin_get_single(self, submission_gus):
        """
        @return a receiverDescriptionDict
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class Submission", "admin_get_single", submission_gus)

        store = self.getStore('submission - admin_get_single')

        # I didn't understand why, but NotOneError is not raised even if the search return None
        try:
            requested_s = store.find(Submission, Submission.submission_gus == submission_gus).one()
        except NotOneError:
            store.close()
            raise SubmissionNotFoundError
        if requested_s is None:
            store.close()
            raise SubmissionNotFoundError

        retSubmission = requested_s._description_dict()

        store.close()
        return retSubmission

    @transact
    def admin_get_all(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Submission", "admin_get_all")
        pass


    # called by a transact method, return
    def _description_dict(self):

        descriptionDict = {
            'submission_gus': self.submission_gus,
            'fields' : self.fields,
            'context_gus' : self.context_gus,
            'creation_time' : gltime.prettyDateTime(self.creation_time),
            'expiration_time' : gltime.prettyDateTime(self.expiration_time),
            'receiver_gus_list' : self.receivers_gus_list,
            # folder would be reported as sub-dict if present - XXX
            'folder_gus' : self.folder_gus
        }

        return descriptionDict
