from storm.exceptions import NotOneError
from storm.twisted.transact import transact

from storm.locals import Int, Pickle
from storm.locals import Unicode, Bool, Date
from storm.locals import Reference

from globaleaks.utils import gltime, idops

from globaleaks.models.base import TXModel, ModelError
# from globaleaks.models.receiver import Receiver
from globaleaks.models.node import Node
from globaleaks.utils import log


__all__ = [ 'Context', 'InvalidContext' ]


class InvalidContext(ModelError):
    ModelError.error_message = "Invalid Context addressed with context_gus"
    ModelError.error_code = 1 # need to be resumed the table and come back in use them
    ModelError.http_status = 400 # Bad Request

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

    # to be defined ans supported
    scheduled_jobs = Int()
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
        log.debug("[D] %s %s " % (__file__, __name__), "Context delete of", context_gus)

        store = self.getStore('context delete')

        try:
            requested_c = store.find(Context, Context.context_gus == context_gus).one()
        except NotOneError:
            store.close()
            raise InvalidContext
        if requested_c is None:
            store.close()
            raise InvalidContext

        log.msg("Deleted context %s, created in %s" % (requested_c.name, requested_c.creation_date) )
        store.remove(requested_c)
        store.commit()
        store.close()

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

        # This is BAD! but actually we have not yet re-defined a policy to manage
        # REST answers
        retContext = {'context_gus' : requested_c.context_gus,
                      'name': requested_c.name,
                      'description' : requested_c.description,
                      'selectable_receiver' : requested_c.selectable_receiver,
                      'fields' : requested_c.fields,
                      'tip_max_access' : requested_c.tip_max_access,
                      'tip_timetolive' : requested_c.tip_timetolive,
                      'folder_max_download' : requested_c.folder_max_download,
                      'escalation_threshold' : requested_c.escalation_threshold }
        # This is missing of all the other need to be implemented fields

        store.close()
        return retContext

    @transact
    def admin_get_all(self):
        """
        @return: an array containing all contextDescriptionDict
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Context admin_get_all")

        store = self.getStore('context get_all')
        dicts = []

        result = store.find(Context)
        # also if "None", simply is returned an empty array
        for requested_c in result:
            dd = requested_c._description_dict(requested_c.receiver_dicts())
            dicts.append(dd)

        store.close()
        return dicts

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

        retContext = requested_c._description_dict([])
        # remove the keys private in the public diplay of node informations
        retContext.pop('tip_max_access')
        retContext.pop('tip_timetolive')
        retContext.pop('folder_max_download')
        retContext.pop('escalation_threshold')

        store.close()
        return retContext

    @transact
    def public_get_all(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Context public_get_all")

        store = self.getStore('context public_get_all')

        dicts = []
        result = store.find(Context)
        # also "None" is fine: simply is returned an empty array

        for cntx in result:
            dd = cntx._description_dict(cntx.receiver_dicts())
            # remove the keys private in the public diplay of node informations
            dd.pop('tip_max_access')
            dd.pop('tip_timetolive')
            dd.pop('folder_max_download')
            dd.pop('escalation_threshold')

            dicts.append(dd)

        store.close()
        return dicts

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
        log.debug("[D] %s %s " % (__file__, __name__), "Context exists", context_gus)

        store = self.getStore('context get_single')

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

    # This is not a transact method, is used internally by this class
    def _description_dict(self, receivers):

        log.debug("[D] %s %s " % (__file__, __name__), "Context _description_dict")

        description_dict = {"context_gus": self.context_gus,
                            "name": self.name,
                            "description": self.description,
                            "selectable_receiver": self.selectable_receiver,
                            "languages_supported": self.languages_supported,
                            'tip_max_access' : self.tip_max_access,
                            'tip_timetolive' : self.tip_timetolive,
                            'folder_max_download' : self.folder_max_download,
                            'escalation_threshold' : self.escalation_threshold,
                            "fields": self.fields,
                            "receivers": receivers }
        # This is missing of all the other need to be implemented fields

        return description_dict


    # under review
    # under review, at the moment submission is broken
    # under review
    # under review
    def receiver_dicts(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Context receiver_dicts")

        receiver_dicts = []
        for receiver in self.receivers:
            receiver_dict = {"receiver_gus": receiver.receiver_gus,
                    "can_delete_submission": receiver.can_delete_submission,
                    "can_postpone_expiration": receiver.can_postpone_expiration,
                    "can_configure_notification": receiver.can_configure_notification,
                    "can_configure_delivery": receiver.can_configure_delivery,
                    "can_trigger_escalation": receiver.can_trigger_escalation,
                    "name": receiver.name,
                    "description": receiver.description,

                    # one language is the default
                    "languages_supported": receiver.languages_supported
            }
            receiver_dicts.append(receiver_dict)
        return receiver_dicts


    # under review
    def create_receiver_tips(self, internaltip):
        log.debug("[D] %s %s " % (__file__, __name__), "Context create_receiver_tips", internaltip)

        receiver_tips = []
        for receiver in self.receivers:
            from globaleaks.models.tip import ReceiverTip
            receiver_tip = ReceiverTip()
            receiver_tip.new(internaltip.internaltip_id)
            receiver_tips.append(receiver_tip)
        return receiver_tips

    # under review
    @transact
    def add_receiver(self, context_gus, receiver_gus):
        log.debug("[D] %s %s " % (__file__, __name__), "Context add_receiver")

        store = self.getStore('add_receiver')

        receiver = store.find(Receiver,
                        Receiver.receiver_gus==receiver_gus).one()
        context = store.find(Context,
                        Context.context_gus==context_gus).one()

        context.receivers.add(receiver)

        store.commit()
        store.close()
