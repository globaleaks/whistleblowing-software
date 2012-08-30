from storm.twisted.transact import transact
from storm.locals import *

from globaleaks.db import getStore, transactor

__all__ = ['InternalTip', 'Folder',
           'File', 'Tip','ReceiverTip',
           'Submission', 'Node', 'Receiver']

class TXModel(object):
    """
    This is the model to be subclassed for having the DB operations be done on
    storm ORM.

    The methods that should be run on the Storm ORM should be decorated with
    @transact. Be sure *not* to return any reference to Storm objects, these
    where retrieved in a different thread and cannot exit the matrix.
    """
    createQuery = ""
    transactor = transactor

    @transact
    def createTable(self):
        store = getStore()
        store.execute(self.createQuery)
        store.commit()

    @transact
    def save(self):
        store = getStore()
        store.add(self)
        store.commit()


class Submission(TXModel):
    """
    This represents a temporary submission. Submissions should be stored here
    until they are transformed into a Tip.
    """
    __storm_table__ = 'submission'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, temporary_id INTEGER, fields VARCHAR, "\
                   " created VARCHAR)"

    id = Int(primary=True)

    temporary_id = Int()

    fields = Pickle()
    created = Date()

class File(TXModel):
    """
    Represents a file: a file.
    """
    __storm_table__ = 'file'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, location VARCHAR, description VARCHAR, "\
                   " folder_id INTEGER)"

    id = Int(primary=True)

    location = Unicode()
    description = Unicode()

    folder_id = Int()

    #folder = Reference(folder_id, Folder.id)

class Folder(TXModel):
    """
    This represents a file set: a collection of files.
    """
    __storm_table__ = 'folder'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, description VARCHAR, "\
                   " internaltip_id INTEGER)"

    id = Int(primary=True)
    description = Unicode()

    internaltip_id = Int()

    #tip = Reference(internaltip_id, InternalTip.id)
    files = ReferenceSet(id, File.folder_id)

class InternalTip(TXModel):
    """
    This is the internal representation of a Tip that has been submitted to the
    GlobaLeaks node.
    It has a one-to-many association with the individual Tips of every receiver
    and whistleblower.
    """
    __storm_table__ = 'internaltip'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, fields VARCHAR, comments VARCHAR,"\
                   " pertinence INTEGER, expires VARCHAR, file_id INT)"

    id = Int(primary=True)

    fields = Pickle()
    comments = Pickle()
    pertinence = Int()
    expires = Date()

    file_id = Int()

    # Folders associated with the submission
    folders = ReferenceSet(id, Folder.internaltip_id)

    # Tips associated with this InternalTip
    # children = ReferenceSet(id, Tip.internaltip_id)

    def __repr__(self):
        return "<InternalTip: (%s, %s, %s, %s, %s)" % (self.fields, \
                self.file, self.comments, self.pertinence, \
                self.expires)

class Tip(TXModel):
    __storm_table__ = 'tip'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, address VARCHAR, password VARCHAR,"\
                   " type INTEGER, internaltip_id INTEGER, total_view_count INTEGER, "\
                   " total_download_count INTEGER, relative_view_count INTEGER, "\
                   " relative_download_count INTEGER)"

    id = Int(primary=True)

    type = Int()
    address = Unicode()
    password = Unicode()

    internaltip_id = Int()
    internaltip = Reference(internaltip_id, InternalTip.id)

class ReceiverTip(Tip):
    total_view_count = Int()
    total_download_count = Int()
    relative_view_count = Int()
    relative_download_count = Int()

class Node(TXModel):
    __storm_table__ = 'node'

    id = Int(primary=True)

    context = Pickle()
    statistics = Pickle()
    properties = Pickle()
    description = Unicode()
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()

class Receiver(TXModel):
    __storm_table = 'receivers'

    public_name = Unicode()
    private_name = Unicode()


