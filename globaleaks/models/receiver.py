from storm.exceptions import NotOneError
from storm.twisted.transact import transact
from storm.locals import Int, Pickle, Date, Unicode, Bool

from globaleaks.models.base import TXModel, ModelError
from globaleaks.utils import log, idops, gltime
from globaleaks.models.context import  Context, InvalidContext

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

    # MISSING, contexts linked

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

        thaman.receiver_gus = idops.random_receiver_gus()

        thaman.name = receiver_dict['name']
        thaman.description = receiver_dict['description']
        thaman.tags = receiver_dict['tags']
        thaman.know_languages = receiver_dict['know_languages']

        thaman.creation_date = gltime.utcDateNow()
        thaman.update_date = gltime.utcDateNow()
            # last_access is not initialized

        thaman.notification_selected = receiver_dict['notification_selected']
        thaman.notification_fields = receiver_dict['notification_fields']
        thaman.delivery_selected =  receiver_dict['delivery_selected']
        thaman.delivery_fields =  receiver_dict['delivery_fields']

        thaman.can_trigger_escalation = receiver_dict['can_trigger_escalation']
        thaman.receiver_level = receiver_dict['receiver_level']

        # every context need to be checked here
        """
        checker = Context()

        for c_gus in receiver_dict['context_gus_list']:

            # yield ?
            response = checker.exists(c_gus)
            if response:
                print "yep! exists"
            else:
                print "no, do not exists, it's bad"
                raise

        """
        store.add(thaman)
        store.commit()
        store.close()

        return thaman.receiver_gus


    @transact
    def admin_update(self, receiver_gus, receiver_dict):
        """
        This is the method called by the admin for change receiver preferences.
        may edit more elements than the next method (self_update)
        the dict need to be already validated
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class Receiver", "admin_update", receiver_gus)

        store = self.getStore('receiver - admin_update')

        # I didn't understand why, but NotOneError is not raised even if the search return None
        try:
            requested_r = store.find(Receiver, Receiver.receiver_gus == receiver_gus).one()
        except NotOneError:
            store.close()
            raise InvalidReceiver
        if requested_r is None:
            store.close()
            raise InvalidReceiver

        requested_r.name = receiver_dict['name']
        requested_r.description = receiver_dict['description']
        requested_r.tags = receiver_dict['tags']
        requested_r.know_languages = receiver_dict['know_languages']

        requested_r.update_date = gltime.utcDateNow()

        requested_r.notification_selected = receiver_dict['notification_selected']
        requested_r.notification_fields = receiver_dict['notification_fields']
        requested_r.delivery_selected =  receiver_dict['delivery_selected']
        requested_r.delivery_fields =  receiver_dict['delivery_fields']

        requested_r.can_trigger_escalation = receiver_dict['can_trigger_escalation']
        requested_r.receiver_level = receiver_dict['receiver_level']

        # Context TO BE DONE

        store.commit()
        store.close()


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

        # This is BAD! but actually we have not yet re-defined a policy to manage
        # REST answers
        retReceiver = {
                    'receiver_gus' : requested_r.receiver_gus,
                    'name' : requested_r.name,
                    'description' : requested_r.description,
                    'tags = receiver':requested_r.tags,
                    'know_languages' : requested_r.know_languages,
                    #'creation_date' : requested_r.creation_date,
                    #'update_date' : requested_r.update_date,
                    #'last_access' : requested_r.last_access,
                    # datetime.date(2012, 10, 26) is not JSON serializable
                    'can_trigger_escalation' : requested_r.can_trigger_escalation,
                    'receiver_level' : requested_r.receiver_level
                }
                    # 'notification_selected' : notification_selected
                    # 'notification_fields' : notification_fields
                    # 'delivery_selected' :  delivery_selected
                    # 'delivery_fields' :  delivery_fields

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


    @transact
    def update_language_mask(self):
        """
        for every contexts:
            select all the receivers in the context:
                sum the language, update the context
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class Receiver", "update_language_mask")
        pass


# Receivers are NEVER slippery: http://i.imgur.com/saLqb.jpg

