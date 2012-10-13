from storm.twisted.transact import transact
from storm.locals import *


"""
Quick reference for the content:

    models:         TXModel
    tips:           StoredTips, Folders, Files, Comments, SpecialTip
    admin:          SytemSettings, Contexts, ModulesProfiles, AdminStats, LocalizedTexts
    receiver:       PersonalPreference, ReceiverTip
    whistleblower:  Submission, PublicStats

"""


class PersonalPreference(TXModel):

    __storm_table__ = 'receiverpref'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                  "(id INTEGER PRIMARY KEY, receiver_gus VARCHAR, notification_selected INT," \
                  " notification_fields VARCHAR, delivery_selected INT, delivery_fields VARCHAR, " \
                  " creation_date DATETIME, last_access DATETIME, know_languages VARCHAR, "\
                  " receiver_name VARCHAR, receiver_description VARCHAR, receiver_tags VARCHAR, "\
                  " receiver_level INT, receiver_properties VARCHAR, can_delete_submission BOOL, "\
                  " can_postpone_expiration BOOL, can_configure_delivery BOOL, receiver_secret VARCHAR"\
                  " can_configure_notification BOOL, can_trigger_escalation BOOL, contexts_followed VARCHAR)"

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

class ReceiverTip(TXModel):
    """
    This is the table keeping track of ALL the receivers activities and
    date in a Tip, Tip core data are stored in StoredTip. The data here
    provide accountability of Receiver accesses, operations, options.
    """
    __storm_table__ = 'receivertip'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                  "(INTEGER PRIMARY KEY, submission_gus VARCHAR, authoptions VARCHAR, notification_date DATETIME, "\
                  " view_count INTEGER, last_access DATETIME, pertinence_vote INTEGER, "\
                  " storedtip_id INTEGER)"

    submission_gus = Unicode()
    notification_date = Date()
    authoptions = Pickle()
        # remind: here we can make a password checks, PersonalPreference has a
        # stored hash of the actual password. when Receiver change a password, do not change
        # in explicit way also the single Tips password.
    view_count = Int()
    last_access = Date()
    pertinence_vote = Int()

    Reference(storedtip_id, StoredTips.id)

    """
    this method has not yet reviewed during the refactor, also the method below, receiver_dicts
    """
    @transact
    def create(self, internaltip, receiver_id):
        store = self.getStore()

        receiver = store.find(Receiver, Receiver.receiver_id==receiver_id)

        tip = ReceiverTip()
        tip.internaltip = internaltip
        store.add(tip)

        store.commit()
        store.close()


    """
    @transact
    def receiver_dicts(self):
        store = self.getStore()

        receiver_dicts = []

        for receiver in store.find(Receiver):
            receiver_dict = {}
            receiver_dict['receiver_id'] = receiver.receiver_id
            receiver_dict['receiver_name'] = receiver.receiver_name
            receiver_dict['receiver_description'] = receiver.receiver_description

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
            receiver.receiver_id = receiver_dict['receiver_id']
            receiver.receiver_name = receiver_dict['receiver_name']
            receiver.receiver_description = receiver_dict['receiver_description']

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
        """



