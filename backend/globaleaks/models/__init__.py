# -*- coding: UTF-8
"""
GlobaLeaks ORM Models definitions.
"""
from __future__ import absolute_import

from storm.expr import And
from storm.locals import Bool, Int, Reference, ReferenceSet, Unicode, Storm, JSON

from .properties import MetaModel, DateTime

from globaleaks import __version__, DATABASE_VERSION, LANGUAGES_SUPPORTED_CODES

from globaleaks.orm import transact
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import datetime_now, datetime_null, uuid4
from globaleaks.utils.validator import shorttext_v, longtext_v, \
    shortlocal_v, longlocal_v, shorturl_v, longurl_v

empty_localization = {}

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
    localized_keys = []
    int_keys = []
    bool_keys = []
    datetime_keys = []
    json_keys = []

    def __init__(self, values=None):
        self.update(values)

    @classmethod
    def new(cls, store, values=None):
        """
        Add a new object to the store, filling its data with the attributes
        given.

        :param store:
        :param attrs: The dictionary containing initial values for the
        """
        obj = cls(values)
        store.add(obj)
        return obj

    def update(self, values=None):
        """
        Updated Models attributes from dict.
        """
        # May raise ValueError and AttributeError
        if values is None:
            return

        for k in getattr(self, "unicode_keys"):
            if k in values and values[k] is not None:
                value = unicode(values[k])
                setattr(self, k, value)

        for k in getattr(self, "int_keys"):
            if k in values and values[k] is not None:
                value = int(values[k])
                setattr(self, k, value)

        for k in getattr(self, "datetime_keys"):
            if k in values and values[k] is not None:
                value = values[k]
                setattr(self, k, value)

        for k in getattr(self, "bool_keys"):
            if k in values and values[k] is not None:
                if values[k] == u'true':
                    value = True
                elif values[k] == u'false':
                    value = False
                else:
                    value = bool(values[k])
                setattr(self, k, value)

        for k in getattr(self, "localized_keys"):
            if k in values and values[k] is not None:
                value = values[k]
                previous = getattr(self, k)

                if previous and isinstance(previous, dict):
                    previous.update(value)
                    setattr(self, k, previous)
                else:
                    setattr(self, k, value)

        for k in getattr(self, "json_keys"):
            if k in values and values[k] is not None:
                value = values[k]
                setattr(self, k, value)


    def __repr___(self):
        values = ['{}={}'.format(attr, getattr(self, attr)) for attr in self._public_attrs]
        return '<%s model with values %s>' % (self.__name__, ', '.join(values))

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
    Base class for working the database, already integrating an id.
    """
    __storm_table__ = None
    id = Unicode(primary=True, default_factory=uuid4)

    @classmethod
    def get(cls, store, obj_id):
        return store.find(cls, cls.id == obj_id).one()

    @classmethod
    def delete(cls, store):
        store.remove(cls)


class User(Model):
    """
    This model keeps track of globaleaks users.
    """
    creation_date = DateTime(default_factory=datetime_now)

    username = Unicode(validator=shorttext_v)

    password = Unicode()
    salt = Unicode()

    deletable = Bool(default=True)

    name = Unicode(validator=shorttext_v)
    description = JSON(validator=longlocal_v)

    role = Unicode()
    state = Unicode()
    last_login = DateTime(default_factory=datetime_null)
    mail_address = Unicode()
    language = Unicode()
    timezone = Int()
    password_change_needed = Bool(default=True)
    password_change_date = DateTime(default_factory=datetime_null)

    # roles: 'admin', 'receiver', 'custodian'
    # states: 'disabled', 'enabled'

    # BEGIN of PGP key fields
    pgp_key_info = Unicode(default=u'')
    pgp_key_fingerprint = Unicode(default=u'')
    pgp_key_public = Unicode(default=u'')
    pgp_key_expiration = DateTime(default_factory=datetime_null)
    pgp_key_status = Unicode(default=u'disabled') # 'disabled', 'enabled'
    # END of PGP key fields

    unicode_keys = ['username', 'password', 'salt', 'role',
                    'state', 'language', 'mail_address',
                    'name']

    localized_keys = ['description']

    int_keys = ['timezone', 'password_change_needed']

    bool_keys = ['deletable']


class Context(Model):
    """
    This model keeps track of contexts settings.
    """
    show_small_cards = Bool(default=False)
    show_context = Bool(default=True)
    show_recipients_details = Bool(default=False)
    allow_recipients_selection = Bool(default=False)
    maximum_selectable_receivers = Int(default=0)
    select_all_receivers = Bool(default=False)

    enable_comments = Bool(default=True)
    enable_messages = Bool(default=False)
    enable_two_way_comments = Bool(default=True)
    enable_two_way_messages = Bool(default=True)
    enable_attachments = Bool(default=True)
    enable_whistleblower_identity = Bool(default=False)

    tip_timetolive = Int()

    # localized strings
    name = JSON(validator=shortlocal_v)
    description = JSON(validator=longlocal_v)
    recipients_clarification = JSON(validator=longlocal_v)

    questionnaire_layout = Unicode(default=u'horizontal')

    show_receivers_in_alphabetical_order = Bool(default=False)

    presentation_order = Int(default=0)

    unicode_keys = ['questionnaire_layout']

    localized_keys = ['name', 'description', 'recipients_clarification']

    int_keys = ['tip_timetolive',
                'maximum_selectable_receivers',
                'show_receivers_in_alphabetical_order',
                'presentation_order' ]

    bool_keys = [
      'select_all_receivers',
      'show_small_cards',
      'show_context',
      'show_recipients_details',
      'allow_recipients_selection',
      'enable_comments',
      'enable_messages',
      'enable_two_way_comments',
      'enable_two_way_messages',
      'enable_attachments'
    ]

class InternalTip(Model):
    """
    This is the internal representation of a Tip that has been submitted to the
    GlobaLeaks node.

    It has a not associated map for keep track of Receivers, Tips,
    Comments and WhistleblowerTip.
    All of those element has a Storm Reference with the InternalTip.id,
    never vice-versa
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

    new = Int(default=True)


