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
from storm.locals import Int, Pickle, Unicode, DateTime, Reference
from storm.store import AutoReload

from globaleaks.utils import log, gltime
from globaleaks.models.base import TXModel
from globaleaks.models.context import Context
from globaleaks.rest.errors import InvalidInputFormat

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

    id = Int(primary=True, default=AutoReload)

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

    receivers = Pickle()

    files = Pickle()

    context_gus = Unicode()
    context = Reference(context_gus, Context.context_gus)

    _marker = [ u'new', u'first', u'second' ]

    @transact
    def new(self, submission_dict):
        """
        initialize an internalTip form a recently finalized Submission
        @return: none
        """
        store = self.getStore()

        self.last_activity = gltime.utcDateNow()
        self.creation_date = gltime.utcDateNow()

        # _import_dict do not exists because InternalTip has not update()
        try:
            self.fields = submission_dict['wb_fields']
            self.files = submission_dict['files']
            self.context_gus = submission_dict['context_gus']

            self.receivers = submission_dict['receivers']
            # the receivers arrive from the handler *correctly* checked with
            # context settings, and eventually modified by handler.

        except KeyError, e:
            raise InvalidInputFormat("InternalTip initialization failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("InternalTip initialization failed (wrong %s)" % e)

        # Align the References
        self.context = store.find(Context, Context.context_gus == self.context_gus).one()

        # these value are copied from self.context, and are the only of internaltip
        # that can be changed (by the admin them using update_inner_values() )
        self.escalation_threshold = self.context.escalation_threshold
        self.access_limit = self.context.tip_max_access
        self.download_limit = self.context.file_max_download

        self.expiration_date = gltime.utcFutureDate(hours=(self.context.tip_timetolive * 24))
        # self.expiration_date = gltime.utcFutureDate(self.context.tip_timetolive)
        # TODO issue #36: https://github.com/globaleaks/GLBackend/issues/36

        # Initialization values
        self.pertinence_counter = 0
        self.mark = u'new'

        store.add(self)
        return self._description_dict()


    # And "update" ? NO! no one can update an InternalTip - NEVER!!1!
    # http://i61.photobucket.com/albums/h63/freecodesource/funny/pictures/funny_signs_6.jpg


    @transact
    def change_inner_value(self, id, escalation=None, accesslimit=None, downloadlimit=None):
        """
        This function is called by admin, whenever want update a value in the

        @param id: Target InternalTip
        @param escalation: new level of escalation threshold
        @param accesslimit: new amount of access limit
        @param downloadlimit: now amount of download limit
        @return: None
        """
        store = self.getStore()

        selected_it = store.find(InternalTip, InternalTip.id == int(id)).one()

        if escalation:
            selected_it.escalation_threshold = escalation

        if accesslimit:
            selected_it.access_limit = accesslimit

        if downloadlimit:
            selected_it.download_limit = downloadlimit


    @transact
    def get_itips_by_maker(self, marker, escalated):
        """
        @escalated: a bool, checked only when marker is u'first', verify if the internaltip
            pertinence value has reach the context expected threshold
        @return: all the internaltips matching with the requested
            marked, between this list of option:
        """
        store = self.getStore()

        if marker == u'new':
            req_it = store.find(InternalTip, InternalTip.mark == u'new')
        elif marker == u'first' and escalated:
            req_it = store.find(InternalTip, (InternalTip.mark == u'first', InternalTip.pertinence_counter >= InternalTip.escalation_threshold ))
        elif marker == u'first' and not escalated:
            req_it = store.find(InternalTip, InternalTip.mark == u'first')
        elif marker == u'second':
            req_it = store.find(InternalTip, InternalTip.mark == u'second')
        else:
            raise NotImplemented

        retVal = []
        for single_itip in req_it:
            retVal.append(single_itip._description_dict())

        return retVal


    @transact
    def flip_mark(self, subject_id, newmark):
        """
        @param newmark: u'first' or u'second', at the start is u'new'
        @subject_id: InternalTip.id to be changed, this mark represent the progress of the iTip
        @return: None
        """
        store = self.getStore()

        if newmark not in self._marker:
            raise NotImplemented

        try:
            requested_t = store.find(InternalTip, InternalTip.id == int(subject_id)).one()
        except NotOneError:
            raise Exception("Not found InternalTip %d" % subject_id)
        if requested_t is None:
            raise Exception("Not found InternalTip %d" % subject_id)

        # XXX log message
        log.debug("flip mark in InternalTip %d, from [%s] to [%s]" % (requested_t.id, requested_t.mark, newmark))

        requested_t.last_activity = gltime.utcDateNow()
        requested_t.mark = newmark


    # REMIND: at the moment is not yet called by the various hooks
    @transact
    def update_last_activity(self, internaltip_id):
        """
        update_last_activity is called when an operation happen in some elements
        related to the internaltip (file upload, new comment, receiver escalation,
        new pertinence, receivertip deleted by receiver)
        """
        store = self.getStore()

        try:
            requested_t = store.find(InternalTip, InternalTip.id == int(internaltip_id)).one()
        except NotOneError:
            raise Exception("Not found InternalTip %d" % internaltip_id)
        if requested_t is None:
            raise Exception("Not found InternalTip %d" % internaltip_id)

        requested_t.last_activity = gltime.utcDateNow()


    @transact
    def update_pertinence(self, internaltip_id, overall_vote):
        """
        In the case a receiver remove himself from a tip, its vote
        cease to be valid. In the case a new tier of receiver join,
        their vote need to be considered. The logic of this function has
        been changed, because the only safe way to have an updated
        vote, is getting the value from the handlers (returned by ReceiverTip
        analysis)
        @param internaltip_id: valid itip_id related to the Tip analized
        @return: None
        """
        store = self.getStore()

        requested_t = store.find(InternalTip, InternalTip.id == int(internaltip_id)).one()

        requested_t.pertinence_counter = overall_vote
        requested_t.last_activity = gltime.utcDateNow()


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
        selected = store.find(InternalTip, InternalTip.id == int(internaltip_id)).one()
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

        rcvr_tips = store.find(ReceiverTip, ReceiverTip.internaltip_id == int(internaltip_id))

        receivers_desc = []
        for tip in rcvr_tips:
            receivers_desc.append(tip.receiver._description_dict())

        return receivers_desc


    @transact
    def get_single(self, internaltip_id):

        store = self.getStore()
        selected = store.find(InternalTip, InternalTip.id == int(internaltip_id)).one()
        return selected._description_dict()


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
            'internaltip_id' : unicode(self.id),
            'context_name' : unicode(self.context.name),
            'context_gus': unicode(self.context_gus),
            'creation_date' : unicode(gltime.prettyDateTime(self.creation_date)),
            'last_activity' : unicode(gltime.prettyDateTime(self.creation_date)),
            'expiration_date' : unicode(gltime.prettyDateTime(self.creation_date)),
            'fields' : dict(self.fields),
            'download_limit' : int(self.download_limit),
            'access_limit' : int(self.access_limit),
            'mark' : unicode(self.mark),
            'pertinence' : unicode(self.pertinence_counter),
            'escalation_threshold' : unicode(self.escalation_threshold),
            'files' : dict(self.files) if self.files else {},
            'receiver_map' : list(self.receivers) if self.receivers else []
        }
        return dict(description_dict)

