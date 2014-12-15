# -*- coding: UTF-8
"""
GlobaLeaks ORM Models definitions.
"""
from __future__ import absolute_import

import copy

from storm.locals import Bool, DateTime, Int, Pickle, Reference, ReferenceSet, Unicode, Storm, JSON

from globaleaks.settings import transact
from globaleaks.utils.utility import datetime_now, uuid4
from globaleaks.utils.validator import shorttext_v, longtext_v, shortlocal_v
from globaleaks.utils.validator import longlocal_v, dict_v

from .properties import MetaModel, DateTime

def db_forge_obj(store, mock_class, mock_fields):
    obj = mock_class()
    for key, val in mock_fields.iteritems():
        setattr(obj, key, val)
    store.add(obj)
    return obj

@transact
def forge_obj(store, mock_class, mock_fields):
    return db_forge_obj(store, mock_class, mock_fields)

class BaseModel(Storm):
    """
    Globaleaks's most basic model.

    Define a set of methods  on the top of Storm to simplify
    creation/access/update/deletions of data.
    """
    __metaclass__ = MetaModel
    __storm_table__ = None

    # initialize empty list for the base classes
    unicode_keys = []
    localized_strings = []
    int_keys = []
    bool_keys = []
    json_keys = []

    def __init__(self, attrs=None):
        self.update(attrs)

    @classmethod
    def new(cls, store, attrs=None):
        """
        Add a new object to the store, filling its data with the attributes
        given.

        :param store:
        :param attrs: The dictionary containing initial values for the
        """
        obj = cls(attrs)
        store.add(obj)
        return obj

    def update(self, attrs=None):
        """
        Updated Models attributes from dict.
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
        cls_json_keys = getattr(self, "json_keys")
        cls_localized_keys = getattr(self, "localized_strings")

        for k in cls_unicode_keys:
            value = unicode(attrs[k])
            setattr(self, k, value)

        for k in cls_int_keys:
            value = int(attrs[k])
            setattr(self, k, value)

        for k in cls_json_keys:
            value = attrs[k]
            setattr(self, k, value)

        for k in cls_bool_keys:
            if attrs[k] == u'true':
                value = True
            elif attrs[k] == u'false':
                value = False
            else:
                value = bool(attrs[k])
            setattr(self, k, value)

        for k in cls_localized_keys:
            value = attrs[k]
            previous = getattr(self, k)
            if previous and isinstance(previous, dict):
                previous.update(value)
                setattr(self, k, previous)
            else:
                setattr(self, k, value)

    def __repr___(self):
        attrs = ['{}={}'.format(attr, getattr(self, attr))
                 for attr in self._public_attrs]
        return '<%s model with values %s>' % (self.__name__, ', '.join(attrs))

    def __setattr__(self, name, value):
        # harder better faster stronger
        if isinstance(value, str):
            value = unicode(value)
        return super(BaseModel, self).__setattr__(name, value)

    def dict(self, *keys):
        """
        Return a dictionary serialization of the current model.
        if no filter is provided, returns every single attribute.

        :raises KeyError: if a key is not recognized as public attribute.
        """
        keys = set(keys or self._public_attrs)
        not_allowed_keys = keys - self._public_attrs
        if not_allowed_keys:
            raise KeyError('Invalid keys: {}'.format(not_allowed_keys))
        else:
            return {key: getattr(self, key) for key in keys & self._public_attrs}


class Model(BaseModel):
    """
    Base class for working the database, already integrating an id, and a
    creation_date.
    """
    __storm_table__ = None
    id = Unicode(primary=True, default_factory=uuid4)
    creation_date = DateTime(default_factory=datetime_now)
    # Note on creation last_update and last_access may be out of sync by some
    # seconds.

    @classmethod
    def get(cls, store, obj_id):
        return store.find(cls, cls.id == obj_id).one()

    @classmethod
    def delete(self, store):
        store.remove(self)


class User(Model):
    """
    This model keeps track of globaleaks users.
    """
    username = Unicode(validator=shorttext_v)
    password = Unicode()
    salt = Unicode()
    role = Unicode()
    state = Unicode()
    last_login = DateTime()
    language = Unicode()
    timezone = Int()

    _roles = [ u'admin', u'receiver' ]
    _states = [ u'disabled', u'password_change_needed', u'enabled']

    unicode_keys = [ 'username', 'password', 'salt', 'role',
                     'state', 'language' ]
    int_keys = [ 'timezone' ]


class Context(Model):
    """
    This model keeps track of specific contexts settings.
    """
    # steps = [
    #     {
    #         'name': local_dict,
    #         'type': 'fields',
    #         'fields': [field_group_id1,
    #                    field_group_id2]
    #     },
    #     {
    #         'name': local_dict,
    #         'type': 'receiver',
    #         'options': {
    #             'show_small_receiver': True,
    #             'selectable_receiver': True,
    #             'show_small_cards': False,
    #             'maximum_selectable_receivers': 10,
    #             'select_all_receivers': True
    #         }
    #     }
    # ]

    selectable_receiver = Bool()
    show_small_cards = Bool()
    show_receivers = Bool()
    maximum_selectable_receivers = Int()
    select_all_receivers = Bool()

    escalation_threshold = Int()

    tip_max_access = Int()
    file_max_download = Int()
    file_required = Bool()
    tip_timetolive = Int()
    submission_timetolive = Int()
    last_update = DateTime()
    tags = Pickle()

    # localized stuff
    name = Pickle(validator=shortlocal_v)
    description = Pickle(validator=longlocal_v)
    receiver_introduction = Pickle(validator=longlocal_v)

    # receivers = ReferenceSet(
    #                         Context.id,
    #                         ReceiverContext.context_id,
    #                         ReceiverContext.receiver_id,
    #                         Receiver.id)

    postpone_superpower = Bool()
    can_delete_submission = Bool()

    require_file_description = Bool()
    delete_consensus_percentage = Int()
    require_pgp = Bool()
    show_small_cards = Bool()
    show_receivers = Bool()
    enable_private_messages = Bool()

    presentation_order = Int()

    unicode_keys = []
    localized_strings = ['name', 'description', 'receiver_introduction']
    int_keys = [ 'escalation_threshold', 'tip_max_access', 'file_max_download',
                 'maximum_selectable_receivers', 'delete_consensus_percentage',
                 'presentation_order' ]
    bool_keys = [ 'selectable_receiver', 'file_required', 'select_all_receivers',
                  'postpone_superpower', 'can_delete_submission',
                  'require_file_description', 'require_pgp',
                  'show_small_cards', 'show_receivers', "enable_private_messages" ]


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
    # context = Reference(InternalTip.context_id, Context.id)
    # comments = ReferenceSet(InternalTip.id, Comment.internaltip_id)
    # receivertips = ReferenceSet(InternalTip.id, ReceiverTip.internaltip_id)
    # internalfiles = ReferenceSet(InternalTip.id, InternalFile.internaltip_id)
    # receivers = ReferenceSet(InternalTip.id, Receiver.id)

    wb_steps = JSON()
    pertinence_counter = Int()
    expiration_date = DateTime()
    last_activity = DateTime()

    # the LIMITS are stored in InternalTip because and admin may
    # need change them. These values are copied by Context
    escalation_threshold = Int()
    access_limit = Int()
    download_limit = Int()

    mark = Unicode()

    _marker = [u'submission', u'finalize', u'first', u'second']
    # N.B. *_keys = It's created without initializing dict


class ReceiverTip(Model):
    """
    This is the table keeping track of ALL the receivers activities and
    date in a Tip, Tip core data are stored in StoredTip. The data here
    provide accountability of Receiver accesses, operations, options.
    """
    internaltip_id = Unicode()
    receiver_id = Unicode()
    # internaltip = Reference(ReceiverTip.internaltip_id, InternalTip.id)
    # receiver = Reference(ReceiverTip.receiver_id, Receiver.id)

    last_access = DateTime(default_factory=datetime_now)
    access_counter = Int()
    expressed_pertinence = Int()
    notification_date = DateTime()
    mark = Unicode()

    _marker = [u'not notified', u'notified', u'unable to notify', u'disabled',
               u'skipped']
    # N.B. *_keys = It's created without initializing dict


class WhistleblowerTip(Model):
    """
    WhisteleblowerTip is intended, to provide a whistleblower access to the
    Tip.  Has ome differencies from the ReceiverTips: has a secret
    authentication checks, has different capabilities, like: cannot not
    download, cannot express pertinence.
    """
    internaltip_id = Unicode()
    # internaltip = Reference(WhistleblowerTip.internaltip_id, InternalTip.id)
    receipt_hash = Unicode()
    last_access = DateTime()
    access_counter = Int()

    # N.B. *_keys = It's created without initializing dict


class ReceiverFile(Model):
    """
    This model keeps track of files destinated to a specific receiver
    """
    internaltip_id = Unicode()
    internalfile_id = Unicode()
    receiver_id = Unicode()
    receiver_tip_id = Unicode()
    # internalfile = Reference(ReceiverFile.internalfile_id, InternalFile.id)
    # receiver = Reference(ReceiverFile.receiver_id, Receiver.id)
    # internaltip = Reference(ReceiverFile.internaltip_id, InternalTip.id)
    # receiver_tip = Reference(ReceiverFile.receiver_tip_id, ReceiverTip.id)

    file_path = Unicode()
    size = Int()
    downloads = Int()
    last_access = DateTime()

    mark = Unicode()
    _marker = [u'not notified', u'notified', u'unable to notify', u'disabled',
               u'skipped']

    status = Unicode()
    _status_list = [u'reference', u'encrypted', u'unavailable', u'nokey']
    # reference = receiverfile.file_path reference internalfile.file_path
    # encrypted = receiverfile.file_path is an encrypted file for
    #                                    the specific receiver
    # unavailable = the file was supposed to be available but something goes
    # wrong and now is lost

    # N.B. *_keys = It's created without initializing dict


class InternalFile(Model):
    """
    This model keeps track of files before they are packaged
    for specific receivers
    """
    internaltip_id = Unicode()
    # internaltip = Reference(InternalFile.internaltip_id, InternalTip.id)

    name = Unicode(validator=longtext_v)
    file_path = Unicode()

    content_type = Unicode()
    description = Unicode(validator=longtext_v)
    size = Int()

    mark = Unicode()
    _marker = [u'not processed', u'locked', u'ready', u'delivered']
    # 'not processed' = submission time
    # 'ready' = processed in ReceiverTip, available for usage
    # 'delivered' = the file need to stay on DB, but from the
    #               disk has been deleted
    #  it happens when GPG encryption is present in the whole Receiver group.
    # 'locked' = the file is under process by delivery scheduler

    # N.B. *_keys = It's created without initializing dict


class Comment(Model):
    """
    This table handle the comment collection, has an InternalTip referenced
    """
    internaltip_id = Unicode()

    author = Unicode()
    content = Unicode(validator=longtext_v)

    # In case of system_content usage, content has repr() equiv
    system_content = Pickle()

    type = Unicode()
    _types = [u'receiver', u'whistleblower', u'system']
    mark = Unicode()
    _marker = [
        u'not notified',
        u'notified',
        u'unable to notify',
        u'disabled',
        u'skipped']

    # N.B. *_keys = It's created without initializing dict


class Message(Model):
    """
    This table handle the direct messages between whistleblower and one
    Receiver.
    """
    receivertip_id = Unicode()
    author = Unicode()
    content = Unicode(validator=longtext_v)
    visualized = Bool()

    type = Unicode()
    _types = [u'receiver', u'whistleblower']
    mark = Unicode()
    _marker = [
        u'not notified',
        u'notified',
        u'unable to notify',
        u'disabled',
        u'skipped']


class Node(Model):
    """
    This table has only one instance, has the "id", but would not exists a
    second element of this table. This table acts, more or less, like the
    configuration file of the previous GlobaLeaks release (and some of the GL
    0.1 details are specified in Context)

    This table represent the System-wide settings
    """
    name = Unicode(validator=shorttext_v)
    public_site = Unicode()
    hidden_service = Unicode()
    email = Unicode()
    receipt_salt = Unicode()
    last_update = DateTime()
    # this has a dedicated validator in update_node()
    receipt_regexp = Unicode()

    languages_enabled = Pickle()
    default_language = Unicode()
    default_timezone = Int()

    # localized string
    description = Pickle(validator=longlocal_v)
    presentation = Pickle(validator=longlocal_v)
    footer = Pickle(validator=longlocal_v)
    subtitle = Pickle(validator=longlocal_v)
    terms_and_conditions = Pickle(validator=longlocal_v)
    security_awareness_title = Pickle(validator=longlocal_v)
    security_awareness_text = Pickle(validator=longlocal_v)

    # Here is set the time frame for the stats publicly exported by the node.
    # Expressed in hours
    stats_update_time = Int()

    # Advanced settings
    maximum_namesize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_submission = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()
    allow_unencrypted = Bool()

    # privileges configurable in node/context/receiver
    postpone_superpower = Bool()
    can_delete_submission = Bool()

    ahmia = Bool()
    wizard_done = Bool(default=False)
    anomaly_checks = Bool(default=False)

    disable_privacy_badge = Bool(default=False)
    disable_security_awareness_badge = Bool(default=False)
    disable_security_awareness_questions = Bool(default=False)

    whistleblowing_question = JSON()
    whistleblowing_button = JSON()

    enable_custom_privacy_badge = Bool()
    custom_privacy_badge_tbb = JSON()
    custom_privacy_badge_tor = JSON()
    custom_privacy_badge_none = JSON()

    exception_email = Unicode()

    unicode_keys = ['name', 'public_site', 'email', 'hidden_service',
                    'exception_email', 'default_language', 'receipt_regexp']
    int_keys = [ 'stats_update_time', 'maximum_namesize',
                 'maximum_textsize', 'maximum_filesize', 'default_timezone' ]
    bool_keys = [ 'tor2web_admin', 'tor2web_receiver', 'tor2web_submission',
                  'tor2web_unauth', 'postpone_superpower', 'anomaly_checks',
                  'can_delete_submission', 'ahmia', 'allow_unencrypted',
                  'disable_privacy_badge', 'disable_security_awareness_badge',
                  'disable_security_awareness_questions', 'enable_custom_privacy_badge' ]
                # wizard_done is not checked because it's set by the backend
    localized_strings = [ 'description', 'presentation', 'footer', 'subtitle',
                          'terms_and_conditions', 'security_awareness_title',
                          'security_awareness_text', 'whistleblowing_question',
                          'whistleblowing_button', 'custom_privacy_badge_tbb',
                          'custom_privacy_badge_tor', 'custom_privacy_badge_none' ]


class Notification(Model):

    """
    This table has only one instance, and contain all the notification
    information for the node templates are imported in the handler, but
    settings are expected all at once.
    """
    server = Unicode()
    port = Int()
    username = Unicode()
    password = Unicode()

    source_name = Unicode(validator=shorttext_v)
    source_email = Unicode(validator=shorttext_v)

    security = Unicode()
    _security_types = [u'TLS', u'SSL']

    encrypted_tip_template = Pickle(validator=longlocal_v)
    encrypted_tip_mail_title = Pickle(validator=longlocal_v)
    plaintext_tip_template = Pickle(validator=longlocal_v)
    plaintext_tip_mail_title = Pickle(validator=longlocal_v)

    encrypted_file_template = Pickle(validator=longlocal_v)
    encrypted_file_mail_title = Pickle(validator=longlocal_v)
    plaintext_file_template = Pickle(validator=longlocal_v)
    plaintext_file_mail_title = Pickle(validator=longlocal_v)

    encrypted_comment_template = Pickle(validator=longlocal_v)
    encrypted_comment_mail_title = Pickle(validator=longlocal_v)
    plaintext_comment_template = Pickle(validator=longlocal_v)
    plaintext_comment_mail_title = Pickle(validator=longlocal_v)

    encrypted_message_template = Pickle(validator=longlocal_v)
    encrypted_message_mail_title = Pickle(validator=longlocal_v)
    plaintext_message_template = Pickle(validator=longlocal_v)
    plaintext_message_mail_title = Pickle(validator=longlocal_v)

    admin_anomaly_template = Pickle(validator=longlocal_v)

    zip_description = Pickle(validator=longlocal_v)

    unicode_keys = [
        'server',
        'username',
        'password',
        'source_name',
        'source_email']
    localized_strings = [
        'encrypted_tip_template',
        'encrypted_tip_mail_title',
        'plaintext_tip_template',
        'plaintext_tip_mail_title',
        'encrypted_file_template',
        'encrypted_file_mail_title',
        'plaintext_file_template',
        'plaintext_file_mail_title',
        'encrypted_comment_template',
        'encrypted_comment_mail_title',
        'plaintext_comment_template',
        'plaintext_comment_mail_title',
        'encrypted_message_template',
        'encrypted_message_mail_title',
        'plaintext_message_template',
        'plaintext_message_mail_title',
        'zip_description']
    int_keys = ['port']


class Receiver(Model):
    """
    name, description, password and notification_fields, can be changed
    by Receiver itself
    """
    user_id = Unicode()
    # Receiver.user = Reference(Receiver.user_id, User.id)

    name = Unicode(validator=shorttext_v)

    # localization string
    description = Pickle(validator=longlocal_v)

    # of GPG key fields
    gpg_key_info = Unicode()
    gpg_key_fingerprint = Unicode()
    gpg_key_status = Unicode()
    gpg_key_armor = Unicode()
    gpg_enable_notification = Bool()

    _gpg_types = [u'Disabled', u'Enabled']

    # Can be changed and can be different from username!
    mail_address = Unicode()

    # Admin chosen options
    can_delete_submission = Bool()
    postpone_superpower = Bool()

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
    message_notification = Bool()

    # contexts = ReferenceSet("Context.id",
    #                         "ReceiverContext.context_id",
    #                         "ReceiverContext.receiver_id",
    #                         "Receiver.id")

    presentation_order = Int()

    unicode_keys = ['name', 'mail_address']
    localized_strings = ['description']
    int_keys = ['receiver_level', 'presentation_order']
    bool_keys = ['can_delete_submission', 'tip_notification',
                 'comment_notification', 'file_notification',
                 'message_notification', 'postpone_superpower']


class Field(Model):
    label = JSON()
    description = JSON()
    hint = JSON()

    multi_entry = Bool()
    required = Bool()
    preview = Bool()

    # This is set if the field should be duplicated for collecting statistics
    # when encryption is enabled.
    stats_enabled = Bool()

    # This indicates that this field should be used as a template for composing
    # new steps.
    is_template = Bool()

    x = Int()
    y = Int()

    type = Unicode()
    # Supported field types:
    # * inputbox
    # * textarea
    # * selectbox
    # * checkbox
    # * modal
    # * dialog
    # * tos
    # * fieldgroup

    # When only 1 option
    # {
    #     "trigger": field_id
    # }

    # When multiple options
    # [
    #     {
    #         "name": lang_dict,
    #         "x": int,
    #         "y": int,
    #         "description": lang_dict,
    #         "trigger": field_id
    #     }, ...
    # ]

    unicode_keys = ['type']
    int_keys = ['x', 'y']
    localized_strings = ['label', 'description', 'hint']
    bool_keys = ['multi_entry', 'preview', 'required', 'stats_enabled', 'is_template']

    # XXX the instance already knows about the store, are we sure there's no way
    # to obtain it?
    def delete(self, store):
        for child in self.children:
            child.delete(store)
        store.remove(self)

    def copy(self, store, is_template):
        obj_copy = self.__class__()
        obj_copy.label = copy.deepcopy(self.label)
        obj_copy.description = copy.deepcopy(self.label)
        obj_copy.hint = copy.deepcopy(self.label)
        obj_copy.multi_entry = self.multi_entry
        obj_copy.required = self.required
        obj_copy.stats_enabled = self.stats_enabled
        obj_copy.is_template = is_template
        obj_copy.x = self.x
        obj_copy.y = self.y
        obj_copy.type = self.type
        for child in self.children:
            child_copy = child.copy(store, is_template)
            obj_copy.children.add(child_copy)
        for opt in self.options:
            opt_copy = opt.copy(store)
            obj_copy.options.add(opt_copy)
        store.add(obj_copy)
        return obj_copy

class FieldOption(Model):
    _storm_table__ = 'option'

    field_id = Unicode()
    number = Int()
    attrs = JSON()

    unicode_keys = ['field_id']
    int_keys = ['number']
    json_keys = ['attrs']

    def __init__(self, attrs=None, localized_keys=[]):
        self.attrs = dict()
        self.update(attrs, localized_keys)

    @classmethod
    def new(cls, store, attrs=None, localized_keys=[]):
        obj = cls(attrs, localized_keys)
        store.add(obj)
        return obj

    def update(self, attrs=None, localized_keys=[]):
        BaseModel.update(self, attrs)

        for k in localized_keys:
            value = attrs['attrs'][k]
            previous = self.attrs.get(k, None)
            if previous and isinstance(previous, dict):
                previous.update(value)
                self.attrs[k] = previous
            else:
                self.attrs[k] = value

    def copy(self, store):
        obj_copy = self.__class__()
        obj_copy.field_id = self.field_id
        obj_copy.number = self.number
        obj_copy.attrs = copy.deepcopy(self.attrs)
        return obj_copy

class Step(Model):
    __storm_table__ = 'step'

    context_id = Unicode()
    label = JSON()
    description = JSON()
    hint = JSON()
    number = Int()

    unicode_keys = ['context_id']
    int_keys = ['number']
    localized_strings = ['label', 'description', 'hint']


class ApplicationData(Model):
    """
    Exists only one instance of this class, because the ApplicationData
    had only one big updated blob.
    """
    __storm_table__ = 'applicationdata'

    version = Int()
    # XXX why is this a Pickle? ~ A.
    fields = Pickle()


class Stats(Model):
    """
    Stats collection!
    """
    __storm_table__ = 'stats'

    content = Pickle()


# Follow classes used for Many to Many references
class ReceiverContext(BaseModel):
    """
    Class used to implement references between Receivers and Contexts
    """
    __storm_table__ = 'receiver_context'
    __storm_primary__ = 'context_id', 'receiver_id'
    context_id = Unicode()
    receiver_id = Unicode()


class ReceiverInternalTip(BaseModel):
    """
    Class used to implement references between Receivers and IntInternalTips
    """
    __storm_table__ = 'receiver_internaltip'
    __storm_primary__ = 'receiver_id', 'internaltip_id'

    receiver_id = Unicode()
    internaltip_id = Unicode()


class FieldField(BaseModel):
    """
    Class used to implement references between Fields and Fields!
    parent - child relation used to implement fieldgroups
    """
    __storm_table__ = 'field_field'
    __storm_primary__ = 'parent_id', 'child_id'

    parent_id = Unicode()
    child_id = Unicode()

    unicode_keys = ['parent_id', 'child_id']


class Stats(Model):
    __storm_table__ = 'Stats'

    start = DateTime()
    summary = JSON()
    freemb = Int()


class Anomalies(Model):
    __storm_table__ = 'anomalies'

    stored_when = Unicode() # is a Datetime but string
    alarm = Int()
    events = JSON()


class StepField(BaseModel):
    """
    Class used to implement references between Steps and Fields!
    """
    __storm_table__ = 'step_field'
    __storm_primary__ = 'step_id', 'field_id'

    step_id = Unicode()
    field_id = Unicode()

    unicode_keys = ['step_id', 'field_id']


Field.options = ReferenceSet(Field.id,
                             FieldOption.field_id)

FieldOption.field = Reference(FieldOption.field_id, Field.id)

Context.steps = ReferenceSet(Context.id,
                             Step.context_id)

Step.context = Reference(Step.context_id, Context.id)

# _*_# References tracking below #_*_#
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

Message.receivertip = Reference(Message.receivertip_id, ReceiverTip.id)

Field.children = ReferenceSet(
    Field.id,
    FieldField.parent_id,
    FieldField.child_id,
    Field.id)

Step.children = ReferenceSet(
    Step.id,
    StepField.step_id,
    StepField.field_id,
    Field.id)

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

models = [Node, User, Context, ReceiverTip, WhistleblowerTip, Comment,
          InternalTip, Receiver, ReceiverContext, InternalFile, ReceiverFile,
          Notification, Message, Stats, Field, FieldField, Step,
          Stats, Anomalies, ApplicationData]