class ReceiverTip(Model):
    """
    This is the table keeping track of ALL the receivers activities and
    date in a Tip, Tip core data are stored in StoredTip. The data here
    provide accountability of Receiver accesses, operations, options.
    """
    internaltip_id = Unicode()
    receiver_id = Unicode()

    last_access = DateTime(default_factory=datetime_null)
    access_counter = Int(default=0)

    label = Unicode(default=u"")

    can_access_whistleblower_identity = Bool(default=False)

    new = Int(default=True)

    unicode_keys = ['label']


class WhistleblowerTip(Model):
    """
    WhisteleblowerTip is intended, to provide a whistleblower access to the
    Tip. It has some differencies from the ReceiverTips: It has a secret
    authentication receipt and different capabilities, like: cannot not
    download.
    """
    internaltip_id = Unicode()
    receipt_hash = Unicode()

    last_access = DateTime(default_factory=datetime_null)
    access_counter = Int(default=0)


class IdentityAccessRequest(Model):
    """
    This model keeps track of identity access requests by receivers and
    of the answers by custodians.
    """
    receivertip_id = Unicode()
    request_date = DateTime(default_factory=datetime_now)
    request_motivation = Unicode(default=u"")
    reply_date = DateTime(default_factory=datetime_null)
    reply_user_id = Unicode()
    reply_motivation = Unicode(default=u"")
    reply = Unicode(default=u"pending")


class InternalFile(Model):
    """
    This model keeps track of files before they are packaged
    for specific receivers.
    """
    creation_date = DateTime(default_factory=datetime_now)

    internaltip_id = Unicode()

    name = Unicode(validator=longtext_v)
    file_path = Unicode()

    content_type = Unicode()
    size = Int()

    new = Int(default=True)
    
    submission = Int(default = False)

    processing_attempts = Int(default=0)


class ReceiverFile(Model):
    """
    This model keeps track of files destinated to a specific receiver
    """
    internaltip_id = Unicode()
    internalfile_id = Unicode()
    receiver_id = Unicode()
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


