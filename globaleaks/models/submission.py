from twisted.internet.defer import returnValue
from storm.twisted.transact import transact
from storm.locals import *

from globaleaks.utils import idops, gltime
from globaleaks.models.base import TXModel
from globaleaks.models.tip import Folder, InternalTip, Tip

__all__ = ['Submission']

"""
This ORM implementation is called whistleblower, because contain the information mostly useful
for the WBs, other elements used by WBs stay on globaleaks.db.tips.SpecialTip
"""

class SubmissionError(Exception):
    pass

class Submission(TXModel):
    """
    This represents a temporary submission. Submissions should be stored here
    until they are transformed into a Tip.
    """
    __storm_table__ = 'submission'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, submission_id VARCHAR, fields VARCHAR, "\
                   " creation_time DATETIME, receivers VARCHAR, folder_id INTEGER)"
    id = Int(primary=True)
    submission_id = Unicode() # Int()
    folder_id = Int()
    fields = Pickle()
    receivers = Pickle()
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
            s.fields = []

        for field in fields:
            s.fields.append(field)


        store.commit()
        store.close()


    @transact
    def select_receiver(self, submission_id, receiver):
        store = self.getStore()
        s = store.find(Submission, Submission.submission_id==submission_id).one()
        s.reciever_selected = receiver
        store.commit()
        store.close()

    @transact
    def status(self, submission_id):
        store = self.getStore()
        s = store.find(Submission, Submission.submission_id==submission_id).one()

        status = {'receivers_selected': s.receivers,
                  'fields': s.fields}

        store.commit()
        store.close()
        return status

    @transact
    def create_tips(self, submission_id, receipt):
        store = self.getStore()
        try:
            s = store.find(Submission,
                Submission.submission_id==submission_id).one()
        except Exception, e:
            store.commit()
            store.close()
            raise Exception("Collision detected! HELP THE WORLD WILL END!")

        if not s:
            raise Exception("Did not find a submission with that ID")

        internal_tip = InternalTip()
        internal_tip.fields = s.fields
        store.add(internal_tip)

        whistleblower_tip = Tip()
        whistleblower_tip.internal_tip_id = internal_tip.id
        whistleblower_tip.address = receipt
        store.add(whistleblower_tip)

        if not s.receivers:
            raise SubmissionError("No receivers selected")

        # XXX lookup the list of receivers and create their tips too.
        for receiver in s.receivers:
            #print receiver
            pass

        # Delete the temporary submission
        store.remove(s)

        store.commit()
        store.close()


