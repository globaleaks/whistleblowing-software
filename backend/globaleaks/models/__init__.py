# -*- coding: utf-8
"""
ORM Models definitions.
"""
from __future__ import absolute_import

from datetime import timedelta
from storm.locals import Bool, Int, Unicode, Storm, JSON

from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.settings import Settings
from globaleaks.utils.utility import datetime_now, datetime_null, datetime_to_ISO8601, uuid4

from .properties import MetaModel, DateTime


def db_forge_obj(store, mock_class, mock_fields):
    obj = mock_class(mock_fields)
    store.add(obj)
    return obj


@transact
def forge_obj(store, mock_class, mock_fields):
    return db_forge_obj(store, mock_class, mock_fields)


def db_get(store, model, *args, **kwargs):
    ret = store.find(model, *args, **kwargs).one()
    if ret is None:
        raise errors.ModelNotFound(model)

    return ret


@transact
def get(store, model, *args, **kwargs):
    return db_get(store, model, *args, **kwargs)


def db_delete(store, model, *args, **kwargs):
    return store.find(model, *args, **kwargs).remove()


@transact
def delete(store, model, *args, **kwargs):
    return db_delete(store, model, *args, **kwargs)


class Model(Storm):
    """
    Globaleaks's most basic model.

    Define a set of methods on the top of Storm to simplify
    creation/access/update/deletions of data.
    """
    __metaclass__ = MetaModel
    __storm_table__ = None

    # initialize empty list for the base classes
    properties = []
    unicode_keys = []
    localized_keys = []
    int_keys = []
    bool_keys = []
    datetime_keys = []
    json_keys = []
    date_keys = []
    optional_references = []
    list_keys = []

    def __init__(self, values=None, migrate=False):
        self.update(values)

    def update(self, values=None):
        """
        Updated Models attributes from dict.
        """
        if values is None:
            return

        if 'id' in values and values['id']:
            setattr(self, 'id', values['id'])

        if 'tid' in values and values['tid'] != '':
            setattr(self, 'tid', values['tid'])

        for k in getattr(self, 'unicode_keys'):
            if k in values and values[k] is not None:
                setattr(self, k, unicode(values[k]))

        for k in getattr(self, 'int_keys'):
            if k in values and values[k] is not None:
                setattr(self, k, int(values[k]))

        for k in getattr(self, 'datetime_keys'):
            if k in values and values[k] is not None:
                setattr(self, k, values[k])

        for k in getattr(self, 'bool_keys'):
            if k in values and values[k] is not None:
                if values[k] == u'true':
                    value = True
                elif values[k] == u'false':
                    value = False
                else:
                    value = bool(values[k])
                setattr(self, k, value)

        for k in getattr(self, 'localized_keys'):
            if k in values and values[k] is not None:
                value = values[k]
                previous = getattr(self, k)

                if previous and isinstance(previous, dict):
                    previous.update(value)
                    setattr(self, k, previous)
                else:
                    setattr(self, k, value)

        for k in getattr(self, 'json_keys'):
            if k in values and values[k] is not None:
                setattr(self, k, values[k])

        for k in getattr(self, 'optional_references'):
            if k in values and values[k]:
                setattr(self, k, values[k])

    def __str__(self):
        # pylint: disable=no-member
        values = ['{}={}'.format(attr, getattr(self, attr)) for attr in self.properties]
        return '<%s model with values %s>' % (self.__class__.__name__, ', '.join(values))

    def __repr__(self):
        return self.__str__()

    def __setattr__(self, name, value):
        # harder better faster stronger
        if isinstance(value, str):
            value = unicode(value)

        return super(Model, self).__setattr__(name, value)

    def dict(self, language):
        """
        Return a dictionary serialization of the current model.
        """
        ret = {}

        for k in self.properties:
            value = getattr(self, k)

            if k in self.localized_keys:
                value = value[language] if language in value else u''

            elif k in self.date_keys:
                value = datetime_to_ISO8601(value)

            ret[k] = value

        for k in self.list_keys:
            ret[k] = []

        return ret


class ModelWithID(Model):
    """
    Base class for working the database, already integrating an id.
    """
    __storm_table__ = None
    id = Unicode(primary=True, default_factory=uuid4)


class ModelWithTID(Model):
    """
    Base class for models requiring a TID
    """
    __storm_table__ = None

    tid = Int(primary=True, default=1)


class ModelWithTIDandID(Model):
    """
    Base class for models requiring a TID and an ID
    """
    __storm_table__ = None

    tid = Int(default=1)
    id = Unicode(primary=True, default_factory=uuid4)


class Tenant(ModelWithID):
    """
    Class used to implement tenants
    """
    id = Int(primary=True)
    label = Unicode(default=u'')
    active = Bool(default=True)
    creation_date = DateTime(default_factory=datetime_now)
    subdomain = Unicode(default=u'')

    unicode_keys = ['label', 'subdomain']
    bool_keys = ['active']


