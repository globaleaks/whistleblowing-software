from storm.twisted.transact import transact
from storm.locals import *
from globaleaks.db import *
import pickle

# under the voce of "needlessy overcomplications", Twister + Storm
# http://twistedmatrix.com/users/radix/storm-api/storm.store.ResultSet.html

from globaleaks.db import getStore, transactor

__all__ = [ 'StoredData', 'Folders', 'Files', 'Comments', 'SpecialTip' ]

"""
Quick reference for the content:

    models:         TXModel
    tips:           StoredTips, Folders, Files, Comments, SpecialTip
    admin:          SytemSettings, Contexts, ModulesProfiles, ReceiversInfo, AdminStats, LocalizedTexts
    receiver:       PersonalPreference, ReceiverTip
    whistleblower:  Submission, PublicStats

"""


class StoredTip(TXModel):
    """
    Every tip has a certain shared data between all, and they are here collected, and
    this StoredTips.id is referenced by Folders, Files, Comments, and the derived Tips
    """
    __storm_table__ = 'storedtips'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, fields VARCHAR, "\
                   " creation_date DATETIME, pertinence_value INT,"\
                   " escalation_threshold INT, expire_time DATETIME, access_limit INT, download_limit INT)"

    id = Int(primary=True)
    fields = Pickle()
    pertinence_value = Int()
    escalation_trashold = Int()
    creation_date = Date()
    expire_date = Date()

        # the LIMITS are defined and declared *here*, and then
        # in the (Special|Receiver)Tip there are the view_count
        # in Folders(every Receiver has 1 to N folders), has the download_count
    access_limit = Int()
    download_limit = Int()

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

    def

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
                   " associated_receiver_id INT, property_applied VARCHAR, "
                   " upload_time DATETIME, storedtip_id INTEGER, downloaded_count INT, files_related VARCHAR)"

    id = Int(primary=True)
    folder_gus = Unicode()
    description = Unicode()
    property_applied = Pickle()
        # actually there are not property, but here would be marked if symmetric
        # asymmetric encryption has been used.
    upload_time = Date()
    downloaded_count = Int()
    files_related = Pickle()

    Reference(associated_receiver_id, Receiver.id)
        # associated_receiver_id is useful for show, in the general page of the
        # receiver, eventually the latest available folders
    Reference(storedtip_id, StoredTips.id)
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

    Reference(folder_id, Folder.id)

class Comment(TXModel):
    __storm_table__ = 'comments'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                  "(id INTEGER PRIMARY KEY, content VARCHAR, type VARCHAR,"\
                  " author VARCHAR, comment_date DATETIME, storedtip_id INT)"

    id = Int(primary=True)

    type = Unicode()
    content = Unicode()
    author = Unicode()
    comment_date = Date()

    Reference(storedtip_id, StoredTips.id)

class SpecialTip(TXModel):
    """
    SpecialTip is intended, at the moment, to provide a whistleblower access to the Tip.
    differently from the ReceiverTips, has a secret and/or authentication checks, has
    different capabilities, like: cannot not download, cannot express pertinence, and
    other operation permitted to the WB shall be configured by the Admin.

    SpecialTip contains some information, but the tip data returned to the WB, is
    composed by SpecialTip + Tip
    """
    __storm_table__ = 'specialtip'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, secret VARCHAR, view_count VARCHAR,"\
                   " last_access DATETIME )"

    id = Int(primary=True)

    """
    need to have a tip_US (unique string) ? may even not, in fact, in the 0.1 release
    we had used a tip_US just because was stored in the same table, but if we support
    a more complex auth system for the whistleblower, we want that WB come back
    to the tip only using this method, not using /tip/<t_US> like a receiver.

    This is the reason because here is not placed a t_US, but just a secret
    """

    secret = Pickle()
    view_count = Int()
    last_access = Date()


"""
The classic tip stay in receiver.ReceiverTip
"""