class Comment(Model):
    """
    This table handle the comment collection, has an InternalTip referenced
    """
    creation_date = DateTime(default_factory=datetime_now)

    internaltip_id = Unicode()

    author = Unicode()
    content = Unicode(validator=longtext_v)

    type = Unicode()
    # types: 'receiver', 'whistleblower'

    new = Int(default=True)


class Message(Model):
    """
    This table handle the direct messages between whistleblower and one
    Receiver.
    """
    creation_date = DateTime(default_factory=datetime_now)

    receivertip_id = Unicode()
    author = Unicode()
    content = Unicode(validator=longtext_v)

    type = Unicode()
    # types: 'receiver', whistleblower'

    new = Int(default=True)


class Node(Model):
    """
    This table has only one instance, has the "id", but would not exists a
    second element of this table. This table acts, more or less, like the
    configuration file of the previous GlobaLeaks release (and some of the GL
    0.1 details are specified in Context)

    This table represent the System-wide settings
    """
    version = Unicode(default=unicode(__version__))
    version_db = Unicode(default=unicode(DATABASE_VERSION))

    name = Unicode(validator=shorttext_v, default=u'')

    public_site = Unicode(validator=shorttext_v, default=u'')
    hidden_service = Unicode(validator=shorttext_v, default=u'')

    receipt_salt = Unicode(validator=shorttext_v)

    languages_enabled = JSON(default=LANGUAGES_SUPPORTED_CODES)
    default_language = Unicode(validator=shorttext_v, default=u'en')
    default_timezone = Int(default=0)

    description = JSON(validator=longlocal_v, default=empty_localization)
    presentation = JSON(validator=longlocal_v, default=empty_localization)
    footer = JSON(validator=longlocal_v, default=empty_localization)
    security_awareness_title = JSON(validator=longlocal_v, default=empty_localization)
    security_awareness_text = JSON(validator=longlocal_v, default=empty_localization)
    context_selector_label = JSON(validator=longlocal_v, default=empty_localization)

    # Advanced settings
    maximum_namesize = Int(default=128)
    maximum_textsize = Int(default=4096)
    maximum_filesize = Int(default=30)
    tor2web_admin = Bool(default=True)
    tor2web_custodian = Bool(default=True)
    tor2web_whistleblower = Bool(default=False)
    tor2web_receiver = Bool(default=True)
    tor2web_unauth = Bool(default=True)
    allow_unencrypted = Bool(default=False)
    allow_iframes_inclusion = Bool(default=False)
    submission_minimum_delay = Int(default=10)
    submission_maximum_ttl = Int(default=10800)

    # privileges of receivers
    can_postpone_expiration = Bool(default=False)
    can_delete_submission = Bool(default=False)
    can_grant_permissions = Bool(default=False)

    ahmia = Bool(default=False)
    wizard_done = Bool(default=False)

    disable_privacy_badge = Bool(default=False)
    disable_security_awareness_badge = Bool(default=False)
    disable_security_awareness_questions = Bool(default=False)
    disable_key_code_hint = Bool(default=False)
    disable_donation_panel = Bool(default=False)

    enable_captcha = Bool(default=True)
    enable_proof_of_work = Bool(default=True)

    enable_experimental_features = Bool(default=False)

    whistleblowing_question = JSON(validator=longlocal_v, default=empty_localization)
    whistleblowing_button = JSON(validator=longlocal_v, default=empty_localization)

    simplified_login = Bool(default=True)

    enable_custom_privacy_badge = Bool(default=False)
    custom_privacy_badge_tor = JSON(validator=longlocal_v, default=empty_localization)
    custom_privacy_badge_none = JSON(validator=longlocal_v, default=empty_localization)

    header_title_homepage = JSON(validator=longlocal_v, default=empty_localization)
    header_title_submissionpage = JSON(validator=longlocal_v, default=empty_localization)
    header_title_receiptpage = JSON(validator=longlocal_v, default=empty_localization)
    header_title_tippage = JSON(validator=longlocal_v, default=empty_localization)

    widget_comments_title = JSON(validator=shortlocal_v, default=empty_localization)
    widget_messages_title = JSON(validator=shortlocal_v, default=empty_localization)
    widget_files_title = JSON(validator=shortlocal_v, default=empty_localization)

    landing_page = Unicode(default=u'homepage')

    show_contexts_in_alphabetical_order = Bool(default=False)

    threshold_free_disk_megabytes_high = Int(default=200)
    threshold_free_disk_megabytes_medium = Int(default=500)
    threshold_free_disk_megabytes_low = Int(default=1000)

    threshold_free_disk_percentage_high = Int(default=3)
    threshold_free_disk_percentage_medium = Int(default=5)
    threshold_free_disk_percentage_low = Int(default=10)

    unicode_keys = [
        'name',
        'public_site',
        'hidden_service',
        'default_language',
        'landing_page'
    ]

    int_keys = [
        'maximum_namesize',
        'maximum_textsize',
        'maximum_filesize',
        'default_timezone',
        'show_contexts_in_alphabetical_order',
        'submission_minimum_delay',
        'submission_maximum_ttl',
        'simplified_login',
        'threshold_free_disk_megabytes_high',
        'threshold_free_disk_megabytes_medium',
        'threshold_free_disk_megabytes_low',
        'threshold_free_disk_percentage_high',
        'threshold_free_disk_percentage_medium',
        'threshold_free_disk_percentage_low'
    ]

    bool_keys = ['tor2web_admin', 'tor2web_receiver', 'tor2web_whistleblower',
                 'tor2web_custodian', 'tor2web_unauth',
                 'can_postpone_expiration', 'can_delete_submission', 'can_grant_permissions',
                 'ahmia', 'allow_unencrypted',
                 'allow_iframes_inclusion',
                 'disable_privacy_badge', 'disable_security_awareness_badge',
                 'disable_security_awareness_questions', 'enable_custom_privacy_badge',
                 'disable_key_code_hint',
                 'disable_donation_panel',
                 'enable_captcha',
                 'enable_proof_of_work',
                 'enable_experimental_features']

    # wizard_done is not checked because it's set by the backend

    localized_keys = [
        'description',
        'presentation',
        'footer',
        'security_awareness_title',
        'security_awareness_text',
        'whistleblowing_question',
        'whistleblowing_button',
        'custom_privacy_badge_tor',
        'custom_privacy_badge_none',
        'header_title_homepage',
        'header_title_submissionpage',
        'header_title_receiptpage',
        'header_title_tippage',
        'context_selector_label',
        'widget_comments_title',
        'widget_messages_title',
        'widget_files_title'
    ]


