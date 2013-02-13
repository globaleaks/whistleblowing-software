from random import randint
from storm.locals import ReferenceSet
from storm.locals import *

from globaleaks.settings import config

from time import time
# xxx. we should use python tz.
from datetime import datetime
now = datetime.utcnow

def uuid():
    import uuid
    return unicode(uuid.uuid4())

def update_model(obj, update_dict):
    for key, value in update_dict.iteritems():
         setattr(obj, key, value)

class Model(Storm):
    """
    Base class for working the database
    """
    id = Unicode(primary=True, default_factory=uuid)
    # Note on creation last_update and last_access may be out of sync by some
    # seconds.
    creation_date = DateTime(default_factory=now)

    def __new__(cls, *args, **kw):
        cls.__storm_table__ = cls.__name__.lower()
        # maybe check here for attrs validation, and eventually return None

        return Storm.__new__(cls, *args, **kw)

    def __init__(self, attrs={}):
        for key, value in attrs.iteritems():
            if isinstance(value, str):
                value = unicode(value)
            setattr(self, key, value)

    def dict(self, filter=None):
        """
        return a dictionary serialization of the current model.
        if no filter is provided, returns every single attribute.
        """
        if not filter:
            filter = [x for x in vars(Model) if isinstance(x, types.MethodType)]

        return dict((key, getattr(self, key)) for key in filter)





class Context(Model):
    name = Unicode()
    description = Unicode()
    fields = Pickle()

    languages_supported = Pickle()

    selectable_receiver = Bool()
    escalation_threshold = Int()

    tip_max_access = Int()
    tip_timetolive = Int()
    file_max_download = Int()

    last_update = DateTime()

    # receivers = ReferenceSet("Context.id", "Receiver.context_id")


class InternalTip(Model):
    """
    This is the internal representation of a Tip that has been submitted to the
    GlobaLeaks node.

    It has a not associated map for keep track of Receivers, Tips, Folders,
    Comments and WhistleblowerTip.
    All of those element has a Storm Reference with the InternalTip.id,
    never vice-versa
    """
    fields = Pickle()
    pertinence_counter = Int()
    creation_date = DateTime()
    expiration_date = DateTime()
    last_activity = DateTime()

    # the LIMITS are stored in InternalTip because and admin may
    # need change them. These values are copied by Context
    escalation_threshold = Int()
    access_limit = Int()
    download_limit = Int()

    mark = Unicode()

    receivers = Pickle()

    files = Pickle()

    context_gus = Unicode()
    context = Reference(context_gus, "Context.context_gus")

    whistleblower_tip_id = Unicode()
    whistleblower_tip = Reference(whistleblower_tip_id, "WhistleblowerTip.id")

    # comments = ReferenceSet("InternalTip.id", "Comment.internaltip_id")
    # folders = ReferenceSet("InternalTip.id", "Folder.internaltip_id")

    _marker = [ u'incomplete', u'new', u'first', u'second' ]


class ReceiverTip(Model):
    """
    This is the table keeping track of ALL the receivers activities and
    date in a Tip, Tip core data are stored in StoredTip. The data here
    provide accountability of Receiver accesses, operations, options.
    """
    internaltip_id = Unicode()
    internaltip = Reference(internaltip_id, InternalTip.id)

    access_counter = Int()
    last_access = DateTime()

    expressed_pertinence = Int()

    receiver_id = Unicode()
    receiver = Reference(receiver_id, "Receiver.id")

    notification_date = DateTime()
    notification_mark = Unicode()

    last_access = DateTime(default_factory=now)

    _marker = [ u'not notified', u'notified', u'unable to notify', u'notification ignore' ]

    # receiver_files = ReferenceSet(ReceiverTip.id, ReceiverFile.receiver_tip_id)


