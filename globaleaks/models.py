# -*- coding: UTF-8
#   config
#   ******
#
# GlobaLeaks ORM Models definition

import types

from storm.locals import Bool, DateTime, Int, Pickle, Reference, ReferenceSet, Unicode, Storm
from globaleaks.settings import GLSetting
from globaleaks.rest import errors
from globaleaks.utils import datetime_now
from globaleaks import LANGUAGES_SUPPORTED_CODES


def uuid():
    """
    Generated an UUID used in GlobaLeaks ORM models
    """
    import uuid as u
    return unicode(u.uuid4())

def gltextv(self, attr, value):
    """
    Just to avoid resources depletion by anonymous submissions,
    a simple validation that should make the exhaustion slower.
    """
    try:
        assert isinstance(value, unicode)
    except AssertionError:
        raise errors.InvalidInputFormat("Not an unicode as expected (%s = %s)" %
                        (attr, value))

    if (attr == 'name' and
        (len(value) > GLSetting.memory_copy.maximum_namesize or len(value) == 0)):
        raise errors.InvalidInputFormat("name length need to be > 0 and " \
                            "< of %d" % GLSetting.memory_copy.maximum_namesize)
    # TODO this at the moment is not used again, because need to be moved on gllocalv
    elif attr == 'description' and len(value) > GLSetting.memory_copy.maximum_descsize:
        raise errors.InvalidInputFormat("unicode description has a length " \
                            "limit of %d" % GLSetting.memory_copy.maximum_descsize)
    else:
        if len(value) > GLSetting.memory_copy.maximum_textsize:
            raise errors.InvalidInputFormat("unicode in %s overcome length " \
                            "limit %d" % (attr, GLSetting.memory_copy.maximum_textsize))

    return value

def gldictv(self, attr, value):
    """
    Validate dict content, every key, if unicode, have not to
    overcome the generic length limit.
    """
    if not value:
        return {}

    try:
        assert isinstance(value, dict)
    except AssertionError:
        raise errors.InvalidInputFormat("(%s) dict expected" % attr)


    for key, subvalue in value.iteritems():
        if isinstance(subvalue, unicode):
            if len(subvalue) > GLSetting.memory_copy.maximum_textsize:
                raise errors.InvalidInputFormat("In dict %s the key %s" \
                                "overcome length limit of %d" % (attr, key,
                                GLSetting.memory_copy.maximum_textsize))

    return value


def gllocalv(self, attr, value):
    """
    Validate a dict containing
    """
    try:
        assert isinstance(value, dict)
    except AssertionError:
        raise errors.InvalidInputFormat("(%s) localized dict expected" % attr)

    if not value:
        return value

    for lang, text in value.iteritems():
        if lang not in LANGUAGES_SUPPORTED_CODES:
            raise errors.InvalidInputFormat("(%s) invalid language code in %s" % (lang, attr) )

    return value