class Notification(Model):
    """
    This table has only one instance, and contain all the notification
    information for the node templates are imported in the handler, but
    settings are expected all at once.
    """
    server = Unicode(validator=shorttext_v, default=u'demo.globaleaks.org')
    port = Int(default=9267)

    username = Unicode(validator=shorttext_v, default=u'hey_you_should_change_me')
    password = Unicode(validator=shorttext_v, default=u'yes_you_really_should_change_me')

    source_name = Unicode(validator=shorttext_v, default=u'GlobaLeaks - CHANGE EMAIL ACCOUNT USED FOR NOTIFICATION')
    source_email = Unicode(validator=shorttext_v, default=u'notification@demo.globaleaks.org')

    security = Unicode(validator=shorttext_v, default=u"TLS")
    # security_types: 'TLS', 'SSL'

    # Admin
    admin_pgp_alert_mail_title = JSON(validator=longlocal_v)
    admin_pgp_alert_mail_template = JSON(validator=longlocal_v)
    admin_anomaly_mail_template = JSON(validator=longlocal_v)
    admin_anomaly_mail_title = JSON(validator=longlocal_v)
    admin_anomaly_disk_low = JSON(validator=longlocal_v)
    admin_anomaly_disk_medium = JSON(validator=longlocal_v)
    admin_anomaly_disk_high = JSON(validator=longlocal_v)
    admin_anomaly_activities = JSON(validator=longlocal_v)

    # Receiver
    tip_mail_template = JSON(validator=longlocal_v)
    tip_mail_title = JSON(validator=longlocal_v)
    file_mail_template = JSON(validator=longlocal_v)
    file_mail_title = JSON(validator=longlocal_v)
    comment_mail_template = JSON(validator=longlocal_v)
    comment_mail_title = JSON(validator=longlocal_v)
    message_mail_template = JSON(validator=longlocal_v)
    message_mail_title = JSON(validator=longlocal_v)
    tip_expiration_mail_template = JSON(validator=longlocal_v)
    tip_expiration_mail_title = JSON(validator=longlocal_v)
    pgp_alert_mail_title = JSON(validator=longlocal_v)
    pgp_alert_mail_template = JSON(validator=longlocal_v)
    receiver_notification_limit_reached_mail_template = JSON(validator=longlocal_v)
    receiver_notification_limit_reached_mail_title = JSON(validator=longlocal_v)

    export_template = JSON(validator=longlocal_v)
    export_message_recipient = JSON(validator=longlocal_v)
    export_message_whistleblower = JSON(validator=longlocal_v)

    # Whistleblower Identity
    identity_access_authorized_mail_template = JSON(validator=longlocal_v)
    identity_access_authorized_mail_title = JSON(validator=longlocal_v)
    identity_access_denied_mail_template = JSON(validator=longlocal_v)
    identity_access_denied_mail_title = JSON(validator=longlocal_v)
    identity_access_request_mail_template = JSON(validator=longlocal_v)
    identity_access_request_mail_title = JSON(validator=longlocal_v)
    identity_provided_mail_template = JSON(validator=longlocal_v)
    identity_provided_mail_title = JSON(validator=longlocal_v)

    disable_admin_notification_emails = Bool(default=False)
    disable_custodian_notification_emails = Bool(default=False)
    disable_receiver_notification_emails = Bool(default=False)
    send_email_for_every_event = Bool(default=True)

    tip_expiration_threshold = Int(default=72)
    notification_threshold_per_hour = Int(default=20)
    notification_suspension_time=Int(default=(2 * 3600))

    exception_email_address = Unicode(validator=shorttext_v, default=u"globaleaks-stackexception@lists.globaleaks.org")
    exception_email_pgp_key_info = Unicode(default=u'')
    exception_email_pgp_key_fingerprint = Unicode(default=u'')
    exception_email_pgp_key_public = Unicode(default=u'')
    exception_email_pgp_key_expiration = DateTime(default_factory=datetime_null)
    exception_email_pgp_key_status = Unicode(default=u'disabled')

    unicode_keys = [
        'server',
        'username',
        'password',
        'source_name',
        'source_email',
        'security',
        'exception_email_address'
    ]

    localized_keys = [
        'admin_anomaly_mail_title',
        'admin_anomaly_mail_template',
        'admin_anomaly_disk_low',
        'admin_anomaly_disk_medium',
        'admin_anomaly_disk_high',
        'admin_anomaly_activities',
        'admin_pgp_alert_mail_title',
        'admin_pgp_alert_mail_template',
        'pgp_alert_mail_title',
        'pgp_alert_mail_template',
        'tip_mail_template',
        'tip_mail_title',
        'file_mail_template',
        'file_mail_title',
        'comment_mail_template',
        'comment_mail_title',
        'message_mail_template',
        'message_mail_title',
        'tip_expiration_mail_template',
        'tip_expiration_mail_title',
        'receiver_notification_limit_reached_mail_template',
        'receiver_notification_limit_reached_mail_title',
        'identity_access_authorized_mail_template',
        'identity_access_authorized_mail_title',
        'identity_access_denied_mail_template',
        'identity_access_denied_mail_title',
        'identity_access_request_mail_template',
        'identity_access_request_mail_title',
        'identity_provided_mail_template',
        'identity_provided_mail_title',
        'export_template',
        'export_message_whistleblower',
        'export_message_recipient'
    ]

    int_keys = [
        'port',
        'tip_expiration_threshold',
        'notification_threshold_per_hour',
        'notification_suspension_time',
    ]

    bool_keys = [
        'disable_admin_notification_emails',
        'disable_receiver_notification_emails',
        'send_email_for_every_event'
    ]


