from storm.twisted.transact import transact
from storm.locals import *
from globaleaks.db import *
import pickle

# under the voce of "needlessy overcomplications", Twister + Storm
# http://twistedmatrix.com/users/radix/storm-api/storm.store.ResultSet.html
from globaleaks.utils import idops

from globaleaks.models.base import TXModel
from globaleaks.models.admin import Context
from globaleaks.models.receiver import Receiver

__all__ = [ 'Folder', 'File', 'Comment',
            'InternalTip',  'ReceiverTip',
            'PublicStats']

class Folder(TXModel):
    """
    This represents a file set: a collection of files, description, time
    Every receiver has a different Folder, and if more folder exists, the
    number of folder is (R * Folder_N).
    This is the unique way we had to ensure end to end encryption WB-receiver,
    and if uncrypted situation, simply the Files referenced here are also
    referenced in the other Folders.
    """
    __storm_table__ = 'folders'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   " (id INTEGER PRIMARY KEY, folder_gus VARCHAR, description VARCHAR, "\
                   " associated_receiver_id INT, property_applied VARCHAR, "\
                   " upload_time DATETIME, internaltip_id INTEGER, "\
                   " downloaded_count INT, files_related VARCHAR)"

    id = Int(primary=True)
    folder_gus = Unicode()
    description = Unicode()
    property_applied = Pickle()
    # actually there are not property, but here would be marked if symmetric
    # asymmetric encryption has been used.

    upload_time = Date()
    downloaded_count = Int()
    files_related = Pickle()

    associated_receiver_id = Int()
    associated_receiver = Reference(associated_receiver_id, Receiver.id)
    # associated_receiver_id is useful for show, in the general page of the
    # receiver, eventually the latest available folders

    # XXX do we actually need this? Folder will always be instantiated from
    # internaltip, I do not think it will happend vice versa.
    #internaltip = Reference(internaltip_id, InternalTip.id)

    internaltip_id = Int()

    # is associated to the ORM.id, not to the tip_uniq_ID, eventually,
    # having the Folder.folder_id can be shared and downloaded by
    # someone that has not access to the Tip


class File(TXModel):
    """
    The file are *stored* here, along with their properties
    """
    __storm_table__ = 'files'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                  "(id INTEGER PRIMARY KEY, filename VARCHAR, filecontent VARCHAR, description VARCHAR, "\
                  " content_type VARCHAR, size INT, metadata_cleaned BOOL, uploaded_date DATETIME, folder_id INTEGER," \
                  " hash VARCHAR)"

    id = Int(primary=True)
    filename = Unicode()
    filecontent = RawStr()
    hash = RawStr()
    description = Unicode()
    content_type = Unicode()
    size = Int()
    metadata_cleaned = Bool()
    uploaded_date = Date()

    folder_id = Int()
    folder = Reference(folder_id, Folder.id)

class Comment(TXModel):
    __storm_table__ = 'comments'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                  "(id INTEGER PRIMARY KEY, content VARCHAR, type VARCHAR,"\
                  " author VARCHAR, comment_date DATETIME, internaltip_id INT)"

    id = Int(primary=True)

    type = Unicode()
    content = Unicode()
    author = Unicode()
    comment_date = Date()

    internaltip_id = Int()
    #internaltip = Reference(internaltip_id, InternalTip.id)


class InternalTip(TXModel):
    """
    This is the internal representation of a Tip that has been submitted to the
    GlobaLeaks node.
    It has a one-to-many association with the individual Tips of every receiver
    and whistleblower.

    Every tip has a certain shared data between all, and they are here collected, and
    this StoredTip.id is referenced by Folders, Files, Comments, and the derived Tips
    """
    __storm_table__ = 'internaltips'

    id = Int(primary=True)
    fields = Pickle()

    pertinence_value = Int()
    escalation_threshold = Int()

    comments = Pickle()
    pertinence = Int()

    creation_date = Date()
    expiration_date = Date()

    # the LIMITS are defined and declared *here*, and then
    # in the (Special|Receiver)Tip there are the view_count
    # in Folders(every Receiver has 1 to N folders), has the download_count
    access_limit = Int()
    download_limit = Int()

    file_id = Int()

    folders = ReferenceSet(id, Folder.internaltip_id)
    comments = ReferenceSet(id, Comment.internaltip_id)

    context_id = Unicode()
    context = Reference(context_id, Context.context_id)


    def postpone_expiration(self):
        """
        function called when a receiver has this option
        """

    def tip_total_delete(self):
        """
        function called when a receiver choose to remove a submission
        and all the derived tips. is called by scheduler when
        timeoftheday is >= expired_date
        """


