from storm.twisted.transact import transact
from storm.locals import Int, Pickle, Date, Unicode, Bool, RawStr

from globaleaks.models.base import TXModel
from globaleaks.utils import log

__all__ = ['Receiver' ]

"""
The association between Receiver and Context is performed in models/admin.py ContextReceivers table
"""
class Receiver(TXModel):
    log.debug("[D] %s %s " % (__file__, __name__), "Class Receiver")
    __storm_table__ = 'receivers'

    receiver_gus = Unicode(primary=True)

    name = Unicode()
    description = Unicode()
    tags = Unicode()
    know_languages = Pickle()

    creation_date = Date()
    last_update_date = Date()

    notification_selected = Int()
    notification_fields = Pickle()
    delivery_selected = Int()
    delivery_fields = Pickle()

    can_delete_submission = Bool()
    can_postpone_expiration = Bool()
    can_configure_delivery = Bool()
    can_configure_notification = Bool()

    # escalation related fiels, if escalation is not configured, both are 0
    can_trigger_escalation = Int()
    # receiver_level, mean first or second level of receiver
    receiver_level = Int()

    receiver_secret = RawStr()
    # receiver_secret would be a passphrase hash, we need to think that a receiver
    # may need to configure notification/delivery also if NO ONE tip is available
    # to him/her, and perhaps, this secret shall be used also as addictional
    # auth beside the Tip_GUS (this was a request of one of our adopters, btw)
    #   --- remind, API do not support that yet

    @transact
    def count(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Receiver", "count")
        store = self.getStore()
        receiver_count = store.find(Receiver).count()
        store.commit()
        store.close()
        return receiver_count

    @transact
    def create_dummy_receivers(self):
        log.debug("[D] %s %s " % (__file__, __name__), "Class Receiver", "create_dummy_receivers")
        from globaleaks.messages.dummy import base
        store = self.getStore()
        for receiver_dict in base.receiverDescriptionDicts:
            receiver = Receiver()
            receiver.receiver_gus = receiver_dict['receiver_gus']
            receiver.name = receiver_dict['name']
            receiver.description = receiver_dict['description']

            receiver.can_delete_submission = receiver_dict['can_delete_submission']
            receiver.can_postpone_expiration = receiver_dict['can_postpone_expiration']
            receiver.can_configure_delivery = receiver_dict['can_configure_delivery']
            receiver.can_configure_notification = receiver_dict['can_configure_notification']
            receiver.can_trigger_escalation = receiver_dict['can_trigger_escalation']

            receiver.know_languages = receiver_dict['languages_supported']
            store.add(receiver)
            store.commit()
        store.close()
        return base.receiverDescriptionDicts


    @transact
    def update_language_mask(self):
        """
        for every contexts:
            select all the receivers in the context:
                sum the language, update the context
        """
        log.debug("[D] %s %s " % (__file__, __name__), "Class Receiver", "update_language_mask")
        pass

    """
    TODO
    * having some columns related the activity of the receiver
    * supports utility for store and manage boolean parameter (may be extended heavily, without having to change the db, and without having an huge amount of columns flags) -- receiver_properties Picke()
    * having two methods of extraction (commonly exposed receiver data, and private extraction)
    * supports module profile selection and configuration
    * maybe has sense create a table with the latest operation of the Receiver, this would be a nice information resume for the users
    """

