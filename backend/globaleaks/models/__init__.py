"""
ORM Models definitions.
"""
from __future__ import absolute_import

import collections
import copy

from globaleaks.models.properties import *
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.utils.security import generateRandomKey
from globaleaks.utils.utility import datetime_now, datetime_null, datetime_to_ISO8601


def get_auth_token():
    return unicode(generateRandomKey(32))


def db_forge_obj(session, mock_class, mock_fields):
    obj = mock_class(mock_fields)
    session.add(obj)
    session.flush()
    return obj


@transact
def forge_obj(session, mock_class, mock_fields):
    return db_forge_obj(session, mock_class, mock_fields)


def db_get(session, model, *args, **kwargs):
    if isinstance(model, collections.Iterable):
        ret = session.query(*model).filter(*args, **kwargs).one_or_none()
    else:
        ret = session.query(model).filter(*args, **kwargs).one_or_none()

    if ret is None:
        raise errors.ModelNotFound(model)

    return ret


@transact
def get(session, model, *args, **kwargs):
    return db_get(session, model, *args, **kwargs)


def db_delete(session, model, *args, **kwargs):
    if isinstance(model, collections.Iterable):
        q = session.query(*model).filter(*args, **kwargs).one_or_none()
    else:
        q = session.query(model).filter(*args, **kwargs).one_or_none()

    if q is not None:
        session.query(model).filter(model.id == q.id).delete(synchronize_session='fetch')


@transact
def delete(session, model, *args, **kwargs):
    return db_delete(session, model, *args, **kwargs)



Base = declarative_base()


class Model(object):
    """
    Base ORM model
    """
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

        self.properties =  [c.key for c in self.__table__.columns]

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
                previous = copy.deepcopy(getattr(self, k))

                if previous and isinstance(previous, dict):
                    previous.update(value)
                    value = previous

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

            if value is not None:
                if k in self.localized_keys:
                    ret[k] = value[language] if language in value else u''

                elif k in self.date_keys:
                    ret[k] = datetime_to_ISO8601(value)
            else:
                if self.__table__.columns[k].default and not callable(self.__table__.columns[k].default.arg):
                    ret[k] = self.__table__.columns[k].default.arg
                else:
                    ret[k] = ''

        for k in self.list_keys:
            ret[k] = []

        return ret


class Tenant(Model, Base):
    """
    Class used to implement tenants
    """
    __tablename__ = 'tenant'

    id = Column(Integer, primary_key=True, nullable=False)

    label = Column(UnicodeText, default=u'', nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    subdomain = Column(UnicodeText, default=u'', nullable=False)

    unicode_keys = ['label', 'subdomain']
    bool_keys = ['active']


class Signup(Model, Base):
    __tablename__ = 'signup'

    id = Column(Integer, primary_key=True, nullable=False)
    tid = Column(Integer, ForeignKey('tenant.id', ondelete='SET NULL'))
    subdomain = Column(UnicodeText, unique=True, nullable=False)
    name = Column(UnicodeText, nullable=False)
    surname = Column(UnicodeText, nullable=False)
    email = Column(UnicodeText, nullable=False)
    use_case = Column(UnicodeText, nullable=False)
    use_case_other = Column(UnicodeText, nullable=False)
    language = Column(UnicodeText, nullable=False)
    activation_token = Column(UnicodeText, nullable=False)
    registration_date = Column(DateTime, default=datetime_now, nullable=False)

    unicode_keys = ['subdomain', 'name', 'surname', 'email', 'activation_token', 'use_case', 'use_case_other', 'language']


class EnabledLanguage(Model, Base):
    __tablename__ = 'enabledlanguage'

    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), primary_key=True, default=1, nullable=False)
    name = Column(Unicode(5), primary_key=True, nullable=False)

    def __init__(self, tid=1, name=None, migrate=False):
        if migrate:
            return

        self.tid = tid
        self.name = unicode(name)

    @classmethod
    def list(cls, session, tid):
        return [x[0] for x in session.query(EnabledLanguage.name).filter(EnabledLanguage.tid == tid)]

    @classmethod
    def tid_list(cls, session, tid_list):
        return [(lang.tid, lang.name) for lang in session.query(EnabledLanguage).filter(EnabledLanguage.tid.in_(tid_list)).order_by('tid', 'name')]


