from storm.exceptions import NotOneError
from storm.twisted.transact import transact

from storm.locals import Int, Pickle
from storm.locals import Unicode, Bool, Date
from storm.locals import Reference

from globaleaks.utils import gltime, idops, log

from globaleaks.models.base import TXModel, ModelError

__all__ = [ 'Context', 'InvalidContext' ]


class InvalidContext(ModelError):

    def __init__(self):
        ModelError.error_message = "Invalid Context addressed with context_gus"
        ModelError.error_code = 1 # need to be resumed the table and come back in use them
        ModelError.http_status = 400 # Bad Request

class Context(TXModel):
    from globaleaks.models.node import Node

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

    creation_date = Date()
    update_date = Date()
    last_activity = Date()

    tip_max_access = Int()
    tip_timetolive = Int()
    folder_max_download = Int()

    # to be implemented in REST / dict
    notification_profiles = Pickle()
    delivery_profiles = Pickle()
    inputfilter_chain = Pickle()
    # to be implemented in REST / dict

    # public stats reference
    # private stats reference

    @transact
    def new(self, context_dict):
        """
        @param context_dict: a dictionary containing the expected field of a context,
                is called and define as contextDescriptionDict
        @return: context_gus, the universally unique identifier of the context
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Context new", context_dict)

        store = self.getStore('context new')

        cntx = Context()

        cntx.context_gus = idops.random_context_gus()
        cntx.node_id = 1

        cntx.creation_date = gltime.utcDateNow()
        cntx.update_date = gltime.utcDateNow()
        cntx.last_activity = gltime.utcDateNow()

        cntx.name = context_dict["name"]
        cntx.fields = context_dict["fields"]
        cntx.description = context_dict["description"]
        cntx.selectable_receiver = context_dict["selectable_receiver"]
        cntx.escalation_threshold = context_dict["escalation_threshold"]

        cntx.tip_max_access = context_dict['tip_max_access']
        cntx.tip_timetolive = context_dict['tip_timetolive']
        cntx.folder_max_download = context_dict['folder_max_download']

        # context.languages_supported = context_dict["languages_supported"]
        # this is not taked by the dict, come from receivers declared knowledge

        # Receiver is associated with a Context, in Receiver.new or Receiver.admin_update

        store.add(cntx)
        log.msg("Created context %s at the %s" % (cntx.name, cntx.creation_date) )
        store.commit()
        store.close()

        # return context_dict
        return cntx.context_gus

    @transact
    def update(self, context_gus, context_dict):
        """
        @param context_gus: the universal unique identifier
        @param context_dict: the information fields that need to be update, here is
            supported to be already validated, sanitized and logically verified
            by handlers
        @return: None or Exception on error
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Context update of", context_gus)
        store = self.getStore('context update')

        try:
            requested_c = store.find(Context, Context.context_gus == context_gus).one()
        except NotOneError:
            store.close()
            raise InvalidContext
        if requested_c is None:
            store.close()
            raise InvalidContext

        requested_c.name = context_dict['name']
        requested_c.fields = context_dict['fields']
        requested_c.description = context_dict['description']
        requested_c.selectable_receiver = context_dict['selectable_receiver']
        requested_c.escalation_threshold = context_dict['escalation_threshold']

        requested_c.tip_max_access = context_dict['tip_max_access']
        requested_c.tip_timetolive = context_dict['tip_timetolive']
        requested_c.folder_max_download = context_dict['folder_max_download']

        requested_c.update_date = gltime.utcDateNow()

        store.commit()
        log.msg("Updated context %s in %s, created in %s" %
                (requested_c.name, requested_c.update_date, requested_c.creation_date) )
        store.close()

    @transact
    def delete_context(self, context_gus):
        """
        @param context_gus: the universal unique identifier of the context
        @return: None if is deleted correctly, or raise an exception if something is wrong.
        """
        from globaleaks.models.receiver import Receiver
        log.debug("[D] %s %s " % (__file__, __name__), "Context delete of", context_gus)

        # first, perform existence checks, this would avoid continuos try/except here
        if not self.exists(context_gus):
            raise InvalidContext

        # delete all the reference to the context in the receivers
        receiver_iface = Receiver()

        unlinked_receivers = receiver_iface.unlink_context(context_gus)

        # TODO - delete all the tips associated with the context
        # TODO - delete all the jobs associated with the context
        # TODO - delete all the stats associated with the context

        store = self.getStore('context delete')

        try:
            requested_c = store.find(Context, Context.context_gus == context_gus).one()
        except NotOneError:
            store.close()
            raise InvalidContext
        if requested_c is None:
            store.close()
            raise InvalidContext

        store.remove(requested_c)
        store.commit()
        store.close()

        log.msg("Deleted context %s, created in %s used by %d receivers" %
                (requested_c.name, requested_c.creation_date, unlinked_receivers) )


    @transact
    def admin_get_single(self, context_gus):
        """
        @param context_gus: UUID of the contexts
        @return: the contextDescriptionDict requested, or an exception if do not exists
        """
        store = self.getStore('context admin_get_single')

        try:
            requested_c = store.find(Context, Context.context_gus == context_gus).one()
        except NotOneError:
            store.close()
            raise InvalidContext
        if requested_c is None:
            store.close()
            raise InvalidContext

        ret_context_dict = requested_c._description_dict()
        ret_context_dict.update({'receivers' : requested_c.get_receivers(context_gus, 'admin')})

        store.close()
        return ret_context_dict

    @transact
    def admin_get_all(self):
        """
        @return: an array containing all contextDescriptionDict
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Context admin_get_all")

        store = self.getStore('context admin_get_all')
        ret_contexts_dicts = []

        result = store.find(Context)

        # also if "None", simply is returned an empty array
        for requested_c in result:

            description_dict = requested_c._description_dict()
            description_dict.update({'receivers' : requested_c.get_receivers(requested_c.context_gus, 'admin') })

            ret_contexts_dicts.append(description_dict)

        store.close()
        return ret_contexts_dicts

    @transact
    def public_get_single(self, context_gus):
        """
        @param context_gus: requested context
        @return: context dict, stripped of the 'reserved' info
        """
        store = self.getStore('context public_get_single')

        try:
            requested_c = store.find(Context, Context.context_gus == context_gus).one()
        except NotOneError:
            store.close()
            raise InvalidContext
        if requested_c is None:
            store.close()
            raise InvalidContext

        ret_context_dict = requested_c._description_dict()
        # remove the keys private in the public diplay of node informations
        ret_context_dict.pop('tip_max_access')
        ret_context_dict.pop('tip_timetolive')
        ret_context_dict.pop('folder_max_download')
        ret_context_dict.pop('escalation_threshold')

        ret_context_dict.update({'receivers' : requested_c.get_receivers(context_gus, 'public') })

        store.close()
        return ret_context_dict

    @transact
    def public_get_all(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Context public_get_all")

        store = self.getStore('context public_get_all')

        ret_contexts_dicts = []
        result = store.find(Context)
        # also "None" is fine: simply is returned an empty array

        for requested_c in result:

            description_dict = requested_c._description_dict()
            # remove the keys private in the public diplay of node informations
            description_dict.pop('tip_max_access')
            description_dict.pop('tip_timetolive')
            description_dict.pop('folder_max_download')
            description_dict.pop('escalation_threshold')

            description_dict.update({'receivers' : requested_c.get_receivers(requested_c.context_gus, 'public') })

            ret_contexts_dicts.append(description_dict)

        store.close()
        return ret_contexts_dicts

    @transact
    def count(self):
        """
        @return: the number of contexts. Not used at the moment
        """
        store = self.getStore('context count')
        contextnum = store.find(Context).count()
        store.close()
        return contextnum

    @transact
    def exists(self, context_gus):
        """
        @param context_gus: check if the requested context exists or not
        @return: True if exist, False if not, do not raise exception.
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Context exists ?", context_gus)

        store = self.getStore('context exist')

        try:
            requested_c = store.find(Context, Context.context_gus == context_gus).one()

            if requested_c is None:
                retval = False
            else:
                retval = True

        except NotOneError:
            retval = False

        store.close()
        return retval

    # this is called by Receiver.admin_update and would be
    # called also by Receiver.self_update.
    #
    # ----- Optionally a function like that would be implemented in async,
    # like a submission transformation in Tips, and Tips transformation
    # in notification and delivery.
    # I would avoid this approach, because mean that Context resource
    # may change when an user do not know, and then require a
    # continuos refresh, unacceptable in a Tor link. ------------------
    def update_languages(self, context_gus):

        log.debug("[D] %s %s " % (__file__, __name__), "update_languages ", context_gus)

        language_list = []

        # for each receiver check every languages supported, if not
        # present in the context declared language, append on it
        for rcvr in self.get_receivers(context_gus, 'internal'):
            for language in rcvr.get('know_languages'):
                if not language in language_list:
                    language_list.append(language)

        store = self.getStore('context update_languages')
        requested_c = store.find(Context, Context.context_gus == context_gus).one()
        log.debug("[L] before language update, context", context_gus, "was", requested_c.languages_supported, "and after got", language_list)

        requested_c.languages_supported = language_list
        requested_c.update_date = gltime.utcDateNow()

        store.commit()
        store.close()

    # this is called internally by a @transact functions
    def get_receivers(self, context_gus, info_type):
        """
        @param context_gus: target context to be searched between receivers
        @info_type: its a string with three possible values:
           'submission': called for get the information required in the submission/tip process
           'public': get the information represented to the WB and in public
           'internal': a series of data used by internal calls
           'admin': complete dump of the information, wrap Receiver._description_dict
           'gus': only the list of receiver globaleaks uniq strings
        @return: a list, 0 to MANY receiverDict tuned for the caller requirements
        """
        from globaleaks.models.receiver import Receiver

        typology = [ 'submission', 'public', 'internal', 'admin', 'gus' ]

        if not info_type in typology:
            log.debug("[Fatal]", info_type, "not found in", typology)
            raise NotImplementedError

        store = self.getStore('context get_receivers')

        # I've made some experiment with https://storm.canonical.com/Manual#IN (in vain)
        # the goal is search which context_gus is present in the Receiver.context_gus_list
        # and then work in the selected Receiver.

        results = store.find(Receiver)

        receiver_list = []
        for r in results:
            if context_gus in r.context_gus_list:
                partial_info = {}

                if info_type == typology[0]: # submission
                    partial_info.update({'receiver_gus' : r.receiver_gus})
                    partial_info.update({'notification_selected' : r.notification_selected })
                    partial_info.update({'notification_fields' : r.notification_fields })
                if info_type == typology[1]: # public
                    partial_info.update({'receiver_gus' : r.receiver_gus})
                    partial_info.update({'name': r.name })
                    partial_info.update({'description': r.description })
                if info_type == typology[2]: # internal
                    partial_info.update({'receiver_gus' : r.receiver_gus})
                    partial_info.update({'know_languages' : r.know_languages })
                if info_type == typology[3]: # admin
                    partial_info = r._description_dict()
                if info_type == typology[4]: # gus_only
                    partial_info.update({'receiver_gus' : r.receiver_gus})

                receiver_list.append(partial_info)

        store.close()
        return receiver_list


    # This is not a transact method, is used internally by this class to assembly
    # response dict. This method return all the information of a context, the
    # called using .pop() should remove the 'confidential' value, if any
    def _description_dict(self):

        # This is BAD! but actually we have not yet re-defined a policy to manage
        # REST answers
        description_dict = {"context_gus": self.context_gus,
                            "name": self.name,
                            "description": self.description,
                            "selectable_receiver": self.selectable_receiver,
                            "languages_supported": self.languages_supported,
                            'tip_max_access' : self.tip_max_access,
                            'tip_timetolive' : self.tip_timetolive,
                            'folder_max_download' : self.folder_max_download,
                            'escalation_threshold' : self.escalation_threshold,
                            "fields": self.fields }
        # This is missing of all the other need to be implemented fields,
        # receivers is missing because is append only when needed.

        return description_dict

    @transact
    # Not yet used except unit test - need to be tested
    def add_receiver(self, context_gus, receiver_gus):
        """
        @param context_gus: the context to add the receiver
        @param receiver_gus: receiver that would be added
        @return: None, or raise an exception if Receiver or Context are invalid
        add_receiver should be call every time a Context is updated. If a receiver is
        already present, do not perform operation in that resource.
        """
        from globaleaks.models.receiver import Receiver, InvalidReceiver

        log.debug("[D] %s %s " % (__file__, __name__), "Context add_receiver", context_gus, receiver_gus)

        if not self.exists(context_gus):
            raise InvalidContext

        store = self.getStore('add_receiver')

        try:
            requested_r = store.find(Receiver, Receiver.receiver_gus == receiver_gus).one()
        except NotOneError:
            store.close()
            return InvalidReceiver
        if requested_r is None:
            store.close()
            return InvalidReceiver

        if not context_gus in requested_r.context_gus_list:
            requested_r.context_gus_list.append(context_gus)
            # update last activities, in context and receiver

        log.msg("Addedd receiver", requested_r.receiver_gus, requested_r.name, "to context", context_gus)
        store.commit()
        store.close()

    def create_receiver_tips(self, submissionDict):
        """
        @param submissionDict:
        @return:
        """
        from globaleaks.models.submission import Submission

        log.debug("[D] %s %s " % (__file__, __name__), "Context create_receiver_tips", submissionDict)

        store = self.getStore('create_receiver_tips')

        source_s = store.find(Submission, Submission.submission_gus == submissionDict['submission_gus']).one()

        store.close()

        """
        receiver_tips = []
        for receiver in self.receivers:
            from globaleaks.models.tip import ReceiverTip
            receiver_tip = ReceiverTip()
            receiver_tip.new(internaltip.internaltip_id)
            receiver_tips.append(receiver_tip)
        return receiver_tips
        """

