# -*- encoding: utf-8 -*-
#
# :authors: Arturo Filastò
# :licence: see LICENSE

from twisted.python import log
from twisted.internet.defer import returnValue, inlineCallbacks
from storm.twisted.transact import transact
from storm.locals import Int, Pickle, Date, Unicode
from storm.exceptions import NotOneError, NoneError

from globaleaks.utils import idops, gltime
from globaleaks.models.base import TXModel, ModelError
from globaleaks.models.tip import Folder, InternalTip, Tip, ReceiverTip
from globaleaks.models.admin import Context

__all__ = ['Submission']

"""
This ORM implementation is called whistleblower, because contain the information mostly useful
for the WBs, other elements used by WBs stay on globaleaks.db.tips.SpecialTip
"""

class SubmissionModelError(ModelError):
    pass

class SubmissionNotFoundError(SubmissionModelError):
    pass

class SubmissionNotOneError(SubmissionModelError):
    pass

class SubmissionNoContextSelectedError(SubmissionModelError):
    pass

class SubmissionContextNotFoundError(SubmissionModelError):
    pass

class SubmissionContextNotOneError(SubmissionModelError):
    pass

class Submission(TXModel):
    """
    This represents a temporary submission. Submissions should be stored here
    until they are transformed into a Tip.
    """
    __storm_table__ = 'submission'

    id = Int(primary=True)
    submission_id = Unicode() # Int()
    folder_id = Int()
    fields = Pickle()

    context_selected = Pickle()

    creation_time = Date()

    @transact
    def new(self):
        store = self.getStore()

        submission_id = idops.random_submission_id(False)
        creation_time = gltime.utcDateNow()
        response = {"submission_id": submission_id,
                    "creation_time": gltime.dateToTime(creation_time)}

        submission = Submission()
        submission.submission_id = submission_id
        submission.folder_id = 0
        submission.creation_time = creation_time

        store.add(submission)
        store.commit()
        store.close()
        return response

    @transact
    def update_fields(self, submission_id, fields):
        store = self.getStore()
        s = store.find(Submission, Submission.submission_id==submission_id).one()

        if not s.fields:
            s.fields = {}

        for k, v in fields.items():
            s.fields[k] = v

        store.commit()
        store.close()


    @transact
    def select_context(self, submission_id, context):
        store = self.getStore()
        try:
            s = store.find(Submission, Submission.submission_id==submission_id).one()
        except NotOneError, e:
            # XXX these log lines will be removed in the near future
            log.msg("Problem looking up %s" % submission_id)
            log.msg(e)
            store.rollback()
            store.close()
            raise SubmissionNotFoundError

        s.context_selected = context
        store.commit()
        store.close()

    # TODO def select_receiver


    @transact
    def status(self, submission_id):
        store = self.getStore()
        status = None
        try:
            s = store.find(Submission, Submission.submission_id==submission_id).one()

        except NotOneError, e:
            store.rollback()
            store.close()
            raise SubmissionNotOneError

        if not s:
            store.rollback()
            store.close()
            raise SubmissionNotFoundError

        status = {'context_selected': s.context_selected,
                  'fields': s.fields}
                # TODO 'creation_time' and 'expiration_time'

        store.commit()
        store.close()
        return status

    @transact
    def create_tips(self, submission_id, receipt):
        store = self.getStore()
        try:
            s = store.find(Submission,
                Submission.submission_id==submission_id).one()
        except NotOneError, e:
            log.msg("Problem creating tips for %s" % submission_id)
            log.msg(e)
            store.rollback()
            store.close()
            # XXX if this happens we probably have to delete one row in the DB
            raise SubmissionModelError("Collision detected! HELP THE WORLD WILL END!")

        if not s:
            store.rollback()
            store.close()
            raise SubmissionNotFoundError

        if not s.context_selected:
            store.rollback()
            store.close()
            raise SubmissionNoContextSelectedError

        try:
            context = store.find(Context,
                    Context.context_id == s.context_selected).one()
        except NotOneError, e:
            store.rollback()
            store.close()
            raise SubmissionContextNotOneError

        if not context:
            store.rollback()
            store.close()
            raise SubmissionContextNotFoundError

        internal_tip = InternalTip()
        internal_tip.fields = s.fields
        internal_tip.context_id = s.context_selected
        store.add(internal_tip)

        whistleblower_tip = Tip()
        whistleblower_tip.internaltip = internal_tip
        whistleblower_tip.address = receipt
        store.add(whistleblower_tip)

        #receiver_tips = context.create_receiver_tips(internal_tip)
        for receiver in context.receivers:
            receiver_tip = ReceiverTip()
            receiver_tip.internaltip = internal_tip
            receiver_tip.new()
            store.add(receiver_tip)

        # Delete the temporary submission
        store.remove(s)

        store.commit()
        store.close()

