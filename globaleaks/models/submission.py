# -*- coding: UTF-8)
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

        store = self.getStore()

        try:
            associated_c = store.find(Context, Context.context_gus == unicode(context_gus)).one()
        except NotOneError:
            raise ContextGusNotFound
        if associated_c is None:
            raise ContextGusNotFound

        submission = Submission()
        submission.submission_gus = idops.random_submission_gus(False)

        submission.context_gus = context_gus
        submission.context = associated_c

        # TODO move that in handler, an use update_receivers
        # receivers is a list of receiver_gus
        if associated_c.selectable_receiver:
            submission.receivers = []
        else:
            submission.receivers = associated_c.receivers

        submission.files = {}

        # TODO submission.context.update_stats()

        submission.creation_time = gltime.utcDateNow()
        submission.expiration_time = gltime.utcFutureDate(seconds=1, minutes=1, hours=1)

        store.add(submission)

        submissionDesc = submission._description_dict()
        log.debug("[D] submission created", submission._description_dict())

        # return a more complex data, with context and submission,
        # TODO implement update and new with the new recurring pattern
        return submissionDesc

    # TODO move this element in file
    @transact
    def add_file(self, submission_gus, file_name, content_type, file_size):

        store = self.getStore()

        try:
            submission_r = store.find(Submission, Submission.submission_gus == unicode(submission_gus)).one()
        except NotOneError:
            store.close()
            raise SubmissionGusNotFound
        if not submission_r:
            store.close()
            raise SubmissionGusNotFound

        new_file = File()
        new_file.file_gus = ret_file_gus = unicode(idops.random_file_gus())
        new_file.name = file_name
        new_file.content_type = content_type
        new_file.size = file_size

        submission_r.files.update({ new_file.file_gus : file_name })

        log.debug("Added file %s in submission %s with name %s" % (ret_file_gus, submission_gus, file_name))

        store.add(new_file)

        return ret_file_gus

    @transact
    def update_fields(self, submission_gus, fields):

        store = self.getStore()
        try:
            s = store.find(Submission, Submission.submission_gus == unicode(submission_gus)).one()
        except NotOneError, e:
            raise SubmissionGusNotFound
        if not s:
            raise SubmissionGusNotFound

        # TODO
        # Fields are specified in adminContextDesc with 'fields'
        # and need to be checked using the contexts.fields key
        # only the requested key are searched in the fields.
        # all the other keys are ignored.
        # all the keys need to be validated based on the type
        # TODO
        s.fields = fields

    @transact
    def select_receiver(self, submission_gus, receivers):

        store = self.getStore()

        try:
            requested_s = store.find(Submission, Submission.submission_gus == unicode(submission_gus)).one()
        except NotOneError:
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        # TODO this check need to be done in handler, perhaps with other 'requirements'
        # check
        if requested_s.context.selectable_receiver:
            # TODO checks that all the receiver declared in receivers EXISTS!!
            # (or raise ReceiverGusNotFound)
            requested_s.receivers = receivers
        else:
            print "Receiver selection choosen in a Context that do not supports this option"
            print requested_s.receivers, "=", requested_s.context.receivers

        # If the setting is not acceptable,
        # the request is silently ignored, and the receiver corpus returned
        # by the API is the same unchanged.

    @transact
    def status(self, submission_gus):

        store = self.getStore()

        try:
            requested_s = store.find(Submission, Submission.submission_gus == unicode(submission_gus)).one()
        except NotOneError:
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        statusDict = requested_s._description_dict()

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
            requested_s = store.find(Submission, Submission.submission_gus == unicode(submission_gus)).one()
        except NotOneError:
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        requested_s.receipt = unicode(self._receipt_evaluation(proposed_receipt))


    @transact
    def complete_submission(self, submission_gus):
        """
        need a best-safe receipt feat
        """

        store = self.getStore()

        try:
            requested_s = store.find(Submission, Submission.submission_gus == unicode(submission_gus)).one()
        except NotOneError:
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        # XXX log
        log.debug("Creating internal tip in", requested_s.context_gus,
            "from", requested_s.submission_gus, "with", requested_s.files)

        if not requested_s.fields:
            raise SubmissionFailFields

        internal_tip = InternalTip()

        # Initialize all the Storm fields inherit by Submission and Context
        internal_tip.initialize(requested_s)

        # The list of receiver (receiver_gus) has been already evaluated by submission
        # initialization or update_receivers function. need just to be copied in
        # InternalTip.
        for single_r in requested_s.receivers:
            # TODO XXX Applicative log
            print "++ I'm putting in internaltip ", single_r, "from", requested_s.receivers, "to:", internal_tip.receivers
            internal_tip.receivers.append(single_r)


        # The list of file need to be processed, and the completed files, need to
        # be put in the processing queue and restore the reference in File
        for single_f in requested_s.files:
            # TODO
            print "TODO XXX, need to be processed", single_f

        whistleblower_tip = WhistleblowerTip()
        whistleblower_tip.internaltip_id = internal_tip.id
        whistleblower_tip.internaltip = internal_tip

        if not requested_s.receipt:
            requested_s.receipt = requested_s._receipt_evaluation()

        statusDict = requested_s._description_dict()

        # receipt is the UNICODE PRIMARY KEY of WhistleblowerTip
        whistleblower_tip.receipt = unicode(requested_s.receipt)
        # TODO whistleblower_tip.authoptions would be filled here

        store.add(internal_tip)
        store.add(whistleblower_tip)
        store.remove(requested_s)

        log.debug("Created tip with address %s, Internal Tip and Submission removed" % whistleblower_tip.receipt)

        return statusDict


    @transact
    def submission_delete(self, submission_gus):

        store = self.getStore()

        try:
            requested_s = store.find(Submission, Submission.submission_gus == unicode(submission_gus)).one()
        except NotOneError:
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        store.remove(requested_s)


    @transact
    def get_single(self, submission_gus):

        store = self.getStore()

        try:
            requested_s = store.find(Submission, Submission.submission_gus == unicode(submission_gus)).one()
        except NotOneError:
            raise SubmissionGusNotFound
        if requested_s is None:
            raise SubmissionGusNotFound

        retSubmission = requested_s._description_dict()

        return retSubmission


    @transact
    def get_all(self):

        store = self.getStore()

        # I didn't understand why, but NotOneError is not raised even if the search return None
        present_s = store.find(Submission)

        subList = []
        for s in present_s:
            subList.append(s._description_dict())

        return subList


    # called by a transact method, return
    def _description_dict(self):

        descriptionDict = {
            'submission_gus': unicode(self.submission_gus),
            'fields' : dict(self.fields) if self.fields else {},
            'context_gus' : unicode(self.context_gus),
            'creation_time' : unicode(gltime.prettyDateTime(self.creation_time)),
            'expiration_time' : unicode(gltime.prettyDateTime(self.expiration_time)),
            'receivers' : list(self.receivers) if self.receivers else [],
            'files' : dict(self.files) if self.files else {},
            'receipt' : unicode(self.receipt)
        }

        return dict(descriptionDict)