class Model(Storm):
    """
    Base class for working the database
    """
    id = Unicode(primary=True, default_factory=uuid)
    creation_date = DateTime(default_factory=datetime_now)
    # Note on creation last_update and last_access may be out of sync by some
    # seconds.

    # initialize empty list for the base classes
    unicode_keys = [ ]
    localized_strings = [ ]
    int_keys = [ ]
    bool_keys = [ ]

    def __init__(self, attrs=None):

        if attrs is not None:
            self.update(attrs)

    def __new__(cls, *args, **kw):
        cls.__storm_table__ = cls.__name__.lower()
        # maybe check here for attrs validation, and eventually return None

        return Storm.__new__(cls, *args)

    def update(self, attrs=None):
        """
        Updated Models attributes based on attrs dictionary
        """
        # May raise ValueError and AttributeError
        if attrs is None:
            return

        # Dev note: these fields describe which key are expected in the
        # constructor. if not available, an error is raise.
        # other elements different from bool, unicode and int, can't be
        # processed by the generic "update" method and need to be assigned
        # to the object, [ but before commit(), if they are NOT NULL in the
        # SQL file ]
        cls_unicode_keys = getattr(self, "unicode_keys")
        cls_int_keys = getattr(self, "int_keys")
        cls_bool_keys = getattr(self, "bool_keys")
        cls_localized_keys = getattr(self, "localized_strings")

        for k in cls_unicode_keys:
            value = unicode(attrs[k])
            setattr(self, k, value)

        for k in cls_int_keys:
            value = int(attrs[k])
            setattr(self, k, value)

        for k in cls_bool_keys:
            if attrs[k] == 'true' or attrs[k] == u'true':
                value = True
            elif attrs[k] == 'false' or attrs[k] == u'false':
                value = False
            else:
                value = bool(attrs[k])
            setattr(self, k, value)

        for k in cls_localized_keys:
            value = attrs[k]
            setattr(self, k, value)
            # value is a list with { lang: 'en', 'text': "shit" },
            #                      { lang: 'mi', 'text': "leganord" }
            # print "checking %s on %s" % (k, value)
            # if len(k) > 0:
            #     if value[0].has_key('lang') and value[0].has_key('text'):
            #         setattr(self, k, value)
            #     else:
            #         raise ValueError("Invalid keys in %s" % k)
            # else:
            #     raise ValueError("Missing translated dict in %s" % k)


    def __repr___(self):
        attrs = ['%s=%s' % (attr, getattr(self, attr))
                 for attr in vars(Model)
                 if isinstance(attr, types.MethodType)]
        return '<%s model with values %s>' % (self.__name__, ', '.join(attrs))

    def __setattr__(self, name, value):
        # harder better faster stronger
        if isinstance(value, str):
            value = unicode(value)

        return Storm.__setattr__(self, name, value)

    def dict(self, dict_filter=None):
        """
        return a dictionary serialization of the current model.
        if no filter is provided, returns every single attribute.
        """
        if dict_filter is None:
            dict_filter = [x for x in vars(Model) if isinstance(x, types.MethodType)]

        return dict((key, getattr(self, key)) for key in filter)


class User(Model):
    """
    This model keeps track of globaleaks users
    """
    __storm_table__ = 'user'

    username = Unicode()
    password = Unicode()
    salt = Unicode()
    role = Unicode()
    state = Unicode()
    last_login = DateTime()
    failed_login_count = Int()
 
    _roles = [ u'admin', u'receiver' ]
    _states = [ u'disabled', u'to_be_activated', u'enabled']

    unicode_keys = [ 'username', 'password', 'salt', 'role', 'state' ]
    int_keys = [ 'failed_login_count' ]


class Context(Model):
    """
    This model keeps track of specific contexts settings
    """
    __storm_table__ = 'context'

    # Unique fields is a dict with a unique ID as key,
    # and as value another dict, containing the field
    # descriptive values:
    # "presentation_order" : int
    # "preview" : bool
    # "required" : bool
    # "type" : unicode
    # "options" : dict (optional!)
    unique_fields = Pickle()

    # Localized fields is a dict having as keys, the same
    # keys of unique_fields, and as value a dict, containing:
    # 'name' : unicode
    # 'hint' : unicode
    localized_fields = Pickle()

    selectable_receiver = Bool()
    escalation_threshold = Int()

    tip_max_access = Int()
    file_max_download = Int()
    file_required = Bool()
    tip_timetolive = Int()
    submission_timetolive = Int()
    receipt_regexp = Unicode()
    last_update = DateTime()
    file_required = Bool()
    tags = Pickle()

    # localized stuff
    name = Pickle(validator=gllocalv)
    description = Pickle(validator=gllocalv)
    receipt_description = Pickle(validator=gllocalv)
    submission_introduction = Pickle(validator=gllocalv)
    submission_disclaimer = Pickle(validator=gllocalv)

    #receivers = ReferenceSet(
    #                         Context.id,
    #                         ReceiverContext.context_id,
    #                         ReceiverContext.receiver_id,
    #                         Receiver.id)

    select_all_receivers = Bool()

    unicode_keys = [ 'receipt_regexp' ]
    localized_strings = ['name', 'description', 'receipt_description',
                    'submission_introduction', 'submission_disclaimer' ]
    int_keys = [ 'escalation_threshold', 'tip_max_access', 'file_max_download' ]
    bool_keys = [ 'selectable_receiver', 'file_required', 'select_all_receivers' ]