class User(ModelWithTIDandID):
    """
    This model keeps track of globaleaks users.
    """
    creation_date = DateTime(default_factory=datetime_now)

    username = Unicode(default=u'')

    password = Unicode(default=u'')
    salt = Unicode()

    name = Unicode(default=u'')
    description = JSON(default={})

    public_name = Unicode(default=u'')

    # roles: 'admin', 'receiver', 'custodian'
    role = Unicode(default=u'receiver')
    state = Unicode(default=u'enabled')
    last_login = DateTime(default_factory=datetime_null)
    mail_address = Unicode(default=u'')
    language = Unicode()
    password_change_needed = Bool(default=True)
    password_change_date = DateTime(default_factory=datetime_null)

    # BEGIN of PGP key fields
    pgp_key_fingerprint = Unicode(default=u'')
    pgp_key_public = Unicode(default=u'')
    pgp_key_expiration = DateTime(default_factory=datetime_null)
    # END of PGP key fields

    unicode_keys = ['username', 'role', 'state',
                    'language', 'mail_address', 'name',
                    'public_name', 'language']

    localized_keys = ['description']

    bool_keys = ['password_change_needed']

    date_keys = ['creation_date', 'last_login', 'password_change_date', 'pgp_key_expiration']


class Context(ModelWithTIDandID):
    """
    This model keeps track of contexts settings.
    """
    show_small_receiver_cards = Bool(default=False)
    show_context = Bool(default=True)
    show_recipients_details = Bool(default=False)
    allow_recipients_selection = Bool(default=False)
    maximum_selectable_receivers = Int(default=0)
    select_all_receivers = Bool(default=True)

    enable_comments = Bool(default=True)
    enable_messages = Bool(default=False)
    enable_two_way_comments = Bool(default=True)
    enable_two_way_messages = Bool(default=True)
    enable_attachments = Bool(default=True) # Lets WB attach files to submission
    enable_rc_to_wb_files = Bool(default=False) # The name says it all folks

    tip_timetolive = Int(default=15) # in days, -1 indicates no expiration

    # localized strings
    name = JSON(default={})
    description = JSON(default={})
    recipients_clarification = JSON(default={})

    status_page_message = JSON(default={})

    show_receivers_in_alphabetical_order = Bool(default=True)

    presentation_order = Int(default=0)

    questionnaire_id = Unicode(default=u'default')

    unicode_keys = ['questionnaire_id']

    localized_keys = ['name', 'description', 'recipients_clarification', 'status_page_message']

    int_keys = [
      'tip_timetolive',
      'maximum_selectable_receivers',
      'presentation_order'
    ]

    bool_keys = [
      'select_all_receivers',
      'show_small_receiver_cards',
      'show_context',
      'show_recipients_details',
      'show_receivers_in_alphabetical_order',
      'allow_recipients_selection',
      'enable_comments',
      'enable_messages',
      'enable_two_way_comments',
      'enable_two_way_messages',
      'enable_attachments',
      'enable_rc_to_wb_files'
    ]

    list_keys = ['receivers']


class InternalTip(ModelWithTIDandID):
    """
    This is the internal representation of a Tip that has been submitted
    """
    creation_date = DateTime(default_factory=datetime_now)
    update_date = DateTime(default_factory=datetime_now)

    context_id = Unicode()

    questionnaire_hash = Unicode()
    preview = JSON()
    progressive = Int(default=0)
    tor2web = Bool(default=False)
    total_score = Int(default=0)
    expiration_date = DateTime()

    identity_provided = Bool(default=False)
    identity_provided_date = DateTime(default_factory=datetime_null)

    enable_two_way_comments = Bool(default=True)
    enable_two_way_messages = Bool(default=True)
    enable_attachments = Bool(default=True)
    enable_whistleblower_identity = Bool(default=False)

    wb_last_access = DateTime(default_factory=datetime_now)
    wb_access_counter = Int(default=0)


class ReceiverTip(ModelWithTIDandID):
    """
    This is the table keeping track of ALL the receivers activities and
    date in a Tip, Tip core data are stored in StoredTip. The data here
    provide accountability of Receiver accesses, operations, options.
    """
    internaltip_id = Unicode()
    receiver_id = Unicode()

    last_access = DateTime(default_factory=datetime_null)
    access_counter = Int(default=0)

    label = Unicode(default=u'')

    can_access_whistleblower_identity = Bool(default=False)

    new = Int(default=True)

    enable_notifications = Bool(default=True)

    unicode_keys = ['label']

    bool_keys = ['enable_notifications']


