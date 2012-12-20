# -*- coding: UTF-8
#
#   models/submission
#   *****************
#
# Storm DB table and ORM of the submisson temporary table


from storm.twisted.transact import transact
from storm.locals import Int, Pickle, DateTime, Unicode, Reference
from storm.exceptions import NotOneError

from globaleaks.utils import idops, gltime, random
from globaleaks.models.base import TXModel
from globaleaks.models.externaltip import File, Folder, WhistleblowerTip
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.context import Context
from globaleaks.rest.errors import ContextGusNotFound, SubmissionFailFields, SubmissionGusNotFound
from globaleaks.models.receiver import Receiver

from globaleaks.utils import log

__all__ = ['Submission']


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

    receipt = Unicode()
    receivers = Pickle()

    # XXX remove Folder, use File
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
            raise ContextGusNotFound
        if associated_c is None:
            raise ContextGusNotFound

        submission = Submission()
        submission.submission_gus = idops.random_submission_gus(False)

        submission.context_gus = context_gus
        submission.context = associated_c

        submission.receivers = associated_c.get_receivers('public')
        submission.receivers = associated_c.receivers
        # XXX this was important and actually IS bugged -- review that /me vecna

        # TODO submission.context.update_stats()

        submission.creation_time = gltime.utcDateNow()
        submission.expiration_time = gltime.utcFutureDate(seconds=1, minutes=1, hours=1)

        store.add(submission)

        submissionDesc = submission._description_dict()
        log.debug("[D] submission created", submission._description_dict())

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
            raise SubmissionGusNotFound

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

        log.debug("Added file %s to %s" % (submission_gus, file_name))

        store.add(new_file)

        return new_file_gus

    @transact
    def update_fields(self, submission_gus, fields):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "update_fields", "submission_gus", submission_gus, "fields", fields )

        store = self.getStore('update_fields')
        try:
            s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError, e:
            raise SubmissionGusNotFound
        if not s:
            raise SubmissionGusNotFound

        # Fields are specified in adminContextDesc with 'fields'
        #
        s.fields = fields

    @transact
    def select_receiver(self, submission_gus, receivers):

        store = self.getStore('select_receiver')

        try:
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        # TODO checks that all the receiver declared in receivers EXISTS!!
        requested_s.receivers = receivers

    @transact
    def status(self, submission_gus):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "status", "submission_gus", submission_gus )

        store = self.getStore('status')

        try:
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            # its not possible: is a primary key
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        statusDict = requested_s._description_dict()

        # strip internal/incomplete/reserved information
        statusDict.pop('folder_gus')

        return statusDict

    # not a transact, need to check self.context and evaluate receipt strength
    # would be solved in security by: https://github.com/globaleaks/GLBackend/issues/33
    def _receipt_evaluation(self, receipt_proposal=None):

        if not receipt_proposal:
            return random.random_string(10, 'A-Z,0,9')

        temp_stuff = "%s_%s" % (receipt_proposal, random.random_string(5, 'A-Z,0-9') )
        return temp_stuff

    @transact
    def receipt_proposal(self, submission_gus, proposed_receipt):

        store = self.getStore('receipt_proposal')

        try:
            # XXX need to be checked the presence of a collision, but this bring to insecurity
            # so ... at the moment this issue is not solved.
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        requested_s.receipt = unicode(self._receipt_evaluation(proposed_receipt))

    @transact
    def complete_submission(self, submission_gus):
        """
        Need to be refactored in Tip the Folder thing
        """
        log.debug("[D] ",__file__, __name__, "Submission complete_submission", submission_gus)

        store = self.getStore('complete_submission')

        try:
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        log.debug("Creating internal tip in", requested_s.context_gus, requested_s.submission_gus)

        if not requested_s.fields:
            raise SubmissionFailFields

        internal_tip = InternalTip()

        # Initialize all the Storm fields inherit by Submission and Context
        internal_tip.initialize(requested_s)

        # here is created the table with receiver selected (an information stored only in the submission)
        # and the threshold escalation. Is not possible have a both threshold and receiver
        # selection in this moment (other complications can derived from use them both)
        for single_r in requested_s.receivers:

            # this is an hack that need to be fixed short as possible.
            # receiver_map is an outdated concept
            if type(single_r) == type({}):
                receiver_gus = single_r.get('receiver_gus')
            else:
                receiver_gus = single_r

            selected_r = store.find(Receiver, Receiver.receiver_gus == receiver_gus).one()
            internal_tip.associate_receiver(selected_r)

        store.add(internal_tip)

        log.debug("Created internal tip %s" % internal_tip.context_gus)

        # this is wrong, we need to check if some file has been added TODO
        # temporary fail in this check, folder would be associated in internaltip, but
        # marked coherently with the asynchronous delivery logic
        if requested_s.folder and 1 == 0:
            log.debug("Creating submission folder table %s" % requested_s.folder_gus)
            folder = requested_s.folder
            folder.internaltip = internal_tip

            store.add(folder) 

            log.debug("Submission folder created without error")

            # XXX, and I don't get why folder_gus is returned by new():
            # because file uploader # use submission_gus as reference, do not need folder_gus too.
            # because if someone want restore an upload, use the file_gus instead of folder_gus

        log.debug("Creating tip for whistleblower")
        whistleblower_tip = WhistleblowerTip()
        whistleblower_tip.internaltip_id = internal_tip.id
        whistleblower_tip.internaltip = internal_tip

        if not requested_s.receipt:
            requested_s.receipt = requested_s._receipt_evaluation()

        statusDict = requested_s._description_dict()

        # remind: receipt is the UNICODE PRIMARY KEY of WhistleblowerTip
        whistleblower_tip.receipt = unicode(requested_s.receipt)
        # TODO whistleblower_tip.authoptions would be filled here

        store.add(whistleblower_tip)
        log.debug("Created tip with address %s" % whistleblower_tip.receipt)

        log.debug("created_InternalTip", internal_tip.id," and WhistleBlowerTip, removed submission")

        store.remove(requested_s)

        return statusDict

    @transact
    def submission_delete(self, submission_gus):

        log.debug("[D] ",__file__, __name__, "Submission delete by user request", submission_gus)

        store = self.getStore('submission_delete')

        try:
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        store.remove(requested_s)

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
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        retSubmission = requested_s._description_dict()

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
            'receivers' : self.receivers,
            'file_gus_list' : self.folder_gus,
            'receipt' : self.receipt
        }

        return descriptionDict