class InternalTip(Model):
    """
    This is the internal representation of a Tip that has been submitted to the
    GlobaLeaks node.

    It has a not associated map for keep track of Receivers, Tips,
    Comments and WhistleblowerTip.
    All of those element has a Storm Reference with the InternalTip.id,
    never vice-versa
    """
    __storm_table__ = 'internaltip'

    context_id = Unicode()
    #context = Reference(InternalTip.context_id, Context.id)
    #comments = ReferenceSet(InternalTip.id, Comment.internaltip_id)
    #receivertips = ReferenceSet(InternalTip.id, ReceiverTip.internaltip_id)
    #internalfiles = ReferenceSet(InternalTip.id, InternalFile.internaltip_id)
    #receivers = ReferenceSet(InternalTip.id, Receiver.id)

    wb_fields = Pickle(validator=gldictv)
    pertinence_counter = Int()
    expiration_date = DateTime()
    last_activity = DateTime()

    # the LIMITS are stored in InternalTip because and admin may
    # need change them. These values are copied by Context
    escalation_threshold = Int()
    access_limit = Int()
    download_limit = Int()

    mark = Unicode()

    _marker = [ u'submission', u'finalize', u'first', u'second' ]
    ## NO *_keys = It's created without initializing dict


class ReceiverTip(Model):
    """
    This is the table keeping track of ALL the receivers activities and
    date in a Tip, Tip core data are stored in StoredTip. The data here
    provide accountability of Receiver accesses, operations, options.
    """
    __storm_table__ = 'receivertip'

    internaltip_id = Unicode()
    receiver_id = Unicode()
    #internaltip = Reference(ReceiverTip.internaltip_id, InternalTip.id)
    #receiver = Reference(ReceiverTip.receiver_id, Receiver.id)

    last_access = DateTime(default_factory=datetime_now)
    access_counter = Int()
    expressed_pertinence = Int()
    notification_date = DateTime()
    mark = Unicode()

    _marker = [ u'not notified', u'notified', u'unable to notify', u'disabled', u'skipped' ]

    ## NO *_keys = It's created without initializing dict

class WhistleblowerTip(Model):
    """
    WhisteleblowerTip is intended, to provide a whistleblower access to the Tip.
    Has ome differencies from the ReceiverTips: has a secret authentication checks, has
    different capabilities, like: cannot not download, cannot express pertinence.
    """
    __storm_table__ = 'whistleblowertip'

    internaltip_id = Unicode()
    #internaltip = Reference(WhistleblowerTip.internaltip_id, InternalTip.id)
    receipt_hash = Unicode()
    last_access = DateTime()
    access_counter = Int()

    ## NO *_keys = It's created without initializing dict


class ReceiverFile(Model):
    """
    This model keeps track of files destinated to a specific receiver
    """
    __storm_table__ = 'receiverfile'

    internaltip_id = Unicode()
    internalfile_id = Unicode()
    receiver_id = Unicode()
    receiver_tip_id = Unicode()
    #internalfile = Reference(ReceiverFile.internalfile_id, InternalFile.id)
    #receiver = Reference(ReceiverFile.receiver_id, Receiver.id)
    #internaltip = Reference(ReceiverFile.internaltip_id, InternalTip.id)
    #receiver_tip = Reference(ReceiverFile.receiver_tip_id, ReceiverTip.id)

    file_path = Unicode()
    size = Int()
    downloads = Int()
    last_access = DateTime()

    mark = Unicode()
    _marker = [ u'not notified', u'notified', u'unable to notify', u'disabled', u'skipped' ]

    status = Unicode()
    _status_list = [ u'cloned', u'reference', u'encrypted', u'unavailable' ]
    # cloned = file is copied on the disk; receiverfile.file_path address this copy
    # reference = receiverfile.file_path reference internalfile.file_path
    # encrypted = receiverfile.file_path is an encrypted file for the specific receiver
    # unavailable = the file was supposed to be encrypted but something didn't work
    #                   (e.g.: the key is broken or expired)

    ## NO *_keys = It's created without initializing dict


class InternalFile(Model):
    """
    This model keeps track of files before they are packaged
    for specific receivers
    """
    __storm_table__ = 'internalfile'

    internaltip_id = Unicode()
    #internaltip = Reference(InternalFile.internaltip_id, InternalTip.id)

    name = Unicode(validator=gltextv)
    sha2sum = Unicode()
    file_path = Unicode()

    content_type = Unicode()
    size = Int()
    ## NO *_keys = It's created without initializing dict

    mark = Unicode()
    _marker = [ u'not processed', u'locked', u'ready', u'delivered' ]
    # 'not processed' = submission time
    # 'ready' = processed in ReceiverTip, available for usage
    # 'delivered' = the file need to stay on DB, but from the disk has been deleted
    # happen when GPG encryption is present in the whole Receiver group.
    # 'locked' = the file is under process by delivery scheduler