class User(Model, Base):
    """
    This model keeps track of users.
    """
    __tablename__ = 'user'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), default=1, nullable=False)

    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    username = Column(UnicodeText, default=u'', nullable=False)
    password = Column(UnicodeText, default=u'', nullable=False)
    salt = Column(Unicode(24), nullable=False)
    name = Column(UnicodeText, default=u'', nullable=False)
    description = Column(JSON, default=dict, nullable=False)

    # roles: 'admin', 'receiver', 'custodian'
    role = Column(UnicodeText, default=u'receiver', nullable=False)
    state = Column(UnicodeText, default=u'enabled', nullable=False)
    last_login = Column(DateTime, default=datetime_null, nullable=False)
    mail_address = Column(UnicodeText, default=u'', nullable=False)
    language = Column(UnicodeText, nullable=False)
    password_change_needed = Column(Boolean, default=True, nullable=False)
    password_change_date = Column(DateTime, default=datetime_null, nullable=False)

    auth_token = Column(UnicodeText, default=get_auth_token, nullable=False)

    # BEGIN of PGP key fields
    pgp_key_fingerprint = Column(UnicodeText, default=u'', nullable=False)
    pgp_key_public = Column(UnicodeText, default=u'', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_null, nullable=False)
    # END of PGP key fields

    __table_args__ = (CheckConstraint(role.in_(['admin','receiver', 'custodian'])), \
                      CheckConstraint(state.in_(['disabled', 'enabled'])))

    unicode_keys = ['username', 'role', 'state',
                    'language', 'mail_address', 'name',
                    'language']

    localized_keys = ['description']

    bool_keys = ['password_change_needed']

    date_keys = ['creation_date', 'last_login', 'password_change_date', 'pgp_key_expiration']