class Mail(Model):
    """
    This model keeps track of emails to be spooled by the system
    """
    creation_date = DateTime(default_factory=datetime_now)

    address = Unicode()
    subject = Unicode()
    body = Unicode()

    processing_attempts = Int(default=0)

    unicode_keys = ['address', 'subject', 'body']


class Custodian(Model):
    """
    This model keeps track of custodians settings.
    """
    # currently custodians do not need special settings but
    # but the model is anyhow needed in order to allow the grouping
    pass


class Receiver(Model):
    """
    This model keeps track of receivers settings.
    """
    configuration = Unicode(default=u"default")
    # configurations: 'default', 'forcefully_selected', 'unselectable'

    # Admin chosen options
    can_delete_submission = Bool(default=False)
    can_postpone_expiration = Bool(default=False)
    can_grant_permissions = Bool(default=False)

    tip_notification = Bool(default=True)

    presentation_order = Int(default=0)

    unicode_keys = ['configuration']

    int_keys = ['presentation_order']

    bool_keys = [
        'can_delete_submission',
        'can_postpone_expiration',
        'can_grant_permissions',
        'tip_notification',
    ]


class Field(Model):
    x = Int(default=0)
    y = Int(default=0)
    width = Int(default = 0)

    key = Unicode(default=u"")

    label = JSON(validator=longlocal_v)
    description = JSON(validator=longlocal_v)
    hint = JSON(validator=longlocal_v)

    required = Bool(default=False)
    preview = Bool(default=False)

    multi_entry = Bool(default=False)
    multi_entry_hint = JSON(validator=shortlocal_v)

    # This is set if the field should be duplicated for collecting statistics
    # when encryption is enabled.
    stats_enabled = Bool(default=False)

    activated_by_score = Int(default=0)

    # This reference when != NULL means
    # that the field is referencing a template
    template_id = Unicode()

    type = Unicode(default=u'inputbox')

    instance = Unicode(default=u'instance')
    editable = Bool(default=True)

    unicode_keys = ['type', 'instance', 'key']
    int_keys = ['x', 'y', 'width', 'activated_by_score']
    localized_keys = ['label', 'description', 'hint', 'multi_entry_hint']
    bool_keys = ['editable', 'multi_entry', 'preview', 'required', 'stats_enabled']

    def delete(self, store):
        for child in self.children:
            child.delete(store)
        store.remove(self)


