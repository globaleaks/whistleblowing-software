import json

from twisted.internet.defer import returnValue

from storm.twisted.transact import transact
from storm.locals import *
import pickle

# under the voce of "needlessy overcomplications", Twister + Storm
# http://twistedmatrix.com/users/radix/storm-api/storm.store.ResultSet.html

from globaleaks.db import getStore, transactor, database

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

    When you decorate object methods with @transact be sure to also set the
    transactor attribute to that of a working transactor.
    """
    createQuery = ""
    transactor = transactor
    database = database

    def getStore(self):
        store = Store(self.database)
        return store

    @transact
    def createTable(self):
        store = self.getStore()
        store.execute(self.createQuery)
        store.commit()
        store.close()

    @transact
    def save(self):
        store = self.getStore()
        store.add(self)
        store.commit()
        store.close()

class Submission(TXModel):
    """
    This represents a temporary submission. Submissions should be stored here
    until they are transformed into a Tip.
    """
    __storm_table__ = 'submission'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, submission_id VARCHAR, fields VARCHAR, "\
                   " opening_date DATETIME, receivers VARCHAR, folder_id INTEGER)"
    id = Int(primary=True)
    submission_id = Unicode() # Int()
    folder_id = Int()
    fields = Pickle()
    receivers = Pickle()
    opening_date = Date()

    @transact
    def status(self, submission_id):
        store = self.getStore()
        s = store.find(Submission, Submission.submission_id==submission_id).one()

        status = {'receivers_selected': s.receivers,
                  'fields': s.fields}

        store.commit()
        store.close()
        return status

    @transact
    def create_tips(self, submission_id, receipt):
        store = self.getStore()
        s = store.find(Submission, Submission.submission_id==submission_id).one()

        internal_tip = InternalTip()
        internal_tip.fields = s.fields
        store.add(internal_tip)

        whistleblower_tip = Tip()
        whistleblower_tip.internal_tip_id = internal_tip.id
        whistleblower_tip.address = receipt
        store.add(whistleblower_tip)

        # XXX lookup the list of receivers and create their tips too.
        print "Receivers!"
        for receiver in s.receivers:
            print receiver
        # Delete the temporary submission
        store.remove(s)

        store.commit()
        store.close()

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

    @transact
    def internaltip_get(self):
        store = self.getStore()
        the_one = store.find(InternalTip, InternalTip.id == self.internaltip_id).one()
        store.commit()
        store.close()
        return the_one

class ReceiverTip(Tip):
    total_view_count = Int()
    total_download_count = Int()
    relative_view_count = Int()
    relative_download_count = Int()

    @transact
    def create(self, receiver_id):
        store = self.getStore()

        receiver = store.find(Receiver, Receiver.receiver_id==receiver_id)


class ReceiverContext(TXModel):
    __storm_table__ = 'receivers_context'

    __storm_primary__ = "context_id", "receiver_id"

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(context_id INTEGER, receiver_id INTEGER "\
                   " PRIMARY KEY (context_id, receiver_id) "\
                   ")"

    context_id = Int()
    receiver_id = Int()


class Receiver(TXModel):
    __storm_table__ = 'receivers'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, receiver_id VARCHAR,"\
                   " receiver_name VARCHAR, "\
                   " receiver_description VARCHAR, receiver_tags VARCHAR, "\
                   " creation_date VARCHAR, last_update_date VARCHAR, "\
                   " languages_supported VARCHAR, can_delete_submission INT, "\
                   " can_postpone_expiration INT, can_configure_delivery INT, "\
                   " can_configure_notification INT, can_trigger_escalation INT, "\
                   " receiver_level INT)"

    id = Int(primary=True)

    receiver_id = Unicode()
    receiver_name = Unicode()
    receiver_description = Unicode()
    receiver_tags = Unicode()

    creation_date = Date()
    last_update_date = Date()

    languages_supported = Pickle()

    can_delete_submission = Bool()
    can_postpone_expiration = Bool()
    can_configure_delivery = Bool()
    can_configure_notification = Bool()

    can_trigger_escalation = Bool()

    receiver_level = Int()

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
        from globaleaks.messages.dummy import shared
        store = self.getStore()

        for receiver_dict in shared.receiverDescriptionDicts:
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
        return shared.receiverDescriptionDicts

class Context(TXModel):
    __storm_table__ = 'contexts'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, node_id INT,"\
                   " contexts VARCHAR, description VARCHAR, "\
                   " fields VARCHAR, selectable_receiver INT, "\
                   " receivers VARCHAR, escalation_threshold INT, "\
                   " languages_supported VARCHAR)"

    id = Int(primary=True)

    node_id = Int()
    context_id = Unicode()

    name = Unicode()
    description = Unicode()
    fields = Pickle()
    selectable_receiver = Bool()

    escalation_threshold = Int()
    languages_supported = Pickle()

Context.receivers = ReferenceSet(Context.id,
                                 ReceiverContext.context_id,
                                 ReceiverContext.receiver_id,
                                 Receiver.id)
class Node(TXModel):
    __storm_table__ = 'node'

    createQuery = "CREATE TABLE " + __storm_table__ +\
                   "(id INTEGER PRIMARY KEY, contexts VARCHAR,"\
                   " properties VARCHAR, description VARCHAR, "\
                   " name VARCHAR, public_site VARCHAR, "\
                   " hidden_service VARCHAR)"

    id = Int(primary=True)

    statistics = Pickle()
    properties = Pickle()
    description = Unicode()
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()

    @transact
    def list_contexts(self):
        pass

Node.contexts = ReferenceSet(Node.id, Context.node_id)

"""
Triva, this file implement the 0.2 version of GlobaLeaks, then:
Enter the Ginger - http://www.youtube.com/watch?v=uUD9NBSJvqo
"""