class Comment(Model):
    """
    This table handle the comment collection, has an InternalTip referenced
    """
    __storm_table__ = 'comment'

    internaltip_id = Unicode()

    author = Unicode()
    content = Unicode(validator=gltextv)
    # In case of syastem_content usage, content has repr() equiv
    system_content = Pickle()

    type = Unicode()
    _types = [ u'receiver', u'whistleblower', u'system' ]
    mark = Unicode()
    _marker = [ u'not notified', u'notified', u'unable to notify', u'disabled', u'skipped' ]
    ## NO *_keys = It's created without initializing dict


class Node(Model):
    """
    This table has only one instance, has the "id", but would not exists a second element
    of this table. This table acts, more or less, like the configuration file of the previous
    GlobaLeaks release (and some of the GL 0.1 details are specified in Context)

    This table represent the System-wide settings
    """
    __storm_table__ = 'node'

    name = Unicode(validator=gltextv)
    public_site = Unicode(validator=gltextv)
    hidden_service = Unicode()
    email = Unicode()
    receipt_salt = Unicode()
    last_update = DateTime()
    database_version = Int()

    languages_supported = Pickle()
    languages_enabled = Pickle()
    default_language = Unicode()

    # localized string
    description = Pickle(validator=gllocalv)
    presentation = Pickle(validator=gllocalv)
    footer = Pickle(validator=gllocalv)

    # Here is set the time frame for the stats publicly exported by the node.
    # Expressed in hours
    stats_update_time = Int()

    # Advanced settings
    maximum_namesize = Int()
    maximum_descsize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_submission = Bool()
    tor2web_tip = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()

    # receiver capability apply to all the receivers
    postpone_superpower = Bool()

    exception_email = Unicode()

    unicode_keys = ['name', 'public_site', 'email', 'hidden_service',
                    'exception_email', 'default_language' ]
    int_keys = [ 'stats_update_time', 'maximum_namesize', 'maximum_descsize',
                 'maximum_textsize', 'maximum_filesize' ]
    bool_keys = [ 'tor2web_admin', 'tor2web_receiver', 'tor2web_submission',
                  'tor2web_tip', 'tor2web_unauth', 'postpone_superpower' ]
    localized_strings = [ 'description', 'presentation', 'footer' ]


class Notification(Model):
    """
    This table has only one instance, and contain all the notification information
    for the node
    templates are imported in the handler, but settings are expected all at once
    """
    __storm_table__ = 'notification'

    server = Unicode()
    port = Int()
    username = Unicode()
    password = Unicode()

    source_name = Unicode(validator=gltextv)
    source_email = Unicode(validator=gltextv)

    security = Unicode()
    _security_types = [ u'TLS', u'SSL' ]

    # In the future these would be Markdown, but at the moment
    # are just localized dicts
    tip_template = Pickle(validator=gllocalv)
    file_template = Pickle(validator=gllocalv)
    comment_template = Pickle(validator=gllocalv)
    activation_template = Pickle(validator=gllocalv)
    # these four template would be in the unicode_key implicit
    # expected fields, when Client/Backend are updated in their usage

    tip_mail_title = Pickle(validator=gllocalv)
    file_mail_title = Pickle(validator=gllocalv)
    comment_mail_title = Pickle(validator=gllocalv)
    activation_mail_title = Pickle(validator=gllocalv)

    unicode_keys = ['server', 'username', 'password', 'source_name', 'source_email' ]
    localized_strings = [ 'tip_template', 'file_template', 'comment_template',
                         'activation_template', 'tip_mail_title', 'comment_mail_title',
                         'file_mail_title', 'activation_mail_title' ]
    int_keys = [ 'port' ]


