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
    log.debug("[D] %s %s " % (__file__, __name__), "InternalTip", "TXModel", TXModel)
    __storm_table__ = 'internaltips'

    id = Int(primary=True)

    fields = Pickle()
    pertinence_counter = Int()
    escalation_threshold = Int()
    creation_date = DateTime()
    expiration_date = DateTime()
    last_activity = DateTime()

    # the LIMITS are defined and declared *here*, and track in
    # ReceiverTip (access) and Folders (download, if delivery supports).
    # *Here*, because the values are copied by Context.* but Admin can modify them,
    # if needed.
    access_limit = Int()
    download_limit = Int()

    mark = Unicode()
        # TODO ENUM: new, first, second

    receivers_map = Pickle()

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
        self.context_gus = submission.context.context_gus
        self.escalation_threshold = submission.context.escalation_threshold
        self.access_limit = submission.context.tip_max_access
        self.download_limit = submission.context.file_max_download

        # remind: files has not yet been referenced to InternalTip
        self.files = submission.files
        # need operations in File.internaltip_id File.internaltip

        self.expiration_date = submission.expiration_time
        self.fields = submission.fields
        self.pertinence_counter = 0
        self.receivers_map = []
        self.mark = u'new'

    # called by a transact: submission.complete_submission,
    def associate_receiver(self, chosen_r):
        """
        The existence of this function is important!
        Also if apparently the data may seem redounded. The selected
        receivers CAN BE A SUB-GROUP of the context, therefore only when
        submission is still available we had those information selected that information
        is available.
        Here this information is stored, with the tip_gus that would be None or a valid Tip.
        """

        self.receivers_map.append({
            'receiver_gus' : chosen_r.receiver_gus,
            'receiver_level' : chosen_r.receiver_level,
            'tip_gus' : None,
            'notification_selected' : chosen_r.notification_selected,
            'notification_fields' : chosen_r.notification_fields  })

        log.debug("associate_receiver, called by complete_submission", self.receivers_map)


    @transact
    def tiplist_related(self, id, tip_gus):
        """
        @param tip_gus: get a list of all the the tip_gus for the receiver authorized with a valid tip_gus,
            tip_gus is
        @return: the simpler index, used as tip list
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class InternalTip", "tiplist_related", tip_gus)

        def map_search(map, know_tip, know_receiver):
            """
            when is know the receiver:
                check both is the receiver is included (they should be personally selected)
                check it the threshold escalation has been triggered and tip_gus generated
            when is know the tip:
                return the receiver_gus related
            """
            for receiver_mapped in map:

                tested_receiver = receiver_mapped.get('receiver_gus')
                tested_tip = receiver_mapped.get('tip_gus')

                if know_receiver:
                    if tested_receiver == know_receiver and tested_tip is not None:
                        return tested_tip

                if know_tip:
                    if tested_tip is not None and know_tip == tested_tip:
                        return tested_receiver

            return None

        store = self.getStore('tiplist_related')

        try:
            requested_t = store.find(InternalTip, InternalTip.id == id).one()
        except NotOneError, e:
            store.close()
            raise Exception("Programmer Error: use ReceiverTip.exists")
        if not requested_t:
            store.close()
            raise Exception("Programmer Error: use ReceiverTip.exists")

        receiver_gus = map_search(requested_t.receivers_map, tip_gus, None)

        ret_gus_list = []

        # get all the InternalTips, we can't make query inside a list
        itiplist = store.find(InternalTip)

        for itip in itiplist:

            found_tip_gus = map_search(itip.receivers_map, None, receiver_gus)
            if found_tip_gus:
                ret_gus_list.append(found_tip_gus)

        store.close()
        return ret_gus_list

    @transact
    def get_notification_list(self, id):
        """
        @param id: InternalTip id to be queried
        @return: a list of list [ 'notification_selected', 'notification_field'] [...],
            called by scheduler operation (notification_sched.py)
        """
        store = self.getStore('get_notification_list')

        selected_it = store.find(InternalTip, InternalTip.id == id).one()

        retVal = []
        for single_receiver in selected_it.receivers_map:
            if single_receiver['tip_gus'] != None:
                retVal.append([ single_receiver['notification_selected'], single_receiver['notification_fields'] ])

        store.close()
        return retVal

    # perhaps get_newly_generated and get_newly_escalated can be melted, and in task queue
    @transact
    def get_newly_generated(self):
        """
        @return: all the internaltips with mark == u'new', in a list of id
        """
        store = self.getStore('get_newly_generated')

        new_itips = store.find(InternalTip, InternalTip.mark == u'new')

        retVal = []
        for single_itip in new_itips:
            retVal.append(single_itip.id)

        store.close()
        return retVal

    @transact
    def get_newly_escalated(self):
        """
        @return: all the internaltips with
            pertinence_counter >= escalation_threshold and mark == u'first',
            in a list of id
        """
        store = self.getStore('get_newly_escalated')

        escalated_itips = store.find(InternalTip, (InternalTip.mark == u'first' and InternalTip.pertinence_counter >= InternalTip.escalation_threshold ))

        retVal = []
        for single_itip in escalated_itips:
            retVal.append(single_itip.id)

        store.close()
        return retVal

    @transact
    def flip_mark(self, subject_id, newmark):
        """
        @param newmark: u'first' or u'second', at the start is u'new'
        @subject_id: InternalTip.id to be changed, this mark represent the progress of the iTip
        @return: None
        """
        store = self.getStore('flip mark')

        requested_t = store.find(InternalTip, InternalTip.id == subject_id).one()
        log.debug("flip mark in InternalTip %d, from [%s] to [%s]" % (requested_t.id, requested_t.mark, newmark))
        requested_t.mark = newmark

        store.commit()
        store.close()


    @transact
    def admin_get_all(self):

        log.debug("[D] %s %s " % (__file__, __name__), "InternalTip admin_print_all")

        store = self.getStore('admin_print_all')
        all_itips = store.find(InternalTip)

        retVal = []
        for itip in all_itips:
            retVal.append(itip._description_dict() )

        store.close()
        return retVal

    # not a transact, because called by the ReceiverTip.pertinence_vote
    def pertinence_update(self, vote):
        """
        @vote: a boolean that express if the Tip is pertinent or not
        @return: the pertinence counter
        """
        log.debug("[D] %s %s " % (__file__, __name__), "InternalTip", "pertinence_update:", self.pertinence_counter, vote)

        if vote:
            self.pertinence_counter += 1
        else:
            self.pertinence_counter -= 1

        # TODO last update time
        return self.pertinence_counter

    # not transact, called by ReceiverTip.personal_delete
    def receiver_remove(self):
        """
        @return: None, a receiver has choose to remove self from the Tip, notify with a system message the others
        """
        pass

    @transact
    def postpone_expiration(self):
        """
        function called when a receiver has this option
        """
        log.debug("[D] %s %s " % (__file__, __name__), "InternalTip", "postpone_expiration")


    @transact
    def get_receivers_map(self, internaltip_id):

        log.debug("[D] %s %s " % (__file__, __name__), "InternalTip admin_print_all")

        store = self.getStore('internaltip - get_receivers')
        refitip = store.find(InternalTip, InternalTip.id == internaltip_id).one()

        retVal = refitip.receivers_map

        store.close()
        return retVal

    @transact
    def tip_total_delete(self):
        """
        function called when a receiver choose to remove a submission
        and all the derived tips. is called by scheduler when
        timeoftheday is >= expired_date, or is called by ReceiverTip.total_delete
        """
        log.debug("[D] %s %s " % (__file__, __name__), "InternalTip", "tip_total_delete")

    def _description_dict(self):

        description_dict = {
            'internaltip_id' : self.id, # running in debug!
            'context_name' : self.context.name,
            'context_gus': self.context_gus,
            'creation_date' : gltime.prettyDateTime(self.creation_date),
            'expiration_date' : gltime.prettyDateTime(self.creation_date),
            'fields' : self.fields,
            'download_limit' : self.download_limit,
            'access_limit' : self.access_limit,
            'mark' : self.mark,
            'pertinence' : self.pertinence_counter,
            'escalation_threshold' : self.escalation_threshold,
            'files' : self.files if self.files else {},
            'receiver_map' : self.receivers_map # it's already a dict
        }
        return description_dict

    # perhaps need to be a @transact method called by handlers
    def _receivers_description(self):
        pass

