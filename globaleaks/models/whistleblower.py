from storm.twisted.transact import transact
from storm.locals import *

from globaleaks.models.base import TXModel
from globaleaks.models.tip import Folder

__all__ = ['Submission', 'PublicStats' ]

"""
This ORM implementation is called whistleblower, because contain the information mostly useful
for the WBs, other elements used by WBs stay on globaleaks.db.tips.SpecialTip
"""

class Submission(TXModel):
    """
    This represents a temporary submission. Submissions should be stored here
    until they are transformed into a Tip.
    """
    __storm_table__ = 'submission'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, submission_gus VARCHAR, fields VARCHAR, "\
                   " opening_date DATETIME, receivers VARCHAR, folder_id INTEGER)"

    id = Int(primary=True)
    submission_gus = Unicode()
    fields = Pickle()
    receivers = Pickle()
    opening_date = Date()

    folder_id = Int()
    folder = Reference(folder_id, Folder.id)

    """
    The following methos has not been reviewed after the refactor
    """
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
        s = store.find(Submission, Submission.submission_id==submission_id).one()

        if not s:
            raise Exception("Did not find a submission with that ID")

        internal_tip = InternalTip()
        internal_tip.fields = s.fields
        store.add(internal_tip)

        whistleblower_tip = Tip()
        whistleblower_tip.internal_tip_id = internal_tip.id
        whistleblower_tip.address = receipt
        store.add(whistleblower_tip)

        # XXX lookup the list of receivers and create their tips too.
        for receiver in s.receivers:
            #print receiver
            pass

        # Delete the temporary submission
        store.remove(s)

        store.commit()
        store.close()

class PublicStats(TXModel):
    """
    * Follow the same logic of admin.AdminStats,
    * need to be organized along with the information that we want to shared to the WBs:
       *  active_submission represent the amount of submission active in the moment
       *  node activities is a sum of admin + receiver operation
    * that's all time dependent information
       * remind: maybe also non-time dependent information would exists, if a node want to publish also their own analyzed submission, (but this would require another db table)
    """
    __storm_table__ = 'publicstats'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, active_submissions INT, node_activities INT, uptime INT"

    id = Int(primary=True)

    active_submissions = Int()
    node_activities = Int()
    uptime = Int()
    """
    likely would be expanded, but avoiding to spread information that may lead an attacker advantaged
    """