class FieldAttr(Model):
    field_id = Unicode()
    name = Unicode()
    type = Unicode()
    value = JSON()

    # FieldAttr is a special model.
    # Here we consider all its attributes as unicode, then
    # depending on the type we handle the value as a localized value
    unicode_keys = ['field_id', 'name', 'type', 'value']

    def update(self, values=None):
        """
        Updated Models attributes from dict.
        """
        # May raise ValueError and AttributeError
        if values is None:
            return

        setattr(self, 'field_id', unicode(values['field_id']))
        setattr(self, 'name', unicode(values['name']))
        setattr(self, 'type', unicode(values['type']))

        if self.type == 'localized':
            value = values['value']
            previous = getattr(self, 'value')

            if previous and isinstance(previous, dict):
                previous.update(value)
                setattr(self, 'value', previous)
            else:
                setattr(self, 'value', value)
        else:
            setattr(self, 'value', unicode(values['value']))


class FieldOption(Model):
    field_id = Unicode()
    presentation_order = Int(default=0)
    label = JSON()
    score_points = Int(default=0)

    unicode_keys = ['field_id']
    int_keys = ['presentation_order', 'score_points']
    localized_keys = ['label']


class OptionActivateField(BaseModel):
    __storm_primary__ = 'option_id', 'field_id'

    option_id = Unicode()
    field_id = Unicode()

    unicode_keys = ['option_id', 'field_id']


class OptionActivateStep(BaseModel):
    __storm_primary__ = 'option_id', 'step_id'

    option_id = Unicode()
    step_id = Unicode()

    unicode_keys = ['option_id', 'step_id']


class FieldAnswer(Model):
    internaltip_id = Unicode()
    key = Unicode(default=u'')
    is_leaf = Bool(default=True)
    value = Unicode(default=u'')

    unicode_keys = ['internaltip_id', 'key', 'value']
    bool_keys = ['is_leaf']