class Context(Model, Base):
    """
    This model keeps track of contexts settings.
    """
    __tablename__ = 'context'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), default=1, nullable=False)

    show_small_receiver_cards = Column(Boolean, default=False, nullable=False)
    show_context = Column(Boolean, default=True, nullable=False)
    show_recipients_details = Column(Boolean, default=False, nullable=False)
    allow_recipients_selection = Column(Boolean, default=False, nullable=False)
    maximum_selectable_receivers = Column(Integer, default=0, nullable=False)
    select_all_receivers = Column(Boolean, default=True, nullable=False)
    enable_comments = Column(Boolean, default=True, nullable=False)
    enable_messages = Column(Boolean, default=False, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_two_way_messages = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    enable_rc_to_wb_files = Column(Boolean, default=False, nullable=False)
    tip_timetolive = Column(Integer, default=15, nullable=False)
    name = Column(JSON, default=dict, nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    recipients_clarification = Column(JSON, default=dict, nullable=False)
    status_page_message = Column(JSON, default=dict, nullable=False)
    show_receivers_in_alphabetical_order = Column(Boolean, default=True, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)

    questionnaire_id = Column(Unicode(36), ForeignKey('questionnaire.id'), default=u'default', nullable=False)

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


class InternalTip(Model, Base):
    """
    This is the internal representation of a Tip that has been submitted
    """
    __tablename__ = 'internaltip'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), default=1, nullable=False)

    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    update_date = Column(DateTime, default=datetime_now, nullable=False)
    context_id = Column(Unicode(36), ForeignKey('context.id', ondelete='CASCADE'), nullable=False)
    questionnaire_hash = Column(Unicode(64), ForeignKey('archivedschema.hash', ondelete='CASCADE'), nullable=False)
    preview = Column(JSON, nullable=False)
    progressive = Column(Integer, default=0, nullable=False)
    https = Column(Boolean, default=False, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    identity_provided = Column(Boolean, default=False, nullable=False)
    identity_provided_date = Column(DateTime, default=datetime_null, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_two_way_messages = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    enable_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    receipt_hash = Column(Unicode(128), nullable=False)
    wb_last_access = Column(DateTime, default=datetime_now, nullable=False)
    wb_access_counter = Column(Integer, default=0, nullable=False)


class ReceiverTip(Model, Base):
    """
    This is the table keeping track of ALL the receivers activities and
    date in a Tip, Tip core data are stored in StoredTip. The data here
    provide accountability of Receiver accesses, operations, options.
    """
    __tablename__ = 'receivertip'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    internaltip_id = Column(Unicode(36), ForeignKey('internaltip.id', ondelete='CASCADE'), nullable=False)
    receiver_id = Column(Unicode(36), ForeignKey('receiver.id', ondelete='CASCADE'), nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    access_counter = Column(Integer, default=0, nullable=False)
    label = Column(UnicodeText, default=u'', nullable=False)
    can_access_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    enable_notifications = Column(Boolean, default=True, nullable=False)

    unicode_keys = ['label']

    bool_keys = ['enable_notifications']


class IdentityAccessRequest(Model, Base):
    """
    This model keeps track of identity access requests by receivers and
    of the answers by custodians.
    """
    __tablename__ = 'identityaccessrequest'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    receivertip_id = Column(Unicode(36), ForeignKey('receivertip.id', ondelete='CASCADE'), nullable=False)
    request_date = Column(DateTime, default=datetime_now, nullable=False)
    request_motivation = Column(UnicodeText, default=u'')
    reply_date = Column(DateTime, default=datetime_null, nullable=False)
    reply_user_id = Column(Unicode(36), default=u'', nullable=False)
    reply_motivation = Column(UnicodeText, default=u'', nullable=False)
    reply = Column(UnicodeText, default=u'pending', nullable=False)


class InternalFile(Model, Base):
    """
    This model keeps track of submission files
    """
    __tablename__ = 'internalfile'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    internaltip_id = Column(Unicode(36), ForeignKey('internaltip.id', ondelete='CASCADE'), nullable=False)
    name = Column(UnicodeText, nullable=False)
    file_path = Column(UnicodeText, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    size = Column(Integer, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    submission = Column(Integer, default = False, nullable=False)
    processing_attempts = Column(Integer, default=0, nullable=False)


class ReceiverFile(Model, Base):
    """
    This model keeps track of files destinated to a specific receiver
    """
    __tablename__ = 'receiverfile'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    internalfile_id = Column(Unicode(36), ForeignKey('internalfile.id', ondelete='CASCADE'), nullable=False)
    receivertip_id = Column(Unicode(36), ForeignKey('receivertip.id', ondelete='CASCADE'), nullable=False)
    file_path = Column(UnicodeText, nullable=False)
    size = Column(Integer, nullable=False)
    downloads = Column(Integer, default=0, nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    status = Column(UnicodeText, nullable=False)

    __table_args__ = (CheckConstraint(status.in_(['processing', 'reference', 'encrypted', 'unavailable', 'nokey'])),)


class WhistleblowerFile(Model, Base):
    """
    This models stores metadata of files uploaded by recipients intended to be
    delivered to the whistleblower. This file is not encrypted and nor is it
    integrity checked in any meaningful way.
    """
    __tablename__ = 'whistleblowerfile'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    receivertip_id = Column(Unicode(36), ForeignKey('receivertip.id', ondelete='CASCADE'), nullable=False)
    name = Column(UnicodeText, nullable=False)
    file_path = Column(UnicodeText, nullable=False)
    size = Column(Integer, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    downloads = Column(Integer, default=0, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    description = Column(UnicodeText, nullable=False)


class Comment(Model, Base):
    """
    This table handle the comment collection, has an InternalTip referenced
    """
    __tablename__ = 'comment'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    internaltip_id = Column(Unicode(36), ForeignKey('internaltip.id', ondelete='CASCADE'), nullable=False)
    author_id = Column(Unicode(36), ForeignKey('user.id', ondelete='SET NULL'))
    content = Column(UnicodeText, nullable=False)
    type = Column(UnicodeText, nullable=False)
    new = Column(Integer, default=True, nullable=False)


class Message(Model, Base):
    """
    This table handle the direct messages between whistleblower and one
    Receiver.
    """
    __tablename__ = 'message'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    receivertip_id = Column(Unicode(36), ForeignKey('receivertip.id', ondelete='CASCADE'), nullable=False)
    content = Column(UnicodeText, nullable=False)
    type = Column(UnicodeText, nullable=False)
    new = Column(Integer, default=True, nullable=False)

    __table_args__ = (CheckConstraint(type.in_(['receiver', 'whistleblower'])),)


class Mail(Model, Base):
    """
    This model keeps track of emails to be spooled by the system
    """
    __tablename__ = 'mail'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), default=1, nullable=False)

    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    address = Column(UnicodeText, nullable=False)
    subject = Column(UnicodeText, nullable=False)
    body = Column(UnicodeText, nullable=False)
    processing_attempts = Column(Integer, default=0, nullable=False)

    unicode_keys = ['address', 'subject', 'body']


class Receiver(Model, Base):
    """
    This model keeps track of receivers settings.
    """
    __tablename__ = 'receiver'

    id = Column(Unicode(36), ForeignKey('user.id', ondelete='CASCADE'), primary_key=True, default=uuid4, nullable=False)

    configuration = Column(UnicodeText, default=u'default', nullable=False)
    can_delete_submission = Column(Boolean, default=False, nullable=False)
    can_postpone_expiration = Column(Boolean, default=False, nullable=False)
    can_grant_permissions = Column(Boolean, default=False, nullable=False)
    tip_notification = Column(Boolean, default=True, nullable=False)

    __table_args__ = (CheckConstraint(configuration.in_(['default', 'forcefully_selected', 'unselectable'])),)

    unicode_keys = ['configuration']

    bool_keys = [
        'can_delete_submission',
        'can_postpone_expiration',
        'can_grant_permissions',
        'tip_notification',
    ]

    list_keys = ['contexts']


class Field(Model, Base):
    __tablename__ = 'field'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), default=1, nullable=False)

    x = Column(Integer, default=0, nullable=False)
    y = Column(Integer, default=0, nullable=False)
    width = Column(Integer, default=0, nullable=False)

    label = Column(JSON, nullable=False)
    description = Column(JSON, nullable=False)
    hint = Column(JSON, nullable=False)
    required = Column(Boolean, default=False, nullable=False)
    preview = Column(Boolean, default=False, nullable=False)
    multi_entry = Column(Boolean, default=False, nullable=False)
    multi_entry_hint = Column(JSON, nullable=False)
    stats_enabled = Column(Boolean, default=False, nullable=False)
    triggered_by_score = Column(Integer, default=0, nullable=False)

    template_id = Column(Unicode(36), ForeignKey('field.id', ondelete='CASCADE'))
    fieldgroup_id = Column(Unicode(36), ForeignKey('field.id', ondelete='CASCADE'))
    step_id = Column(Unicode(36), ForeignKey('step.id', ondelete='CASCADE'))

    type = Column(UnicodeText, default=u'inputbox', nullable=False)
    instance = Column(UnicodeText, default=u'instance', nullable=False)
    editable = Column(Boolean, default=True, nullable=False)

    __table_args__ = (CheckConstraint(type.in_(['inputbox',
                                                'textarea',
                                                'multichoice',
                                                'selectbox',
                                                'checkbox',
                                                'modal',
                                                'dialog',
                                                'tos',
                                                'fileupload',
                                                'number',
                                                'date',
                                                'email',
                                                'fieldgroup'])), \
                      CheckConstraint(instance.in_(['instance',
                                                    'reference',
                                                    'template'])),)

    unicode_keys = ['type', 'instance', 'key']
    int_keys = ['x', 'y', 'width', 'triggered_by_score']
    localized_keys = ['label', 'description', 'hint', 'multi_entry_hint']
    bool_keys = ['editable', 'multi_entry', 'preview', 'required', 'stats_enabled']
    optional_references = ['template_id', 'step_id', 'fieldgroup_id']


class FieldAttr(Model, Base):
    __tablename__ = 'fieldattr'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    field_id = Column(Unicode(36), ForeignKey('field.id', ondelete='CASCADE'), nullable=False)
    name = Column(UnicodeText, nullable=False)
    type = Column(UnicodeText, nullable=False)
    value = Column(JSON, nullable=False)

    __table_args__ = (CheckConstraint(type.in_(['int',
                                                'bool',
                                                'unicode',
                                                'localized'])),)

    unicode_keys = ['field_id', 'name', 'type']

    def update(self, values=None):
        super(FieldAttr, self).update(values)

        if values is None:
            return

        value = values['value']

        if self.type == 'localized':
            previous = getattr(self, 'value')
            if previous and isinstance(previous, dict):
                previous = copy.deepcopy(previous)
                previous.update(value)
                value = previous

        self.value = value


class FieldOption(Model, Base):
    __tablename__ = 'fieldoption'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    field_id = Column(Unicode(36), ForeignKey('field.id', ondelete='CASCADE'), nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    label = Column(JSON, nullable=False)
    score_points = Column(Integer, default=0, nullable=False)
    trigger_field = Column(Unicode(36), ForeignKey('field.id', ondelete='SET NULL'))

    unicode_keys = ['field_id']
    int_keys = ['presentation_order', 'score_points']
    localized_keys = ['label']
    optional_references = ['trigger_field']


class FieldAnswer(Model, Base):
    __tablename__ = 'fieldanswer'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    internaltip_id = Column(Unicode(36), ForeignKey('internaltip.id', ondelete='CASCADE'), nullable=True)
    fieldanswergroup_id = Column(Unicode(36), ForeignKey('fieldanswergroup.id', ondelete='CASCADE'), nullable=True)
    key = Column(UnicodeText, default=u'', nullable=False)
    is_leaf = Column(Boolean, default=True, nullable=False)
    value = Column(UnicodeText, default=u'', nullable=False)

    unicode_keys = ['internaltip_id', 'key', 'value']
    bool_keys = ['is_leaf']


class FieldAnswerGroup(Model, Base):
    __tablename__ = 'fieldanswergroup'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    number = Column(Integer, default=0, nullable=False)
    fieldanswer_id = Column(Unicode(36), ForeignKey('fieldanswer.id', ondelete='CASCADE'), nullable=False)

    unicode_keys = ['fieldanswer_id']
    int_keys = ['number']


class Step(Model, Base):
    __tablename__ = 'step'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    questionnaire_id = Column(Unicode(36), ForeignKey('questionnaire.id', ondelete='CASCADE'), nullable=True)
    label = Column(JSON, nullable=False)
    description = Column(JSON, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)

    unicode_keys = ['questionnaire_id']
    int_keys = ['presentation_order']
    localized_keys = ['label', 'description']


class Questionnaire(Model, Base):
    __tablename__ = 'questionnaire'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), default=1, nullable=False)

    name = Column(UnicodeText, default=u'', nullable=False)
    enable_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    editable = Column(Boolean, default=True, nullable=False)

    unicode_keys = ['key', 'name']
    bool_keys = ['editable']
    list_keys = ['steps']


class ArchivedSchema(Model, Base):
    __tablename__ = 'archivedschema'

    hash = Column(Unicode(64), primary_key=True, nullable=False)

    schema = Column(JSON, nullable=False)
    preview = Column(JSON, nullable=False)

    unicode_keys = ['hash']


class Stats(Model, Base):
    __tablename__ = 'stats'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), default=1, nullable=False)

    start = Column(DateTime, nullable=False)
    summary = Column(JSON, nullable=False)


class Anomalies(Model, Base):
    __tablename__ = 'anomalies'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), default=1, nullable=False)

    date = Column(DateTime, nullable=False)
    alarm = Column(Integer, nullable=False)
    events = Column(JSON, nullable=False)