class Receiver(Model):
    """
    name, description, password and notification_fields, can be changed
    by Receiver itself
    """
    __storm_table__ = 'receiver'

    user_id = Unicode()
    # Receiver.user = Reference(Receiver.user_id, User.id)

    name = Unicode(validator=gltextv)

    # localization string
    description = Pickle(validator=gllocalv)

    # of GPG key fields
    gpg_key_info = Unicode()
    gpg_key_fingerprint = Unicode()
    gpg_key_status = Unicode()
    gpg_key_armor = Unicode()
    gpg_enable_notification = Bool()
    gpg_enable_files = Bool()

    _gpg_types = [ u'Disabled', u'Enabled' ]
    # would work fine also a Bool, but SQLITE validator is helpful here.

    # User notification_variable
    notification_fields = Pickle()

    # Admin chosen options
    can_delete_submission = Bool()

    # receiver_tier = 1 or 2. Mean being part of the first or second level
    # of receivers body. if threshold is configured in the context. default 1
    receiver_level = Int()

    last_update = DateTime()

    # Group which the Receiver is part of
    tags = Pickle()

    # personal advanced settings
    tip_notification = Bool()
    comment_notification = Bool()
    file_notification = Bool()

    # contexts = ReferenceSet("Context.id",
    #                         "ReceiverContext.context_id",
    #                         "ReceiverContext.receiver_id",
    #                         "Receiver.id")

    unicode_keys = ['name' ]
    localized_strings = [ 'description' ]
    int_keys = [ 'receiver_level' ]
    bool_keys = [ 'can_delete_submission', 'tip_notification',
                  'comment_notification', 'file_notification' ]


# Follow two classes used for Many to Many references
class ReceiverContext(object):
    """
    Class used to implement references between Receivers and Contexts
    """
    __storm_table__ = 'receiver_context'
    __storm_primary__ = 'context_id', 'receiver_id'
    context_id = Unicode()
    receiver_id = Unicode()

Context.receivers = ReferenceSet(
                                 Context.id,
                                 ReceiverContext.context_id,
                                 ReceiverContext.receiver_id,
                                 Receiver.id)

Receiver.contexts = ReferenceSet(
                        Receiver.id,
                        ReceiverContext.receiver_id,
                        ReceiverContext.context_id,
                        Context.id)

class ReceiverInternalTip(object):
    """
    Class used to implement references between Receivers and IntInternalTips
    """
    __storm_table__ = 'receiver_internaltip'
    __storm_primary__ = 'receiver_id', 'internaltip_id'
    receiver_id = Unicode()
    internaltip_id = Unicode()

Receiver.user = Reference(Receiver.user_id, User.id)

Receiver.internaltips = ReferenceSet(Receiver.id,
                                     ReceiverInternalTip.receiver_id,
                                     ReceiverInternalTip.internaltip_id,
                                     InternalTip.id)

InternalTip.receivers = ReferenceSet(InternalTip.id,
                                     ReceiverInternalTip.internaltip_id,
                                     ReceiverInternalTip.receiver_id,
                                     Receiver.id)

InternalTip.context = Reference(InternalTip.context_id,
                                Context.id)

InternalTip.comments = ReferenceSet(InternalTip.id,
                                    Comment.internaltip_id)

InternalTip.receivertips = ReferenceSet(InternalTip.id,
                                        ReceiverTip.internaltip_id)

InternalTip.internalfiles = ReferenceSet(InternalTip.id,
                                         InternalFile.internaltip_id)

ReceiverFile.internalfile = Reference(ReceiverFile.internalfile_id,
                                      InternalFile.id)

ReceiverFile.receiver = Reference(ReceiverFile.receiver_id, Receiver.id)

ReceiverFile.internaltip = Reference(ReceiverFile.internaltip_id,
                                     InternalTip.id)

ReceiverFile.receiver_tip = Reference(ReceiverFile.receiver_tip_id,
                                      ReceiverTip.id)

WhistleblowerTip.internaltip = Reference(WhistleblowerTip.internaltip_id,
                                         InternalTip.id)

InternalFile.internaltip = Reference(InternalFile.internaltip_id,
                                     InternalTip.id)

ReceiverTip.internaltip = Reference(ReceiverTip.internaltip_id, InternalTip.id)

ReceiverTip.receiver = Reference(ReceiverTip.receiver_id, Receiver.id)

Receiver.tips = ReferenceSet(Receiver.id, ReceiverTip.receiver_id)

Comment.internaltip = Reference(Comment.internaltip_id, InternalTip.id)


models = [Node, User, Context, ReceiverTip, WhistleblowerTip, Comment, InternalTip,
          Receiver, ReceiverContext, InternalFile, ReceiverFile, Notification ]