class FieldAnswerGroup(Model):
    number = Int(default=0)
    fieldanswer_id = Unicode()

    unicode_keys = ['fieldanswer_id']
    int_keys = ['number']


class ArchivedSchema(Model):
    hash = Unicode()
    type = Unicode()
    schema = JSON()

    unicode_keys = ['hash']


class Step(Model):
    context_id = Unicode()
    label = JSON()
    description = JSON()
    presentation_order = Int(default=0)

    unicode_keys = ['context_id']
    int_keys = ['presentation_order']
    localized_keys = ['label', 'description']

    def delete(self, store):
        for child in self.children:
            child.delete(store)
        store.remove(self)


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


class StepField(BaseModel):
    """
    Class used to implement references between Steps and Fields!
    """
    __storm_table__ = 'step_field'
    __storm_primary__ = 'step_id', 'field_id'

    step_id = Unicode()
    field_id = Unicode()

    unicode_keys = ['step_id', 'field_id']


class Stats(Model):
    start = DateTime()
    summary = JSON()
    free_disk_space = Int()


class Anomalies(Model):
    date = DateTime()
    alarm = Int()
    events = JSON()


class SecureFileDelete(Model):
    filepath = Unicode()


class ApplicationData(Model):
    version = Int()
    default_questionnaire = JSON()

    int_keys = ['version']
    json_keys = ['default_questionnaire']


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


class FieldAnswerGroupFieldAnswer(BaseModel):
    """
    Class used to implement references between FieldAnswerGroup and FieldAnswer
    """
    __storm_table__ = 'fieldanswergroup_fieldanswer'
    __storm_primary__ = 'fieldanswergroup_id', 'fieldanswer_id'

    fieldanswergroup_id = Unicode()
    fieldanswer_id = Unicode()


class Counter(Model):
    """
    Class used to implement unique counters
    """
    key = Unicode(validator=shorttext_v)
    counter = Int(default=1)
    update_date = DateTime(default_factory=datetime_now)

    unicode_keys = ['key']
    int_keys = ['number']


class ShortURL(Model):
    """
    Class used to implement url shorteners
    """
    shorturl = Unicode(validator=shorturl_v)
    longurl = Unicode(validator=longurl_v)

    unicode_keys = ['shorturl', 'longurl']


Field.template = Reference(Field.template_id, Field.id)

Field.steps = ReferenceSet(
    Field.id,
    StepField.field_id,
    StepField.step_id,
    Step.id
)

Field.fieldgroups = ReferenceSet(
    Field.id,
    FieldField.child_id,
    FieldField.parent_id,
    Field.id
)

Field.options = ReferenceSet(
    Field.id,
    FieldOption.field_id
)

Field.children = ReferenceSet(
    Field.id,
    FieldField.parent_id,
    FieldField.child_id,
    Field.id
)

Field.attrs = ReferenceSet(Field.id, FieldAttr.field_id)

Field.activated_by_options = ReferenceSet(
    Field.id,
    OptionActivateField.field_id,
    OptionActivateField.option_id,
    FieldOption.id
)

Step.activated_by_options = ReferenceSet(
    Step.id,
    OptionActivateStep.step_id,
    OptionActivateStep.option_id,
    FieldOption.id
)

FieldOption.field = Reference(FieldOption.field_id, Field.id)

FieldOption.activated_fields = ReferenceSet(
    FieldOption.id,
    OptionActivateField.option_id,
    OptionActivateField.field_id,
    Field.id
)

FieldOption.activated_steps = ReferenceSet(
    FieldOption.id,
    OptionActivateStep.option_id,
    OptionActivateStep.step_id,
    Step.id
)

FieldAnswer.groups = ReferenceSet(FieldAnswer.id, FieldAnswerGroup.fieldanswer_id)

FieldAnswerGroup.fieldanswers = ReferenceSet(
    FieldAnswerGroup.id,
    FieldAnswerGroupFieldAnswer.fieldanswergroup_id,
    FieldAnswerGroupFieldAnswer.fieldanswer_id,
    FieldAnswer.id
)

