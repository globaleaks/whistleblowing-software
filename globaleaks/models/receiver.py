from storm.exceptions import NotOneError
from storm.twisted.transact import transact
from storm.locals import Int, Pickle, Date, Unicode, Bool

from globaleaks.models.context import Context, InvalidContext
from globaleaks.models.base import TXModel, ModelError
from globaleaks.utils import log, idops, gltime

__all__ = ['Receiver', 'InvalidReceiver' ]

class InvalidReceiver(ModelError):
    ModelError.error_message = "Invalid Receiver addressed with receiver_gus"
    ModelError.error_code = 1 # need to be resumed the table and come back in use them
    ModelError.http_status = 400 # Bad Request

# The association between Receiver and Context is performed in models/admin.py ContextReceivers table

class Receiver(TXModel):
    log.debug("[D] %s %s " % (__file__, __name__), "Class Receiver")
    __storm_table__ = 'receivers'

    receiver_gus = Unicode(primary=True)

    name = Unicode()
    description = Unicode()
    tags = Pickle()
    know_languages = Pickle()

    creation_date = Date()
    update_date = Date()
    last_access = Date()

    notification_selected = Unicode()
        # need to be a module_gus, but at the moment is just "email"
    delivery_selected = Unicode()
        # need to be a module_gus, but at the moment is just "local"

    notification_fields = Pickle()
        # email is the first development (email is stored here)
    delivery_fields = Pickle()
        # local delivery is the first configured delivery (no info here)

    can_delete_submission = Bool()
    can_postpone_expiration = Bool()
    can_configure_delivery = Bool()
    can_configure_notification = Bool()

    # escalation related fields, if escalation is not configured, both are 0
    can_trigger_escalation = Int()
    # receiver_level, mean first or second level of receiver
    receiver_level = Int()

    # this for keeping the same feature of GL 0.1
    secret = Unicode()

    context_gus_list = Pickle()

    @transact
    def count(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Receiver", "count")
        store = self.getStore('receiver count')
        receiver_count = store.find(Receiver).count()
        store.commit()
        store.close()
        return receiver_count

    @transact
    def new(self, receiver_dict):
        """
        @receiver_dict: here is supposed to be already sanitized
        @return: the receiver_gus or raise an exception

        Behold! this method convert a soulless dict in Tha Man, The Choosen
        One that want review the whistles blowed documents. It's a sort of
        transparency baptism: here you get your GlobaLeaks Unique String, sir!
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Receiver new", receiver_dict)

        store = self.getStore('receiver new')

        thaman = Receiver()

        thaman._import_dict(receiver_dict)
        thaman.receiver_gus = idops.random_receiver_gus()

        thaman.creation_date = gltime.utcDateNow()
        thaman.update_date = gltime.utcDateNow()
        # last_access is not initialized

        thaman.context_gus_list = []
        context_iface = Context()

        # every context need to be checked here
        for c in receiver_dict['context_gus_list']:

            if context_iface.exists(c):
                thaman.context_gus_list.append(c)
            else:
                store.close()
                raise InvalidContext

        store.add(thaman)
        store.commit()
        store.close()

        # update contexts where needed
        for c in receiver_dict['context_gus_list']:
            context_iface.update_languages(c)

        return thaman.receiver_gus


    @transact
    def admin_update(self, receiver_gus, receiver_dict):
        """
        This is the method called by the admin for change receiver preferences.
        may edit more elements than the next method (self_update)
        the dict need to be already validated
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class Receiver", "admin_update", receiver_gus)

        store = self.getStore('receiver admin_update')

        # I didn't understand why, but NotOneError is not raised even if the search return None
        try:
            requested_r = store.find(Receiver, Receiver.receiver_gus == receiver_gus).one()
        except NotOneError:
            store.close()
            raise InvalidReceiver
        if requested_r is None:
            store.close()
            raise InvalidReceiver

        requested_r._import_dict(receiver_dict)
        requested_r.update_date = gltime.utcDateNow()

        context_iface = Context()

        # actual receiver list is zeroed and rewritten.
        requested_r.context_gus_list = []
        # every context need to be checked here, it do not exist: "Bad Request"
        for c in receiver_dict['context_gus_list']:

            context_exists = context_iface.exists(c)
            if context_exists:
                requested_r.context_gus_list.append(c)
            else:
                store.rollback()
                store.close()
                raise InvalidContext

        store.commit()
        store.close()

        # all the contexts would be updated in some aspects
        for c in receiver_dict['context_gus_list']:
            context_iface.update_languages(c)


    @transact
    def self_update(self, receiver_gus, receiver_dict):
        """
        This is the method called by a receiver for change/set their preference
        """
        pass

    @transact
    def admin_get_single(self, receiver_gus):
        """
        @return a receiverDescriptionDict
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class Receiver", "admin_get_single", receiver_gus)

        store = self.getStore('receiver - admin_get_single')

        # I didn't understand why, but NotOneError is not raised even if the search return None
        try:
            requested_r = store.find(Receiver, Receiver.receiver_gus == receiver_gus).one()
        except NotOneError:
            store.close()
            raise InvalidReceiver
        if requested_r is None:
            store.close()
            raise InvalidReceiver

        retReceiver = requested_r._description_dict()

        store.close()
        return retReceiver


    @transact
    def admin_get_all(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Receiver", "admin_get_all")
        pass

    @transact
    def public_get_single(self, receiver_gus):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Receiver", "public_get_single", receiver_gus)
        pass

    @transact
    def public_get_all(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Receiver", "public_get_all")
        pass

    @transact
    def receiver_delete(self, receiver_gus):
        """
        Delete a receiver, or raise an exception if do not exist
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Receiver delete of", receiver_gus)

        store = self.getStore('receiver delete')

        try:
            requested_r = store.find(Receiver, Receiver.receiver_gus == receiver_gus).one()
        except NotOneError:
            store.close()
            raise InvalidReceiver
        if requested_r is None:
            store.close()
            raise InvalidReceiver

        # log.info()
        store.remove(requested_r)
        store.commit()
        store.close()

    # being a method called by another @transact, do not require @tranact
    # too, because otherwise the order is screwed
    def unlink_context(self, context_gus):
        """
        @param context_gus: context to be found and unassigned if present
        @return: number of receiver unassigned in the operation.
        This method is called when a context is deleted: all the receiver
        reference pointing on it, need to be unassigned
        ----- by hypothesis, here we can delete the receiver without a context
        """
        store = self.getStore('receiver unlink_context')

        # same consideration of Context.get_receivers: probabily there are a more
        # efficient selection query, for search a context_gus in a list
        results = store.find(Receiver)

        unassigned_count = 0
        for r in results:
            if context_gus in r.context_gus_list:
                r.context_gus_list.remove(context_gus)
                unassigned_count += 1

        store.commit()
        store.close()
        return unassigned_count

    # this is non @trasact called by method that needs to import the remote received dict
    # woukd be expanded with defaults value (if configured) and with checks about
    # expected fields. is called by new() and admin_update() (and self_update() not yet!)
    def _import_dict(self, source_rd):

        self.name = source_rd['name']
        self.description = source_rd['description']
        self.tags = source_rd['tags']
        self.know_languages = source_rd['know_languages']

        self.notification_selected = source_rd['notification_selected']
        self.notification_fields = source_rd['notification_fields']
        self.delivery_selected =  source_rd['delivery_selected']
        self.delivery_fields =  source_rd['delivery_fields']

        self.can_delete_submission = source_rd['can_delete_submission']
        self.can_postpone_expiration = source_rd['can_postpone_expiration']
        self.can_configure_delivery = source_rd['can_configure_delivery']
        self.can_configure_notification = source_rd['can_configure_notification']

        self.can_trigger_escalation = source_rd['can_trigger_escalation']
        self.receiver_level = source_rd['receiver_level']

    # this is non @transact method used when is required to dump the objects
    # in a dict. The returned values should be removed using .pop(),
    def _description_dict(self):

        descriptionDict = {
            'receiver_gus' : self.receiver_gus,
            'name' : self.name,
            'description' : self.description,
            'tags = receiver':self.tags,
            'know_languages' : self.know_languages,
            'notification_selected' : self.notification_selected,
            'notification_fields' : self.notification_fields,
            'delivery_selected' :  self.delivery_selected,
            'delivery_fields' :  self.delivery_fields,
            #'creation_date' : self.creation_date,
            #'update_date' : self.update_date,
            #'last_access' : self.last_access,
            # datetime.date(2012, 10, 26) is not JSON serializable
            'context_gus_list' : self.context_gus_list,
            'can_trigger_escalation' : self.can_trigger_escalation,
            'receiver_level' : self.receiver_level,
            'can_delete_submission' : self.can_delete_submission,
            'can_postpone_expiration' : self.can_postpone_expiration,
            'can_configure_delivery' : self.can_configure_delivery,
            'can_configure_notification' : self.can_configure_notification
        }
        return descriptionDict

# Receivers are NEVER slippery: http://i.imgur.com/saLqb.jpg