class SecureFileDelete(Model, Base):
    __tablename__ = 'securefiledelete'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    filepath = Column(UnicodeText, nullable=False)


class ReceiverContext(Model, Base):
    """
    Class used to implement references between Receivers and Contexts
    """
    __tablename__ = 'receiver_context'

    context_id = Column(Unicode(36), ForeignKey('context.id', ondelete='CASCADE'), primary_key=True, nullable=False)
    receiver_id = Column(Unicode(36), ForeignKey('receiver.id', ondelete='CASCADE'), primary_key=True, nullable=False)

    presentation_order = Column(Integer, default=0, nullable=False)

    unicode_keys = ['context_id', 'receiver_id']
    int_keys = ['presentation_order']


class Counter(Model, Base):
    """
    Class used to implement unique counters
    """
    __tablename__ = 'counter'

    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), primary_key=True, default=1, nullable=False)
    key = Column(Unicode(32), primary_key=True, nullable=False)

    counter = Column(Integer, default=1, nullable=False)
    update_date = Column(DateTime, default=datetime_now, nullable=False)

    unicode_keys = ['key']
    int_keys = ['number']


class ShortURL(Model, Base):
    """
    Class used to implement url shorteners
    """
    __tablename__ = 'shorturl'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), default=1, nullable=False)

    shorturl = Column(UnicodeText, nullable=False)
    longurl = Column(UnicodeText, nullable=False)

    unicode_keys = ['shorturl', 'longurl']