class WhistleblowerTip(Model):
    """
    WhisteleblowerTip is intended, to provide a whistleblower access to the Tip.
    Has ome differencies from the ReceiverTips: has a secret authentication checks, has
    different capabilities, like: cannot not download, cannot express pertinence.
    """
    receipt = Unicode()

    last_access = DateTime()
    access_counter = Int()

    internaltip_id = Unicode()
    internaltip = Reference(internaltip_id, "InternalTip.id")

class ReceiverFile(Model):
    file_path = RawStr()
    downloads = Int()

    last_access = DateTime()

    internal_file_id = Unicode()
    internal_file = Reference(internal_file_id, "InternalFile.id")

    receiver_tip_id = Unicode()

class Folder(Model):
    internaltip_id = Unicode()
    # files = ReferenceSet("Folder.id", "InternalFile.folder_id")

class InternalFile(Model):
    """
    The file are *stored* here, along with their properties
    """
    name = Unicode()
    sha2sum = Unicode()

    description = Unicode()
    content_type = Unicode()
    mark = Unicode()
    size = Int()

    folder_id = Unicode()

    _marker = [ u'not processed', u'ready', u'blocked', u'stored' ]

class Comment(Model):
    """
    This table handle the comment collection, has an InternalTip referenced
    """
    internaltip_id = Unicode()

    author = Unicode()
    message = Unicode()

    notification_mark = Unicode()

    _marker = [ u'not notified', u'notified', u'unable to notify', u'notification ignored' ]

class Node(Model):
    """
    This table has only one instance, has the "id", but would not exists a second element
    of this table. This table acts, more or less, like the configuration file of the previous
    GlobaLeaks release (and some of the GL 0.1 details are specified in Context)

    This table represent the System-wide settings
    """
    description = Unicode()
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    languages = Pickle()
    creation_time = DateTime()
    notification_settings = Pickle()
    password = Unicode()

    # Here is set the time frame for the stats publicly exported by the node.
    # Expressed in hours
    stats_update_time = Int()

class Receiver(Model):
    """
    Receiver description model, some Receiver dependent information are
    also in globaleaks.models.plugin ReceiverConfs table
    """
    # Those four variable can be changed by the Receiver
    name = Unicode()
    description = Unicode()

    # Authentication variables
    username = Unicode()
    password = Unicode()

    # notification_variable
    notification_fields = Pickle()

    # Admin choosen options
    can_delete_submission = Bool()
    can_postpone_expiration = Bool()
    can_configure_delivery = Bool()
    can_configure_notification = Bool()

    # receiver_tier = 1 or 2. Mean being part of the first or second level
    # of receivers body. if threshold is configured in the context. default 1
    receiver_level = Int()

    # tips = ReferenceSet("Receiver.id", "ReceiverTip.receiver_id")
    context_id = Unicode()

    last_update = DateTime()
    last_access = DateTime(default_factory=now)
    # contexts = ReferenceSet("Context.id",
    #                         "ReceiverContext.context_id",
    #                         "ReceiverContext.receiver_id",
    #                         "Receiver.id")

class ReceiverContext(Model):
    context_id = Unicode()
    receiver_id = Unicode()


Context.receivers = ReferenceSet(Context.id, Receiver.context_id)

InternalTip.comments = ReferenceSet(InternalTip.id, Comment.internaltip_id)
InternalTip.folders = ReferenceSet(InternalTip.id, Folder.internaltip_id)
ReceiverTip.receiver_files = ReferenceSet(
                        ReceiverTip.id,
                        ReceiverFile.receiver_tip_id)
Receiver.tips = ReferenceSet(
                        Receiver.id,
                        ReceiverTip.receiver_id)
Receiver.contexts = ReferenceSet(
                        Context.id,
                        ReceiverContext.context_id,
                        ReceiverContext.receiver_id,
                        Receiver.id)

Folder.files = ReferenceSet(Folder.id, InternalFile.folder_id)

models = [Node, Context, ReceiverTip, WhistleblowerTip, Comment, InternalTip,
          Receiver, InternalFile, Folder]