class Tip(TXModel):
    __storm_table__ = 'tips'

    id = Int(primary=True)

    type = Unicode()
    address = Unicode()
    password = Unicode()

    internaltip_id = Int()
    internaltip = Reference(internaltip_id, InternalTip.id)

    @transact
    def internaltip_get(self):
        store = self.getStore()
        the_one = store.find(InternalTip, InternalTip.id == self.internaltip_id).one()
        store.commit()
        store.close()
        return the_one

    def get_sub_index(self):
        print self.internaltip
        ret = {
        #"notification_adopted": unicode,
        #"delivery_adopted": unicode,
        "download_limit": self.internaltip.download_limit,
        # remind: download_performed is inside the folderDict
        "access_limit": self.internaltip.access_limit,
        #"access_performed": self.,
        "expiration_date": self.internaltip.expiration_date,
        "creation_date": self.internaltip.creation_date,
        #"last_update_date": self.internaltip.last_update_date,
        "comment_number": len(list(self.internaltip.comments)),
        "folder_number": len(list(self.internaltip.folders)),
        "overall_pertinence": self.internaltip.pertinence
        }
        return ret

    @transact
    def lookup(self, receipt):
        store = self.getStore()

        tip = store.find(Tip, Tip.address == receipt).one()
        tip_sub_index = tip.get_sub_index()

        folders = tip.internaltip.folders

        comments = tip.internaltip.comments
        context = tip.internaltip.context_id

        receiver_dicts = tip.internaltip.context.list_receiver_dicts()

        tip_details = {'tip': tip_sub_index,
                   'fields': tip.internaltip.fields,
                   'folders': None,#folders,
                   'comments': None, #comments,
                   'context': context,
                   'receivers': receiver_dicts
        }
        print tip_details
        store.commit()
        store.close()

        return tip_details

class ReceiverTip(Tip):
    """
    This is the table keeping track of ALL the receivers activities and
    date in a Tip, Tip core data are stored in StoredTip. The data here
    provide accountability of Receiver accesses, operations, options.
    """
    notification_date = Date()
    authoptions = Pickle()
    # remind: here we can make a password checks, PersonalPreference has a
    # stored hash of the actual password. when Receiver change a password, do not change
    # in explicit way also the single Tips password.

    total_view_count = Int()
    total_download_count = Int()
    relative_view_count = Int()
    relative_download_count = Int()

    last_access = Date()
    pertinence_vote = Int()

    def new(self):
        self.total_view_count = 0
        self.total_view_count = 0
        self.relative_view_count = 0
        self.relative_download_count = 0

        self.authoptions = {}

        self.address = idops.random_tip_id()
        #self.password =
        self.type = u'receiver'

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



class WhistleblowerTip(Tip):
    """
    SpecialTip is intended, at the moment, to provide a whistleblower access to the Tip.
    differently from the ReceiverTips, has a secret and/or authentication checks, has
    different capabilities, like: cannot not download, cannot express pertinence, and
    other operation permitted to the WB shall be configured by the Admin.

    SpecialTip contains some information, but the tip data returned to the WB, is
    composed by SpecialTip + Tip
    """

    """
    need to have a tip_US (unique string) ? may even not, in fact, in the 0.1 release
    we had used a tip_US just because was stored in the same table, but if we support
    a more complex auth system for the whistleblower, we want that WB come back
    to the tip only using this method, not using /tip/<t_US> like a receiver.

    This is the reason because here is not placed a t_US, but just a secret
    """

    secret = Pickle()

    # XXX we probably don't want to store this stuff for the WB receipt.
    #     we may just want to store the last_access count, but properly
    #     anonymize it, like only store the fact that they logged in in the
    #     last week. So store just a week number.
    #view_count = Int()
    #last_access = Date()


class PublicStats(TXModel):
    """
    * Follow the same logic of admin.AdminStats,
    * need to be organized along with the information that we want to shared to the WBs:
       *  active_submission represent the amount of submission active in the moment
       *  node activities is a sum of admin + receiver operation
    * that's all time dependent information
       * remind: maybe also non-time dependent information would exists, if a node want to publish also their own analyzed submission, (but this would require another db table)
    """
    __storm_table__ = 'publicstats'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, active_submissions INT, node_activities INT, uptime INT"

    id = Int(primary=True)

    active_submissions = Int()
    node_activities = Int()
    uptime = Int()
    """
    likely would be expanded, but avoiding to spread information that may lead an attacker advantaged
    """


"""
The classic tip stay in receiver.ReceiverTip
"""
