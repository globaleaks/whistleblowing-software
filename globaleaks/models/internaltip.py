# -*- coding: UTF-8
#
#   models/internaltip
#   ******************
#
# There are a Bottom-Up approach with InternalTip being "UP" and
# Folders, Comments, Files, WhistleblowerTip and ReceiverTip (externaltip.py)
# that reference InternalTip
# InternalTip reference classes Context

from storm.twisted.transact import transact

from storm.exceptions import NotOneError
from storm.locals import Int, Pickle, Unicode, DateTime
from storm.locals import Reference

from globaleaks.utils import log, gltime
from globaleaks.models.base import TXModel
from globaleaks.models.context import Context

__all__ = [ 'InternalTip' ]

class InternalTip(TXModel):
    """
    This is the internal representation of a Tip that has been submitted to the
    GlobaLeaks node.

    It has a not associated map for keep track of Receivers, Tips, Folders,
    Comments and WhistleblowerTip.
    All of those element has a Storm Reference with the InternalTip.id, not
    vice-versa
    """

    __storm_table__ = 'internaltips'

    id = Int(primary=True)

    fields = Pickle()
    pertinence_counter = Int()
    creation_date = DateTime()
    expiration_date = DateTime()
    last_activity = DateTime()

    # the LIMITS are stored in InternalTip because and admin may
    # need change them. These values are copied by Context
    escalation_threshold = Int()
    access_limit = Int()
    download_limit = Int()

    mark = Unicode()
        # TODO ENUM: new, first, second

    receivers = Pickle()

    files = Pickle()

    context_gus = Unicode()
    context = Reference(context_gus, Context.context_gus)

    # called by a transact: submission.complete_submission
    def initialize(self, submission):
        """
        initialized an internalTip having the context
        @return: none
        """
        self.last_activity = gltime.utcDateNow()
        self.creation_date = gltime.utcDateNow()

        self.context = submission.context
        self.context_gus = submission.context_gus

        # those four can be referenced thru self.context.
        self.escalation_threshold = submission.context.escalation_threshold
        self.access_limit = submission.context.tip_max_access
        self.download_limit = submission.context.file_max_download

        # TODO XXX review CHECK
        # remind: files has not yet been referenced to InternalTip
        self.files = submission.files
        # need operations in File.internaltip_id File.internaltip
        # TODO XXX review CHECK

        self.expiration_date = submission.expiration_time
        self.fields = submission.fields
        self.pertinence_counter = 0
        self.mark = u'new'

        # receivers list it's copied in submission.complete_submission
        # because can, optionally, having someone added/removed by
        # context rules or so on. Just, it's an operation that is much
        # better keep separated from agnostic submission->tip copy.
        self.receivers = []

    @transact
    def change_inner_value(self, id, escalation=None, accesslimit=None, downloadlimit=None):
        """
        @param id: Target InternalTip
        @param escalation: new level of escalation threshold
        @param accesslimit: new amount of access limit
        @param downloadlimit: now amount of download limit
        @return: None
        """
        store = self.getStore()

        selected_it = store.find(InternalTip, InternalTip.id == id).one()

        if escalation:
            selected_it.escalation_threshold = escalation

        if accesslimit:
            selected_it.access_limit = accesslimit

        if downloadlimit:
            selected_it.download_limit = downloadlimit


    # perhaps get_newly_generated and get_newly_escalated can be melted, and in task queue
    @transact
    def get_newly_generated(self):
        """
        @return: all the internaltips with mark == u'new', in a list of id
        """
        store = self.getStore()

        new_itips = store.find(InternalTip, InternalTip.mark == u'new')

        retVal = []
        for single_itip in new_itips:
            retVal.append(single_itip.id)

        return retVal

    @transact
    def get_newly_escalated(self):
        """
        @return: all the internaltips with
            pertinence_counter >= escalation_threshold and mark == u'first',
            in a list of id
        """
        store = self.getStore()

        escalated_itips = store.find(InternalTip, (InternalTip.mark == u'first' and InternalTip.pertinence_counter >= InternalTip.escalation_threshold ))

        retVal = []
        for single_itip in escalated_itips:
            retVal.append(single_itip.id)

        return retVal

    @transact
    def flip_mark(self, subject_id, newmark):
        """
        @param newmark: u'first' or u'second', at the start is u'new'
        @subject_id: InternalTip.id to be changed, this mark represent the progress of the iTip
        @return: None
        """
        store = self.getStore()

        requested_t = store.find(InternalTip, InternalTip.id == subject_id).one()

        # XXX log message
        log.debug("flip mark in InternalTip %d, from [%s] to [%s]" % (requested_t.id, requested_t.mark, newmark))

        requested_t.last_activity = gltime.utcDateNow()
        requested_t.mark = newmark


    # not a transact, because called by the ReceiverTip.pertinence_vote
    def pertinence_update(self, vote):
        """
        @vote: a boolean that express if the Tip is pertinent or not
        @return: the pertinence counter
        """

        if vote:
            self.pertinence_counter += 1
        else:
            self.pertinence_counter -= 1

        self.last_activity = gltime.utcDateNow()
        return self.pertinence_counter


    # not transact, called by ReceiverTip.personal_delete
    def receiver_align(self):
        """
        When a ReceiverTip is removed, the map is updated
        @return: None, a receiver has choose to remove self from the Tip,
        notify with a system message the others
        """
        pass


    @transact
    def tip_delete(self, internaltip_id):
        """
        function called when a receiver choose to remove a submission
        and all the derived tips. is called by scheduler when
        timeoftheday is >= expired_date.
        It's called by handler or by scheduled operations.
        * The called handle and manage eventually reference to be deleted. *
        """

        store = self.getStore()
        selected = store.find(InternalTip, InternalTip.id == internaltip_id).one()
        store.remove(selected)


    @transact
    def get_receivers_by_itip(self, internaltip_id):
        """
        @param internaltip_id:
        @return: [ Receivers ] a full descriptive dict

        This function is used from the schedule operations, and return the
        most updated data available about Receiver's notification and delivery
        preferences.
        """
        from globaleaks.models.externaltip import ReceiverTip

        store = self.getStore()

        rcvr_tips = store.find(ReceiverTip, ReceiverTip.internaltip_id == internaltip_id)

        receivers_desc = []
        for tip in rcvr_tips:
            receivers_desc.append(tip.receiver._description_dict())

        return receivers_desc


    @transact
    def get_all(self):

        store = self.getStore()
        all_itips = store.find(InternalTip)

        retVal = []
        for itip in all_itips:
            retVal.append(itip._description_dict() )

        return retVal


    def _description_dict(self):

        description_dict = {
            'internaltip_id' : self.id,
            'context_name' : self.context.name,
            'context_gus': self.context_gus,
            'creation_date' : gltime.prettyDateTime(self.creation_date),
            'expiration_date' : gltime.prettyDateTime(self.creation_date),
            'fields' : dict(self.fields),
            'download_limit' : self.download_limit,
            'access_limit' : self.access_limit,
            'mark' : self.mark,
            'pertinence' : self.pertinence_counter,
            'escalation_threshold' : self.escalation_threshold,
            'files' : dict(self.files) if self.files else {},
            'receiver_map' : list(self.receivers) if self.receivers else []
        }
        return dict(description_dict)