class File(Model, Base):
    """
    Class used for storing files
    """
    __tablename__ = 'file'

    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), primary_key=True, default=1, nullable=False)
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    name = Column(UnicodeText, default=u'', nullable=False)
    data = Column(UnicodeText, nullable=False)

    unicode_keys = ['data', 'name']


class UserImg(Model, Base):
    """
    Class used for storing user pictures
    """
    __tablename__ = 'userimg'

    id = Column(Unicode(36), ForeignKey('user.id', ondelete='CASCADE'), primary_key=True, default=uuid4, nullable=False)

    data = Column(UnicodeText, nullable=False)

    unicode_keys = ['data']


class ContextImg(Model, Base):
    """
    Class used for storing context pictures
    """
    __tablename__ = 'contextimg'

    id = Column(Unicode(36), ForeignKey('context.id', ondelete='CASCADE'), primary_key=True, default=uuid4, nullable=False)

    data = Column(UnicodeText, nullable=False)

    unicode_keys = ['data']


class CustomTexts(Model, Base):
    """
    Class used to implement custom texts
    """
    __tablename__ = 'customtexts'

    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), default=1, nullable=False)

    lang = Column(Unicode(5), primary_key=True, nullable=False)
    texts = Column(JSON, nullable=False)

    unicode_keys = ['lang']
    json_keys = ['texts']