class WhistleblowerTip(ModelWithTIDandID):
    """
    WhisteleblowerTip implement the expiring authentication token for
    the whistleblower and acts as interface to the InternalTip.
    """
    receipt_hash = Unicode()


class IdentityAccessRequest(ModelWithTIDandID):
    """
    This model keeps track of identity access requests by receivers and
    of the answers by custodians.
    """
    receivertip_id = Unicode()
    request_date = DateTime(default_factory=datetime_now)
    request_motivation = Unicode(default=u'')
    reply_date = DateTime(default_factory=datetime_null)
    reply_user_id = Unicode(default=u'')
    reply_motivation = Unicode(default=u'')
    reply = Unicode(default=u'pending')


class InternalFile(ModelWithTIDandID):
    """
    This model keeps track of submission files
    """
    creation_date = DateTime(default_factory=datetime_now)

    internaltip_id = Unicode()

    name = Unicode()
    file_path = Unicode()

    content_type = Unicode()
    size = Int()

    new = Int(default=True)

    submission = Int(default = False)

    processing_attempts = Int(default=0)


class ReceiverFile(ModelWithTIDandID):
    """
    This model keeps track of files destinated to a specific receiver
    """
    internalfile_id = Unicode()
    receivertip_id = Unicode()
    file_path = Unicode()
    size = Int()
    downloads = Int(default=0)
    last_access = DateTime(default_factory=datetime_null)

    new = Int(default=True)

    status = Unicode()
    # statuses: 'reference', 'encrypted', 'unavailable', 'nokey'
    # reference = receiverfile.file_path reference internalfile.file_path
    # encrypted = receiverfile.file_path is an encrypted file for
    #                                    the specific receiver
    # unavailable = the file was supposed to be available but something goes
    # wrong and now is lost


class WhistleblowerFile(ModelWithTIDandID):
    """
    This models stores metadata of files uploaded by recipients intended to be
    delivered to the whistleblower. This file is not encrypted and nor is it
    integrity checked in any meaningful way.
    """
    receivertip_id = Unicode()

    name = Unicode()
    file_path = Unicode()
    size = Int()
    content_type = Unicode()
    downloads = Int(default=0)
    creation_date = DateTime(default_factory=datetime_now)
    last_access = DateTime(default_factory=datetime_null)
    description = Unicode()


class Comment(ModelWithTIDandID):
    """
    This table handle the comment collection, has an InternalTip referenced
    """
    creation_date = DateTime(default_factory=datetime_now)

    internaltip_id = Unicode()

    author_id = Unicode()
    content = Unicode()

    type = Unicode()
    # types: 'receiver', 'whistleblower'

    new = Int(default=True)


class Message(ModelWithTIDandID):
    """
    This table handle the direct messages between whistleblower and one
    Receiver.
    """
    creation_date = DateTime(default_factory=datetime_now)

    receivertip_id = Unicode()
    content = Unicode()

    type = Unicode()
    # types: 'receiver', whistleblower'

    new = Int(default=True)


class Mail(ModelWithTIDandID):
    """
    This model keeps track of emails to be spooled by the system
    """
    creation_date = DateTime(default_factory=datetime_now)

    address = Unicode()
    subject = Unicode()
    body = Unicode()

    processing_attempts = Int(default=0)

    unicode_keys = ['address', 'subject', 'body']


class Receiver(ModelWithTIDandID):
    """
    This model keeps track of receivers settings.
    """
    configuration = Unicode(default=u'default')
    # configurations: 'default', 'forcefully_selected', 'unselectable'

    # Admin chosen options
    can_delete_submission = Bool(default=False)
    can_postpone_expiration = Bool(default=False)
    can_grant_permissions = Bool(default=False)

    tip_notification = Bool(default=True)

    unicode_keys = ['configuration']

    bool_keys = [
        'can_delete_submission',
        'can_postpone_expiration',
        'can_grant_permissions',
        'tip_notification',
    ]

    list_keys = ['contexts']


class Field(ModelWithTIDandID):
    x = Int(default=0)
    y = Int(default=0)
    width = Int(default=0)

    label = JSON()
    description = JSON()
    hint = JSON()

    required = Bool(default=False)
    preview = Bool(default=False)

    multi_entry = Bool(default=False)
    multi_entry_hint = JSON()

    # This is set if the field should be duplicated for collecting statistics
    # when encryption is enabled.
    stats_enabled = Bool(default=False)

    triggered_by_score = Int(default=0)

    fieldgroup_id = Unicode()
    step_id = Unicode()
    template_id = Unicode()

    type = Unicode(default=u'inputbox')

    instance = Unicode(default=u'instance')
    editable = Bool(default=True)

    unicode_keys = ['type', 'instance', 'key']
    int_keys = ['x', 'y', 'width', 'triggered_by_score']
    localized_keys = ['label', 'description', 'hint', 'multi_entry_hint']
    bool_keys = ['editable', 'multi_entry', 'preview', 'required', 'stats_enabled']
    optional_references = ['template_id', 'step_id', 'fieldgroup_id']


