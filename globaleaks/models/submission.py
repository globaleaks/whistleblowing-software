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
from globaleaks.models.externaltip import File, WhistleblowerTip
from globaleaks.models.internaltip import InternalTip
from globaleaks.models.context import Context
from globaleaks.rest.errors import ContextGusNotFound, SubmissionFailFields, SubmissionGusNotFound, ReceiverGusNotFound
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

    files = Pickle()

    context_gus = Unicode()
    context = Reference(context_gus, Context.context_gus)

    @transact
    def new(self, context_gus):

        store = self.getStore('new submission')

        try:
            associated_c = store.find(Context, Context.context_gus == context_gus).one()
        except NotOneError:
            store.close()
            raise ContextGusNotFound
        if associated_c is None:
            store.close()
            raise ContextGusNotFound

        submission = Submission()
        submission.submission_gus = idops.random_submission_gus(False)

        submission.context_gus = context_gus
        submission.context = associated_c

        # XXX this was important and actually IS bugged -- review that /me vecna
        # submission.receivers = associated_c.get_receivers('public')
        submission.receivers = associated_c.receivers
        # XXX this was important and actually IS bugged -- review that /me vecna

        submission.files = {}

        # TODO submission.context.update_stats()

        submission.creation_time = gltime.utcDateNow()
        submission.expiration_time = gltime.utcFutureDate(seconds=1, minutes=1, hours=1)

        store.add(submission)
        store.commit()

        submissionDesc = submission._description_dict()
        log.debug("[D] submission created", submission._description_dict())

        store.close()

        return submissionDesc

    @transact
    def add_file(self, submission_gus, file_name):

        store = self.getStore('add_file')

        try:
            submission_r = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            store.close()
            raise SubmissionGusNotFound
        if not submission_r:
            store.close()
            raise SubmissionGusNotFound

        new_file = File()
        new_file.file_gus = ret_file_gus = unicode(idops.random_file_gus())
        new_file.name = file_name

        submission_r.files.update({ new_file.file_gus : file_name })

        log.debug("Added file %s in submission %s with name %s" % (ret_file_gus, submission_gus, file_name))

        store.add(new_file)
        store.commit()
        store.close()

        return ret_file_gus

    @transact
    def update_fields(self, submission_gus, fields):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "update_fields", "submission_gus", submission_gus, "fields", fields )

        store = self.getStore('update_fields')
        try:
            s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError, e:
            store.close()
            raise SubmissionGusNotFound
        if not s:
            store.close()
            raise SubmissionGusNotFound

        # Fields are specified in adminContextDesc with 'fields'
        # and need to be checked using the contexts.fields key
        # only the requested key are searched in the fields.
        # all the other keys are ignored.
        # all the keys need to be validated based on the type

        s.fields = fields

        store.commit()
        store.close()

    @transact
    def select_receiver(self, submission_gus, receivers):

        store = self.getStore('select_receiver')

        try:
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            store.close()
            raise SubmissionGusNotFound
        if requested_s is None:
            store.close()
            raise SubmissionGusNotFound

        # TODO checks that all the receiver declared in receivers EXISTS!!
        requested_s.receivers = receivers

        store.commit()
        store.close()

    @transact
    def status(self, submission_gus):
        log.debug("[D] %s %s " % (__file__, __name__), "Submission", "status", "submission_gus", submission_gus )

        store = self.getStore('status')

        try:
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            store.close()
            raise SubmissionGusNotFound
        if requested_s is None:
            store.close()
            raise SubmissionGusNotFound

        statusDict = requested_s._description_dict()

        store.close()
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
            store.close()
            raise SubmissionGusNotFound
        if requested_s is None:
            store.close()
            raise SubmissionGusNotFound

        requested_s.receipt = unicode(self._receipt_evaluation(proposed_receipt))

        store.commit()
        store.close()

    @transact
    def complete_submission(self, submission_gus):
        """
        need a best-safe receipt feat
        """

        store = self.getStore('complete_submission')

        try:
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            store.close()
            raise SubmissionGusNotFound
        if requested_s is None:
            store.close()
            raise SubmissionGusNotFound

        log.debug("Creating internal tip in", requested_s.context_gus,
            "from", requested_s.submission_gus, "with", requested_s.files)

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

            try:
                selected_r = store.find(Receiver, Receiver.receiver_gus == unicode(receiver_gus)).one()
            except NotOneError:
                store.close()
                raise ReceiverGusNotFound
            if not selected_r:
                store.close()
                raise ReceiverGusNotFound

            internal_tip.associate_receiver(selected_r)

        store.add(internal_tip)

        log.debug("Created internal tip %s" % internal_tip.context_gus)

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
        log.debug("Created tip with address %s, Internal Tip and Submission removed" % whistleblower_tip.receipt)

        # store.remove(requested_s)
        store.commit()
        store.close()

        return statusDict

    @transact
    def submission_delete(self, submission_gus):

        log.debug("[D] ",__file__, __name__, "Submission delete by user request", submission_gus)

        store = self.getStore('submission_delete')

        try:
            requested_s = store.find(Submission, Submission.submission_gus==submission_gus).one()
        except NotOneError:
            store.close()
            raise SubmissionGusNotFound
        if requested_s is None:
            store.close()
            raise SubmissionGusNotFound

        store.remove(requested_s)
        store.commit()
        store.close()


    @transact
    def admin_get_single(self, submission_gus):
        """
        @return a receiverDescriptionDict
        """
        store = self.getStore('submission - admin_get_single')

        # I didn't understand why, but NotOneError is not raised even if the search return None
        try:
            requested_s = store.find(Submission, Submission.submission_gus == submission_gus).one()
        except NotOneError:
            store.close()
            raise SubmissionGusNotFound
        if requested_s is None:
            store.close()
            raise SubmissionGusNotFound

        retSubmission = requested_s._description_dict()

        store.close()
        return retSubmission

    @transact
    def admin_get_all(self):
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
            'files' : self.files if self.files else {},
            'receipt' : self.receipt
        }

        return descriptionDict
