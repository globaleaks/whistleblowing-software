from twisted.internet.defer import returnValue
from storm.twisted.transact import transact
from storm.locals import *

from globaleaks.models.base import TXModel

__all__ = ['Receiver', 'ReceiverPreferences']

class Receiver(TXModel):
    __storm_table__ = 'receivers'

    id = Int(primary=True)

    receiver_id = Unicode()
    name = Unicode()
    description = Unicode()
    tags = Unicode()

    creation_date = Date()
    last_update_date = Date()

    languages_supported = Pickle()

    can_delete_submission = Bool()
    can_postpone_expiration = Bool()
    can_configure_delivery = Bool()
    can_configure_notification = Bool()

    can_trigger_escalation = Bool()

    receiver_level = Int()

    def new(self, internaltip_id):
        self.internaltip_id = internaltip_id

    @transact
    def receiver_dicts(self):
        store = self.getStore()
        receiver_dicts = []

        for receiver in store.find(Receiver):
            receiver_dict = {}
            receiver_dict['id'] = receiver.receiver_id
            receiver_dict['name'] = receiver.name
            receiver_dict['description'] = receiver.description

            receiver_dict['can_delete_submission'] = receiver.can_delete_submission
            receiver_dict['can_postpone_expiration'] = receiver.can_postpone_expiration
            receiver_dict['can_configure_delivery'] = receiver.can_configure_delivery

            receiver_dict['can_configure_notification'] = receiver.can_configure_notification
            receiver_dict['can_trigger_escalation'] = receiver.can_trigger_escalation

            receiver_dict['languages_supported'] = receiver.languages_supported
            receiver_dicts.append(receiver_dict)

        store.commit()
        store.close()

        return receiver_dicts

    @transact
    def create_dummy_receivers(self):
        from globaleaks.messages.dummy import base
        store = self.getStore()
        for receiver_dict in base.receiverDescriptionDicts:
            receiver = Receiver()
            receiver.receiver_id = receiver_dict['id']
            receiver.name = receiver_dict['name']
            receiver.description = receiver_dict['description']

            receiver.can_delete_submission = receiver_dict['can_delete_submission']
            receiver.can_postpone_expiration = receiver_dict['can_postpone_expiration']
            receiver.can_configure_delivery = receiver_dict['can_configure_delivery']
            receiver.can_configure_notification = receiver_dict['can_configure_notification']
            receiver.can_trigger_escalation = receiver_dict['can_trigger_escalation']

            receiver.languages_supported = receiver_dict['languages_supported']
            store.add(receiver)
            store.commit()
        store.close()
        return base.receiverDescriptionDicts

class ReceiverPreferences(TXModel):

    __storm_table__ = 'receiver_preferences'

    """
    Perhaps the various properties before need to be aggregated in a Pickle, and managed
    more easily with a function inside of PersonalPreference. Is in fact a bitmask.
    """

    id = Int(primary=True)
    receiver_gus = Unicode()
    notification_selected = Int()
    notification_fields = Pickle()
    delivery_selected = Int()
    delivery_fields = Pickle()
    creation_date = Date()
    last_access = Date()
    know_languages = Pickle()

    receiver_name = Unicode()
    receiver_description = Unicode()
    receiver_tags = Unicode()

    receiver_secret = RawStr()
    # receiver_secret would be a passphrase hash, we need to think that a receiver
    # may need to configure notification/delivery also if NO ONE tip is available
    # to him/her, and perhaps, this secret shall be used also as addictional
    # auth beside the Tip_GUS (this was a request of one of our adopters, btw)
    #   --- remind, API do not support that yet

    # receiver_properties = Pickle()
    can_delete_submission = Bool()
    can_postpone_expiration = Bool()
    can_configure_delivery = Bool()
    can_configure_notification = Bool()

    # escalation related fiels, if escalation is not configured, both are 0
    can_trigger_escalation = Int()
    # receiver_level, mean first or second level of receiver
    receiver_level = Int()

    context_followed = Pickle()
    # a receiver may stay in more than one contexts, this is because there are
    # not a reference between Context.id and this table

    @transact
    def update_language_mask(self):
        """
        for every contexts:
            select all the receivers in the context:
                sum the language, update the context
        """

    """
    * having some columns related the activity of the receiver
    * supports utility for store and manage boolean parameter (may be extended heavily, without having to change the db, and without having an huge amount of columns flags) -- receiver_properties Picke()
    * having two methods of extraction (commonly exposed receiver data, and private extraction)
    * supports module profile selection and configuration
    * maybe has sense create a table with the latest operation of the Receiver, this would be a nice information resume for the users
    """