Receiver.internaltips = ReferenceSet(
    Receiver.id,
    ReceiverInternalTip.receiver_id,
    ReceiverInternalTip.internaltip_id,
    InternalTip.id
)

Step.children = ReferenceSet(
    Step.id,
    StepField.step_id,
    StepField.field_id,
    Field.id
)

Context.steps = ReferenceSet(Context.id, Step.context_id)

Step.context = Reference(Step.context_id, Context.id)

Custodian.user = Reference(Custodian.id, User.id)
Receiver.user = Reference(Receiver.id, User.id)

Receiver.internaltips = ReferenceSet(
    Receiver.id,
    ReceiverInternalTip.receiver_id,
    ReceiverInternalTip.internaltip_id,
    InternalTip.id
)

InternalTip.receivers = ReferenceSet(
    InternalTip.id,
    ReceiverInternalTip.internaltip_id,
    ReceiverInternalTip.receiver_id,
    Receiver.id
)

InternalTip.context = Reference(
    InternalTip.context_id,
    Context.id
)

InternalTip.answers = ReferenceSet(
    InternalTip.id,
    FieldAnswer.internaltip_id
)

InternalTip.comments = ReferenceSet(
    InternalTip.id,
    Comment.internaltip_id
)

InternalTip.receivertips = ReferenceSet(
    InternalTip.id,
    ReceiverTip.internaltip_id
)

ReceiverTip.messages = ReferenceSet(
    ReceiverTip.id,
    Message.receivertip_id
)

ReceiverTip.identityaccessrequests = ReferenceSet(
    ReceiverTip.id,
    IdentityAccessRequest.receivertip_id
)

InternalTip.internalfiles = ReferenceSet(
    InternalTip.id,
    InternalFile.internaltip_id
)

ReceiverFile.internalfile = Reference(
    ReceiverFile.internalfile_id,
    InternalFile.id
)

ReceiverFile.receiver = Reference(
    ReceiverFile.receiver_id,
    Receiver.id
)

ReceiverFile.internaltip = Reference(
    ReceiverFile.internaltip_id,
    InternalTip.id
)

ReceiverFile.receivertip = Reference(
    ReceiverFile.receivertip_id,
    ReceiverTip.id
)

WhistleblowerTip.internaltip = Reference(
    WhistleblowerTip.internaltip_id,
    InternalTip.id
)

InternalFile.internaltip = Reference(
    InternalFile.internaltip_id,
    InternalTip.id
)

ReceiverTip.internaltip = Reference(ReceiverTip.internaltip_id, InternalTip.id)

ReceiverTip.receiver = Reference(ReceiverTip.receiver_id, Receiver.id)

Receiver.tips = ReferenceSet(Receiver.id, ReceiverTip.receiver_id)

Comment.internaltip = Reference(Comment.internaltip_id, InternalTip.id)

Message.receivertip = Reference(Message.receivertip_id, ReceiverTip.id)

IdentityAccessRequest.receivertip = Reference(
    IdentityAccessRequest.receivertip_id,
    ReceiverTip.id
)

IdentityAccessRequest.reply_user = Reference(
    IdentityAccessRequest.reply_user_id,
    User.id
)

Context.receivers = ReferenceSet(
    Context.id,
    ReceiverContext.context_id,
    ReceiverContext.receiver_id,
    Receiver.id
)

Receiver.contexts = ReferenceSet(
    Receiver.id,
    ReceiverContext.receiver_id,
    ReceiverContext.context_id,
    Context.id
)

model_list = [Node,
               User, Custodian, Receiver,
               Context, ReceiverContext,
               Field, FieldOption, FieldAttr,
               FieldAnswer, FieldAnswerGroup,
               OptionActivateField, OptionActivateStep,
               Step,
               InternalTip, ReceiverTip, WhistleblowerTip,
               Comment, Message,
               InternalFile, ReceiverFile,
               Notification, Mail,
               Stats, Anomalies,
               SecureFileDelete,
               IdentityAccessRequest,
               ArchivedSchema, ApplicationData]
