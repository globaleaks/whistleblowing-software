# -*- coding: UTF-8
#
#   models/context
#   **************
# 
# Implementation of the Storm DB side of context table and ORM

from storm.exceptions import NotOneError
from storm.twisted.transact import transact

from storm.locals import Int, Pickle
from storm.locals import Unicode, Bool, DateTime
from storm.locals import Reference

from globaleaks.utils import gltime, idops, log
from globaleaks.models.node import Node
from globaleaks.models.base import TXModel
from globaleaks.rest.errors import ContextGusNotFound, InvalidInputFormat

__all__ = [ 'Context' ]


class Context(TXModel):

    __storm_table__ = 'contexts'

    context_gus = Unicode(primary=True)

    node_id = Int()
    node = Reference(node_id, Node.id)

    name = Unicode()
    description = Unicode()
    fields = Pickle()

    languages_supported = Pickle()

    selectable_receiver = Bool()
    escalation_threshold = Int()

    creation_date = DateTime()
    update_date = DateTime()
    last_activity = DateTime()

    tip_max_access = Int()
    tip_timetolive = Int()
    file_max_download = Int()

    # list of receiver_gus
    receivers = Pickle()

    # to be implemented in REST / dict
    notification_profiles = Pickle()
    delivery_profiles = Pickle()
    inputfilter_chain = Pickle()
    # to be implemented in REST / dict


    @transact
    def new(self, context_dict):
        """
        @param context_dict: a dictionary containing the expected field of a context,
                is called and define as contextDescriptionDict
        @return: context_gus, the universally unique identifier of the context
        """
        store = self.getStore()

        cntx = Context()

        cntx.context_gus = idops.random_context_gus()
        cntx.node_id = 1

        cntx.creation_date = gltime.utcTimeNow()
        cntx.update_date = gltime.utcTimeNow()
        cntx.last_activity = gltime.utcTimeNow()
        cntx.receivers = []

        try:
            cntx._import_dict(context_dict)
        except KeyError, e:
            raise InvalidInputFormat("Context Import failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("Context Import failed (wrong %s)" % e)

        store.add(cntx)
        log.msg("Created context %s at the %s" % (cntx.name, cntx.creation_date) )

        # return context_dict
        return cntx._description_dict()


    @transact
    def update(self, context_gus, context_dict):
        """
        @param context_gus: the universal unique identifier
        @param context_dict: the information fields that need to be update, here is
            supported to be already validated, sanitized and logically verified
            by handlers
        @return: None or Exception on error
        """
        store = self.getStore()

        try:
            requested_c = store.find(Context, Context.context_gus == unicode(context_gus)).one()
        except NotOneError:
            raise ContextGusNotFound

        if requested_c is None:
            raise ContextGusNotFound

        try:
            requested_c._import_dict(context_dict)
        except KeyError, e:
            raise InvalidInputFormat("Context Import failed (missing %s)" % e)
        except TypeError, e:
            raise InvalidInputFormat("Context Import failed (wrong %s)" % e)

        requested_c.update_date = gltime.utcTimeNow()

        log.msg("Updated context %s in %s, created in %s" %
                (requested_c.name, requested_c.update_date, requested_c.creation_date) )

        return requested_c._description_dict()

    @transact
    def delete_context(self, context_gus):
        """
        @param context_gus: the universal unique identifier of the context
        @return: None if is deleted correctly, or raise an exception if something is wrong.
        """

        # Handler Guarantee there operations *before*:
        #
        # delete all the tips associated with the context, comments and files.

        # remove context from the receiver having association with it

        # TODO - delete all the stats associated with the context

        store = self.getStore()

        try:
            requested_c = store.find(Context, Context.context_gus == unicode(context_gus)).one()
        except NotOneError:
            raise ContextGusNotFound
        if requested_c is None:
            raise ContextGusNotFound

        store.remove(requested_c)
        # TODO XXX Applicative log


    @transact
    def get_single(self, context_gus):
        """
        @param context_gus: UUID of the contexts
        @return: the contextDescriptionDict requested, or an exception if do not exists
        """
        store = self.getStore()

        try:
            requested_c = store.find(Context, Context.context_gus == unicode(context_gus)).one()
        except NotOneError:
            raise ContextGusNotFound
        if requested_c is None:
            raise ContextGusNotFound

        return requested_c._description_dict()


    @transact
    def get_all(self):
        """
        @return: an array containing all contextDescriptionDict
        """
        store = self.getStore()

        result = store.find(Context)

        ret_contexts_dicts = []
        for requested_c in result:
            ret_contexts_dicts.append( requested_c._description_dict() )

        return ret_contexts_dicts


    @transact
    def get_contexts_by_receiver(self, receiver_gus):
        """
        @param receiver_gus: list of context associated with receiver_gus,
            may return an empty list if receiver_gus do not exist.
        @return:
        """
        store = self.getStore()

        result = store.find(Context)

        ret_contexts_dicts = []
        for requested_c in result:
            if str(receiver_gus) in requested_c.receivers:
                ret_contexts_dicts.append( requested_c._description_dict() )

        return ret_contexts_dicts


    @transact
    def count(self):
        """
        @return: the number of contexts. Not used at the moment
        """
        store = self.getStore()
        contextnum = store.find(Context).count()
        return contextnum


    # called always by transact method, from models
    def exists(self, context_gus):
        """
        @param context_gus: check if the requested context exists or not
        @return: True if exist, False if not, do not raise exception.
        """

        store = self.getStore()

        try:
            requested_c = store.find(Context, Context.context_gus == unicode(context_gus)).one()

            if requested_c is None:
                retval = False
            else:
                retval = True

        except NotOneError:
            retval = False

        return retval


    # TODO:
    # operation like that and tags, need to be moved in logic in the handler,
    # and in the model just keep the DB storing, timing update, etc
    @transact
    def update_languages(self, context_gus):
        """
        language_list = []
        # for each receiver check every languages supported, if not
        # present in the context declared language, append on it
        for rcvr in self.get_receivers('internal', context_gus):
            for language in rcvr.get('know_languages'):
                if not language in language_list:
                    language_list.append(language)

        store = self.getStore()
        requested_c = store.find(Context, Context.context_gus == unicode(context_gus)).one()
        log.debug("[L] before language update, context", context_gus, "was", requested_c.languages_supported, "and after got", language_list)

        requested_c.languages_supported = language_list
        requested_c.update_date = gltime.utcDateNow()
        """
        raise NotImplemented


    @transact
    def full_context_align(self, receiver_gus, un_context_selected):
        """
        Called by Receiver handlers (PUT|POST), roll in all the context and delete|add|skip
        with the presence of receiver_gus
        """
        store = self.getStore()

        context_selected = []
        for c in un_context_selected:
            context_selected.append(str(c))

        presents_context =  store.find(Context)

        debug_counter = 0
        for c in presents_context:

            # if is not present in context.receivers and is requested: add
            if not receiver_gus in c.receivers:
                if c.context_gus in context_selected:
                    debug_counter += 1
                    c.receivers.append(str(receiver_gus))

            # if is present in receiver.contexts and is not selected: remove
            if receiver_gus in c.receivers:
                if not c.context_gus in context_selected:
                    debug_counter += 1
                    c.receivers.remove(str(receiver_gus))

        log.debug("    %%%%   full_context_align in all contexts after %s has been set with %s: %d mods" %
                  ( receiver_gus, str(context_selected), debug_counter ) )


    @transact
    def context_align(self, context_gus, receiver_selected):
        """
        Called by Context handler, (PUT|POST), just take the context and update the
        associated receivers, checks the receiver existence, and return an
        exception if do not exist.
        """
        from globaleaks.models.receiver import Receiver
        from globaleaks.rest.errors import ReceiverGusNotFound

        store = self.getStore()

        try:
            requested_c = store.find(Context, Context.context_gus == unicode(context_gus)).one()
        except NotOneError:
            raise ContextGusNotFound
        if requested_c is None:
            raise ContextGusNotFound

        requested_c.receivers = []
        for r in receiver_selected:

            try:
                selected = store.find(Receiver, Receiver.receiver_gus == unicode(r) ).one()
            except NotOneError:
                raise ReceiverGusNotFound
            if selected is None:
                raise ReceiverGusNotFound

            requested_c.receivers.append(str(r))
            requested_c.update_date = gltime.utcTimeNow()

        log.debug("    ++++   context_align in receiver %s with receivers %s" %
                  ( context_gus, str(receiver_selected) ) )


    @transact
    def align_receiver_delete(self, context_gus_list, removed_receiver_gus):

        store = self.getStore()

        aligned_counter = 0
        for context_gus in context_gus_list:

            try:
                requested_c = store.find(Context, Context.context_gus == unicode(context_gus)).one()
            except NotOneError:
                raise ContextGusNotFound
            if requested_c is None:
                raise ContextGusNotFound

            if str(removed_receiver_gus) in requested_c.receivers:
                requested_c.receivers.remove(str(removed_receiver_gus))
                aligned_counter += 1
            else:
                raise AssertionError # Just as debug check

        # TODO XXX App log about aligned_counter
        return aligned_counter


    # This is not a transact method, is used internally by this class to assembly
    # response dict. This method return all the information of a context, the
    # called using .pop() should remove the 'confidential' value, if any
    def _description_dict(self):

        description_dict = {
            "context_gus" : unicode(self.context_gus),
            "name" : unicode(self.name),
            "description" : unicode(self.description),
            "selectable_receiver" : unicode(self.selectable_receiver),
            "languages" : list(self.languages_supported) if self.languages_supported else [],
            'tip_max_access' : int(self.tip_max_access),
            'tip_timetolive' : int(self.tip_timetolive),
            'file_max_download' : int(self.file_max_download),
            'escalation_threshold' : int(self.escalation_threshold),
            'fields': list(self.fields) if self.fields else [],
            'receivers' : list(self.receivers) if self.receivers else []
        }
        return dict(description_dict)

    # this method import the remote received dict.
    # would be expanded with defaults value (if configured) and with checks about
    # expected fields. is called by new() and update()

    def _import_dict(self, context_dict):

        self.name = context_dict['name']
        self.fields = context_dict['fields']
        self.description = context_dict['description']
        self.selectable_receiver = context_dict['selectable_receiver']
        self.escalation_threshold = context_dict['escalation_threshold']
        self.tip_max_access = context_dict['tip_max_access']
        self.tip_timetolive = context_dict['tip_timetolive']
        self.file_max_download = context_dict['file_max_download']

        if self.selectable_receiver and self.escalation_threshold:
            log.msg("[!] Selectable receiver feature and escalation threshold can't work both: threshold ignored")
            self.escalation_threshold = 0