class FieldAttr(ModelWithTIDandID):
    field_id = Unicode()
    name = Unicode()
    type = Unicode()
    value = JSON()

    # FieldAttr is a special model.
    # Here we consider all its attributes as unicode, then
    # depending on the type we handle the value as a localized value
    unicode_keys = ['field_id', 'name', 'type']

    def update(self, values=None):
        """
        Updated ModelWithIDs attributes from dict.
        """
        super(FieldAttr, self).update(values)

        if values is None:
            return

        if self.type == 'localized':
            value = values['value']
            previous = getattr(self, 'value')

            if previous and isinstance(previous, dict):
                previous.update(value)
            else:
                setattr(self, 'value', value)
        else:
            setattr(self, 'value', unicode(values['value']))


class FieldOption(ModelWithTIDandID):
    field_id = Unicode()
    presentation_order = Int(default=0)
    label = JSON()
    score_points = Int(default=0)
    trigger_field = Unicode()

    unicode_keys = ['field_id']
    int_keys = ['presentation_order', 'score_points']
    localized_keys = ['label']
    optional_references = ['trigger_field']


class FieldAnswer(ModelWithTIDandID):
    internaltip_id = Unicode()
    fieldanswergroup_id = Unicode()
    key = Unicode(default=u'')
    is_leaf = Bool(default=True)
    value = Unicode(default=u'')

    unicode_keys = ['internaltip_id', 'key', 'value']
    bool_keys = ['is_leaf']


class FieldAnswerGroup(ModelWithTIDandID):
    number = Int(default=0)
    fieldanswer_id = Unicode()

    unicode_keys = ['fieldanswer_id']
    int_keys = ['number']


class Step(ModelWithTIDandID):
    questionnaire_id = Unicode()
    label = JSON()
    description = JSON()
    presentation_order = Int(default=0)

    unicode_keys = ['questionnaire_id']
    int_keys = ['presentation_order']
    localized_keys = ['label', 'description']


class Questionnaire(ModelWithTIDandID):
    name = Unicode(default=u'')
    enable_whistleblower_identity = Bool(default=False)
    editable = Bool(default=True)

    # TODO: this variables are unused and should be removed at next migration
    show_steps_navigation_bar = Bool(default=False)
    steps_navigation_requires_completion = Bool(default=False)

    unicode_keys = ['name']

    bool_keys = [
      'editable'
    ]

    list_keys = ['steps']


class ArchivedSchema(Model):
    __storm_primary__ = 'hash', 'type'

    hash = Unicode()
    type = Unicode()
    schema = JSON()

    unicode_keys = ['hash']


class Stats(ModelWithTIDandID):
    start = DateTime()
    summary = JSON()


class Anomalies(ModelWithTIDandID):
    date = DateTime()
    alarm = Int()
    events = JSON()


class SecureFileDelete(Model):
    filepath = Unicode(primary=True)


# Follow classes used for Many to Many references
class ReceiverContext(ModelWithTID):
    """
    Class used to implement references between Receivers and Contexts
    """
    __storm_table__ = 'receiver_context'
    __storm_primary__ = 'tid', 'context_id', 'receiver_id'

    unicode_keys = ['context_id', 'receiver_id']
    int_keys = ['presentation_order']

    context_id = Unicode()
    receiver_id = Unicode()
    presentation_order = Int(default=0)


class Counter(ModelWithTID):
    """
    Class used to implement unique counters
    """
    __storm_primary__ = 'tid', 'key'

    key = Unicode(primary=True)
    counter = Int(default=1)
    update_date = DateTime(default_factory=datetime_now)

    unicode_keys = ['key']
    int_keys = ['number']


class ShortURL(ModelWithTIDandID):
    """
    Class used to implement url shorteners
    """
    shorturl = Unicode()
    longurl = Unicode()

    unicode_keys = ['shorturl', 'longurl']


class File(ModelWithTIDandID):
    """
    Class used for storing files
    """
    name = Unicode(default=u'')
    data = Unicode(default=u'')

    unicode_keys = ['data', 'name']


class UserImg(ModelWithTIDandID):
    """
    Class used for storing user pictures
    """
    data = Unicode()

    unicode_keys = ['data']


class ContextImg(ModelWithTIDandID):
    """
    Class used for storing context pictures
    """
    data = Unicode()

    unicode_keys = ['data']


class CustomTexts(ModelWithTID):
    """
    Class used to implement custom texts
    """
    __storm_primary__ = 'tid', 'lang'

    lang = Unicode()
    texts = JSON()

    unicode_keys = ['lang']
    json_keys = ['texts']
