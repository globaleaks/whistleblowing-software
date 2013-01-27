# -*- coding: UTF-8
#
#   models/receiver
#   ***************
# 
# Storm DB implementation of the receiver table and ORM

from storm.exceptions import NotOneError
from storm.locals import Int, Pickle, DateTime, Unicode, Bool

from globaleaks.models.base import TXModel
from globaleaks.utils import log, idops, gltime
from globaleaks.rest.errors import ReceiverGusNotFound, InvalidInputFormat

__all__ = ['Receiver']

class Receiver(TXModel):
    """
    Receiver description model, some Receiver dependent information are
    also in globaleaks.models.plugin ReceiverConfs table
    """
    __storm_table__ = 'receivers'

    receiver_gus = Unicode(primary=True)

    creation_date = DateTime()
    update_date = DateTime()

    # Those four variable can be changed by the Receiver
    name = Unicode()
    description = Unicode()

    # Tags and know_languages reflect in the Context, based on the
    # sum of the Receivers assigned.
    tags = Pickle()
    know_languages = Pickle()

    # Admin choosen options
    can_delete_submission = Bool()
    can_postpone_expiration = Bool()
    can_configure_delivery = Bool()
    can_configure_notification = Bool()
    admin_description = Unicode() # XXX: update API, scripts and outputs

    # receiver_tier = 1 or 2. Mean being part of the first or second level
    # of receivers body. if threshold is configured in the context. default 1
    receiver_level = Int()

    # this for keeping the same feature of GL 0.1
    secret = Unicode()

    # list of context_gus which receiver is associated
    contexts = Pickle()

    def __init__(self, theStore):
        self.store = theStore


    def count(self):
        receiver_count = self.store.find(Receiver).count()
        return receiver_count


    def new(self, receiver_dict):
        """
        @receiver_dict: here is supposed to be already sanitized
        @return: the receiver_gus or raise an exception

        Behold! this method convert a soulless dict in Tha Man, The Choosen
        One that want review the whistles blowed documents. It's a sort of
        transparency baptism: here you get your GlobaLeaks Unique String, sir!
        """


        try:
            self._import_dict(receiver_dict)
        except KeyError, e:
            raise InvalidInputFormat("initialization failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("initialization failed (wrong %s)" % e)

        self.receiver_gus = idops.random_receiver_gus()

        self.creation_date = gltime.utcTimeNow()
        self.update_date = gltime.utcTimeNow()

        self.store.add(self)

        return self._description_dict()



    def update(self, receiver_gus, receiver_dict):
        """
        This is the method called by the admin for change receiver preferences.
        may edit more elements than the next method (self_update)
        the dict need to be already validated
        """


        try:
            requested_r = self.store.find(Receiver, Receiver.receiver_gus == unicode(receiver_gus)).one()
        except NotOneError:
            raise ReceiverGusNotFound
        if requested_r is None:
            raise ReceiverGusNotFound

        try:
            requested_r._import_dict(receiver_dict)
        except KeyError, e:
            raise InvalidInputFormat("admin update failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("admin update failed (wrong %s)" % e)

        requested_r.update_date = gltime.utcTimeNow()
        return requested_r._description_dict()



    def self_update(self, receiver_gus, receiver_dict):
        """
        This is the method called by a receiver for change/set their preference
        """

        try:
            requested_r = self.store.find(Receiver, Receiver.receiver_gus == unicode(receiver_gus)).one()
        except NotOneError:
            raise ReceiverGusNotFound
        if requested_r is None:
            raise ReceiverGusNotFound

        try:
            requested_r.name = receiver_dict['name']
            requested_r.description = receiver_dict['description']
            requested_r.tags = receiver_dict['tags']
            requested_r.know_languages = receiver_dict['languages']
            requested_r.update_date = gltime.utcTimeNow()

        except KeyError, e:
            raise InvalidInputFormat("self update failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("self update failed (wrong %s)" % e)

        return requested_r._description_dict()



    def get_single(self, receiver_gus):
        """
        @return the dictionary describing the requested receiver, or an exception if do not exists.
        """

        try:
            requested_r = self.store.find(Receiver, Receiver.receiver_gus == unicode(receiver_gus)).one()
        except NotOneError:
            raise ReceiverGusNotFound
        if requested_r is None:
            raise ReceiverGusNotFound

        return requested_r._description_dict()



    def get_all(self):
        """
        @return: a list of all the receiver in the node.
        """

        all_r = self.store.find(Receiver)

        retVal = []
        for rcvr in all_r:
            retVal.append(rcvr._description_dict())

        return retVal



    def get_receivers_by_context(self, context_gus):
        """
        @param context_gus: an unchecked context_gus string
        @return: a list of receivers description dict, with only the
            receivers assigned to the requested context_gus.
            Invalid context_gus would return 0 receiver assigned.
        """

        all_r = self.store.find(Receiver)

        retVal = []
        for rcvr in all_r:
            if str(context_gus) in rcvr.contexts:
                retVal.append(rcvr._description_dict())

        if len(retVal) == 0:
            log.debug("[W] No receiver assigned to the context %s" % context_gus)

        return retVal



    def full_receiver_align(self, context_gus, un_receiver_selected):
        """
        Called by Context handlers (PUT|POST), roll in all the receiver and delete|add|skip
        with the presence of context_gus
        """

        receiver_selected = []
        for r in un_receiver_selected:
            receiver_selected.append(str(r))

        presents_receiver = self.store.find(Receiver)

        debug_counter = 0
        for r in presents_receiver:

            # if is not present in receiver.contexts and is requested: add
            if not context_gus in r.contexts:
                if r.receiver_gus in receiver_selected:
                    debug_counter += 1
                    r.contexts.append(str(context_gus))
                    r.update_date = gltime.utcTimeNow()

            # if is present in context.receiver and is not selected: remove
            if context_gus in r.contexts:
                if not r.receiver_gus in receiver_selected:
                    debug_counter += 1
                    r.contexts.remove(str(context_gus))
                    r.update_date = gltime.utcTimeNow()

        log.debug("    ****   full_receiver_align in all receivers after %s has been set with %s: %d mods" %
                  ( context_gus, str(receiver_selected), debug_counter ) )



    def receiver_align(self, receiver_gus, context_selected):
        """
        Called by Receiver handler, (PUT|POST), just take the receiver and update the
        associated contexts
        """
        from globaleaks.models.context import Context
        from globaleaks.rest.errors import ContextGusNotFound


        try:
            requested_r = self.store.find(Receiver, Receiver.receiver_gus == unicode(receiver_gus)).one()
        except NotOneError:
            raise ReceiverGusNotFound
        if requested_r is None:
            raise ReceiverGusNotFound

        requested_r.contexts = []
        for c in context_selected:

            try:
                selected = self.store.find(Context, Context.context_gus == unicode(c)).one()
            except NotOneError:
                raise ContextGusNotFound
            if selected is None:
                raise ContextGusNotFound

            requested_r.contexts.append(str(c))
            requested_r.update_date = gltime.utcTimeNow()

        log.debug("    ++++   receiver_align in receiver %s with contexts %s" %
                  ( receiver_gus, str(context_selected) ) )



    def receiver_delete(self, receiver_gus):
        """
        Delete a receiver, or raise an exception if do not exist. The hanlder calling
        this method would have provided to remove the ReceiverTip (if exits, and if needed)
        """

        try:
            requested_r = self.store.find(Receiver, Receiver.receiver_gus == unicode(receiver_gus)).one()
        except NotOneError:
            raise ReceiverGusNotFound
        if requested_r is None:
            raise ReceiverGusNotFound

        # TODO XXX Applicative log
        self.store.remove(requested_r)



    def align_context_delete(self, receivers_gus_list, removed_context_gus):
        """
        @param receivers_gus_list: a list of receiver_gus target of the ops
        @param context_gus: context being removed
        @return: None
        """

        aligned_counter = 0

        for receiver_gus in receivers_gus_list:

            try:
                requested_r = self.store.find(Receiver, Receiver.receiver_gus == unicode(receiver_gus)).one()
            except NotOneError:
                raise ReceiverGusNotFound
            if requested_r is None:
                raise ReceiverGusNotFound

            if str(removed_context_gus) in requested_r.contexts:
                requested_r.contexts.remove(str(removed_context_gus))
                requested_r.update_date = gltime.utcTimeNow()
                aligned_counter += 1
            else:
                raise AssertionError # Just for debug

        # TODO XXX Applicative log about aligned_counter
        return aligned_counter


    # this method import the remote received dict.
    # is called by new() and admin_update()
    def _import_dict(self, source_rd):

        self.name = source_rd['name']
        self.description = source_rd['description']
        self.tags = source_rd['tags']
        self.know_languages = source_rd['languages']

        # This need to be verified in the calling function, between the valid
        # notification modules available.

        self.can_delete_submission = source_rd['can_delete_submission']
        self.can_postpone_expiration = source_rd['can_postpone_expiration']
        self.can_configure_delivery = source_rd['can_configure_delivery']
        self.can_configure_notification = source_rd['can_configure_notification']

        self.receiver_level = source_rd['receiver_level']

    # this is non  method used when is required to dump the objects
    # in a dict. The returned values should be removed using .pop(),
    def _description_dict(self):

        descriptionDict = {
            'receiver_gus' : unicode(self.receiver_gus),
            'name' : unicode(self.name),
            'description' : unicode(self.description),
            'tags' : list(self.tags) if self.tags else [],
            'languages' : list(self.know_languages) if self.know_languages else [],
            'creation_date' : unicode(gltime.prettyDateTime(self.creation_date)),
            'update_date' : unicode(gltime.prettyDateTime(self.update_date)),
            'contexts' : list(self.contexts) if self.contexts else [],
            'receiver_level' : int(self.receiver_level),
            'can_delete_submission' : bool(self.can_delete_submission),
            'can_postpone_expiration' : bool(self.can_postpone_expiration),
            'can_configure_delivery' : bool(self.can_configure_delivery),
            'can_configure_notification' : bool(self.can_configure_notification)
        }
        return dict(descriptionDict)


# Receivers are NEVER slippery: http://i.imgur.com/saLqb.jpg

