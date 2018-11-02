"""
ORM Models definitions.
"""
from __future__ import absolute_import

import collections
import copy

from six import binary_type

from globaleaks.models import config_desc
from globaleaks.models.properties import *
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.utils.crypto import generateRandomKey
from globaleaks.utils.utility import datetime_now, datetime_null, datetime_never, datetime_to_ISO8601


def get_random_password():
    return text_type(generateRandomKey(16))


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
        session.query(*model).filter(*args, **kwargs).delete(synchronize_session='fetch')
    else:
        session.query(model).filter(*args, **kwargs).delete(synchronize_session='fetch')

@transact
def delete(session, model, *args, **kwargs):
    return db_delete(session, model, *args, **kwargs)


class LocalizationEngine(object):
    """
    This Class can manage all the localized strings inside
    one Storm object. AKA: manage three language on a single
    stone. Hell fucking yeah, History!
    """

    def __init__(self, keys):
        self._localized_strings = {}
        self._localized_keys = keys

    def acquire_orm_object(self, obj):
        self._localized_strings = {key: getattr(obj, key) for key in self._localized_keys}

    def acquire_multilang_dict(self, obj):
        self._localized_strings = {}
        for key in self._localized_keys:
            value = obj[key] if key in obj else ''
            self._localized_strings[key] = value

    def singlelang_to_multilang_dict(self, obj, language):
        ret = {}

        for key in self._localized_keys:
            ret[key] = {language: obj[key]} if key in obj else {language: ''}

        return ret

    def dump_localized_key(self, key, language):
        if key not in self._localized_strings:
            return ""

        translated_dict = self._localized_strings[key]

        if not isinstance(translated_dict, dict):
            return ""

        if language is None:
            # When language is None we export the full language dictionary
            return translated_dict
        elif language in translated_dict:
            return translated_dict[language]
        else:
            return ""


def fill_localized_keys(dictionary, keys, language):
    if language is not None:
        mo = LocalizationEngine(keys)
        multilang_dict = mo.singlelang_to_multilang_dict(dictionary, language)
        dictionary.update({key: multilang_dict[key] for key in keys})

    return dictionary


def get_localized_values(dictionary, obj, keys, language):
    mo = LocalizationEngine(keys)

    if isinstance(obj, dict):
        mo.acquire_multilang_dict(obj)
    elif isinstance(obj, Model):
        mo.acquire_orm_object(obj)

    if language is not None:
        dictionary.update({key: mo.dump_localized_key(key, language) for key in keys})
    else:
        for key in keys:
            value = mo._localized_strings[key] if key in mo._localized_strings else ''
            dictionary.update({key: value})

    return dictionary


Base = declarative_base()


class Model(object):
    """
    Base ORM model
    """
    # initialize empty list for the base classes
    properties = []
    binary_keys = []
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
                setattr(self, k, text_type(values[k]))

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

    def __setattr__(self, name, value):
        if name not in self.binary_keys and isinstance(value, binary_type):
            value = text_type(value, 'utf-8')

        return super(Model, self).__setattr__(name, value)

    def dict(self, language=None):
        """
        Return a dictionary serialization of the current model.
        """
        ret = {}

        for k in self.properties:
            value = getattr(self, k)

            if value is not None:
                if k in self.localized_keys:
                    if language is not None:
                        ret[k] = value[language] if language in value else u''
                    else:
                        ret[k] = value

                elif k in self.date_keys:
                    ret[k] = datetime_to_ISO8601(value)
            else:
                if self.__table__.columns[k].default and not callable(self.__table__.columns[k].default.arg):
                    ret[k] = self.__table__.columns[k].default.arg
                else:
                    ret[k] = ''

            if isinstance(ret[k], binary_type):
                ret[k] = text_type(ret[k])

        for k in self.list_keys:
            ret[k] = []

        return ret


class _Anomalies(Model):
    __tablename__ = 'anomalies'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, default=1, nullable=False)

    date = Column(DateTime, nullable=False)
    alarm = Column(Integer, nullable=False)
    events = Column(JSON, nullable=False)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _ArchivedSchema(Model):
    __tablename__ = 'archivedschema'

    hash = Column(UnicodeText(64), primary_key=True, nullable=False)

    schema = Column(JSON, nullable=False)
    preview = Column(JSON, nullable=False)

    unicode_keys = ['hash']


class _Comment(Model):
    """
    This table handle the comment collection, has an InternalTip referenced
    """
    __tablename__ = 'comment'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    internaltip_id = Column(UnicodeText(36), nullable=False)
    author_id = Column(UnicodeText(36))
    content = Column(UnicodeText, nullable=False)
    type = Column(UnicodeText, nullable=False)
    new = Column(Integer, default=True, nullable=False)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['internaltip_id'], ['internaltip.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _Config(Model):
    __tablename__ = 'config'
    tid = Column(Integer, primary_key=True, default=1, nullable=False)
    var_name = Column(UnicodeText(64), primary_key=True, nullable=False)
    value = Column(JSON, nullable=False)
    customized = Column(Boolean, default=False, nullable=False)

    def __init__(self, tid=1, name=None, value=None, migrate=False):
        """
        :param value:    This input is passed directly into set_v
        :param migrate:  Added to comply with models.Model constructor which is
                         used to copy every field returned by the ORM from the db
                         from an old_obj to a new one.
        """
        if migrate:
            return

        self.tid = tid
        self.var_name = text_type(name)
        self.set_v(value)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)

    def set_v(self, val):
        desc = config_desc.ConfigDescriptor[self.var_name]
        if val is None:
            val = desc._type()

        if isinstance(desc, config_desc.Unicode) and isinstance(val, binary_type):
            val = text_type(val, 'utf-8')

        if not isinstance(val, desc._type):
            raise ValueError("Cannot assign %s with %s" % (self, type(val)))

        if self.value is not None:
            self.customized = True

        self.value = val

    def get_v(self):
        return self.value


class _ConfigL10N(Model):
    __tablename__ = 'config_l10n'

    tid = Column(Integer, primary_key=True, default=1, nullable=False)
    lang = Column(UnicodeText(5), primary_key=True)
    var_name = Column(UnicodeText(64), primary_key=True)
    value = Column(UnicodeText)
    customized = Column(Boolean, default=False)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid', 'lang'], ['enabledlanguage.tid', 'enabledlanguage.name'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)

    def __init__(self, tid=1, lang_code=None, var_name=None, value='', migrate=False):
        if migrate:
            return

        self.tid = tid
        self.lang = text_type(lang_code)
        self.var_name = text_type(var_name)
        self.value = text_type(value)

    def set_v(self, value):
        value = text_type(value)
        if self.value != value:
            self.value = value
            self.customized = True


class _Context(Model):
    """
    This model keeps track of contexts settings.
    """
    __tablename__ = 'context'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, default=1, nullable=False)

    show_steps_navigation_interface = Column(Boolean, default=True, nullable=False)
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
    tip_timetolive = Column(Integer, default=30, nullable=False)
    name = Column(JSON, default=dict, nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    recipients_clarification = Column(JSON, default=dict, nullable=False)
    status_page_message = Column(JSON, default=dict, nullable=False)
    show_receivers_in_alphabetical_order = Column(Boolean, default=True, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    questionnaire_id = Column(UnicodeText(36), default=u'default', nullable=False)
    additional_questionnaire_id = Column(UnicodeText(36))

    unicode_keys = ['questionnaire_id', 'additional_questionnaire_id']

    localized_keys = [
        'name',
        'description',
        'recipients_clarification',
        'status_page_message'
    ]

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

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                ForeignKeyConstraint(['questionnaire_id'], ['questionnaire.id'], deferrable=True, initially='DEFERRED'))


class _ContextImg(Model):
    """
    Class used for storing context pictures
    """
    __tablename__ = 'contextimg'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    data = Column(UnicodeText, nullable=False)

    unicode_keys = ['data']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['id'], ['context.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _CustomTexts(Model):
    """
    Class used to implement custom texts
    """
    __tablename__ = 'customtexts'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, default=1, nullable=False)

    lang = Column(UnicodeText(5), primary_key=True, nullable=False)
    texts = Column(JSON, nullable=False)

    unicode_keys = ['lang']
    json_keys = ['texts']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _EnabledLanguage(Model):
    __tablename__ = 'enabledlanguage'

    tid = Column(Integer, primary_key=True, default=1, nullable=False)
    name = Column(UnicodeText(5), primary_key=True, nullable=False)

    def __init__(self, tid=1, name=None, migrate=False):
        if migrate:
            return

        self.tid = tid
        self.name = text_type(name)

    @classmethod
    def list(cls, session, tid):
        return [x[0] for x in session.query(EnabledLanguage.name).filter(EnabledLanguage.tid == tid)]

    @classmethod
    def tid_list(cls, session, tid_list):
        return [(lang.tid, lang.name) for lang in session.query(EnabledLanguage).filter(EnabledLanguage.tid.in_(tid_list))]

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _Field(Model):
    __tablename__ = 'field'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, default=1, nullable=False)

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
    triggered_by_score = Column(Integer, default=0, nullable=False)

    step_id = Column(UnicodeText(36))
    fieldgroup_id = Column(UnicodeText(36))

    type = Column(UnicodeText, default=u'inputbox', nullable=False)
    instance = Column(UnicodeText, default=u'instance', nullable=False)
    editable = Column(Boolean, default=True, nullable=False)

    template_id = Column(UnicodeText(36))
    template_override_id = Column(UnicodeText(36))

    encrypt = Column(Boolean, default=True, nullable=False)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                ForeignKeyConstraint(['step_id'], ['step.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                ForeignKeyConstraint(['fieldgroup_id'], ['field.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                ForeignKeyConstraint(['template_id'], ['field.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                ForeignKeyConstraint(['template_override_id'], ['field.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                CheckConstraint(self.type.in_(['inputbox',
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
                                              'fieldgroup'])),
                CheckConstraint(self.instance.in_(['instance',
                                                  'reference',
                                                  'template'])),)

    unicode_keys = ['type', 'instance', 'key']
    int_keys = ['x', 'y', 'width', 'triggered_by_score']
    localized_keys = ['label', 'description', 'hint', 'multi_entry_hint']
    bool_keys = ['editable', 'multi_entry', 'preview', 'required', 'encrypt']
    optional_references = ['template_id', 'step_id', 'fieldgroup_id']


class _FieldAttr(Model):
    __tablename__ = 'fieldattr'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    field_id = Column(UnicodeText(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    type = Column(UnicodeText, nullable=False)
    value = Column(JSON, nullable=False)

    unicode_keys = ['field_id', 'name', 'type']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['field_id'], ['field.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                CheckConstraint(self.type.in_(['int',
                                               'bool',
                                               'unicode',
                                               'localized'])))


    def update(self, values=None):
        super(_FieldAttr, self).update(values)

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


class _FieldAnswer(Model):
    __tablename__ = 'fieldanswer'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    internaltip_id = Column(UnicodeText(36), nullable=True)
    fieldanswergroup_id = Column(UnicodeText(36), nullable=True)
    key = Column(UnicodeText, default=u'', nullable=False)
    is_leaf = Column(Boolean, default=True, nullable=False)
    value = Column(UnicodeText, default=u'', nullable=False)

    unicode_keys = ['internaltip_id', 'key', 'value']
    bool_keys = ['is_leaf']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['internaltip_id'], ['internaltip.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                ForeignKeyConstraint(['fieldanswergroup_id'], ['fieldanswergroup.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'))


class _FieldAnswerGroup(Model):
    __tablename__ = 'fieldanswergroup'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    number = Column(Integer, default=0, nullable=False)
    fieldanswer_id = Column(UnicodeText(36), nullable=False)

    unicode_keys = ['fieldanswer_id']
    int_keys = ['number']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['fieldanswer_id'], ['fieldanswer.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _FieldOption(Model):
    __tablename__ = 'fieldoption'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    field_id = Column(UnicodeText(36), nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    label = Column(JSON, nullable=False)
    score_points = Column(Integer, default=0, nullable=False)
    trigger_field = Column(UnicodeText(36))

    unicode_keys = ['field_id']
    int_keys = ['presentation_order', 'score_points']
    localized_keys = ['label']
    optional_references = ['trigger_field']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['field_id'], ['field.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                ForeignKeyConstraint(['trigger_field'], ['field.id'], ondelete='SET NULL', deferrable=True, initially='DEFERRED'))


class _File(Model):
    """
    Class used for storing files
    """
    __tablename__ = 'file'

    tid = Column(Integer, primary_key=True, default=1, nullable=False)
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    name = Column(UnicodeText, default=u'', nullable=False)
    data = Column(UnicodeText, nullable=False)

    unicode_keys = ['data', 'name']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _IdentityAccessRequest(Model):
    """
    This model keeps track of identity access requests by receivers and
    of the answers by custodians.
    """
    __tablename__ = 'identityaccessrequest'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    receivertip_id = Column(UnicodeText(36), nullable=False)
    request_date = Column(DateTime, default=datetime_now, nullable=False)
    request_motivation = Column(UnicodeText, default=u'')
    reply_date = Column(DateTime, default=datetime_null, nullable=False)
    reply_user_id = Column(UnicodeText(36), default=u'', nullable=False)
    reply_motivation = Column(UnicodeText, default=u'', nullable=False)
    reply = Column(UnicodeText, default=u'pending', nullable=False)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['receivertip_id'], ['receivertip.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _InternalFile(Model):
    """
    This model keeps track of submission files
    """
    __tablename__ = 'internalfile'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    internaltip_id = Column(UnicodeText(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    filename = Column(UnicodeText(255), nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    size = Column(Integer, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    submission = Column(Integer, default = False, nullable=False)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['internaltip_id'], ['internaltip.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _InternalTip(Model):
    """
    This is the internal representation of a Tip that has been submitted
    """
    __tablename__ = 'internaltip'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, default=1, nullable=False)

    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    update_date = Column(DateTime, default=datetime_now, nullable=False)
    context_id = Column(UnicodeText(36), nullable=False)

    preview = Column(JSON, nullable=False)
    progressive = Column(Integer, default=0, nullable=False)
    https = Column(Boolean, default=False, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_two_way_messages = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    enable_whistleblower_identity = Column(Boolean, default=False, nullable=False)

    additional_questionnaire_id = Column(UnicodeText(36))

    wb_last_access = Column(DateTime, default=datetime_now, nullable=False)
    wb_access_counter = Column(Integer, default=0, nullable=False)

    status = Column(UnicodeText(36), nullable=True)
    substatus = Column(UnicodeText(36), nullable=True)

    crypto_tip_pub_key = Column(LargeBinary(32), default=b'', nullable=False)

    binary_keys = ['crypto_tip_pub_key']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _InternalTipAnswers(Model):
    """
    This is the internal representation of Tip Questionnaire Answers
    """
    __tablename__ = 'internaltipanswers'

    internaltip_id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    questionnaire_hash = Column(UnicodeText(64), primary_key=True)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    encrypted = Column(Boolean, default=False, nullable=False)
    answers = Column(JSON, nullable=False)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['internaltip_id'], ['internaltip.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _InternalTipData(Model):
    __tablename__ = 'InternalTipData'

    internaltip_id = Column(UnicodeText(36), primary_key=True, nullable=False)
    key = Column(UnicodeText, primary_key=True, nullable=False)

    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    value = Column(JSON, nullable=False)
    encrypted = Column(Boolean, default=False, nullable=False)

    @declared_attr
    def __table_args__(self):
        return (UniqueConstraint('internaltip_id', 'key'),
                ForeignKeyConstraint(['internaltip_id'], ['internaltip.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'))


class _Mail(Model):
    """
    This model keeps track of emails to be spooled by the system
    """
    __tablename__ = 'mail'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, default=1, nullable=False)

    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    address = Column(UnicodeText, nullable=False)
    subject = Column(UnicodeText, nullable=False)
    body = Column(UnicodeText, nullable=False)
    processing_attempts = Column(Integer, default=0, nullable=False)

    unicode_keys = ['address', 'subject', 'body']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _Message(Model):
    """
    This table handle the direct messages between whistleblower and one
    Receiver.
    """
    __tablename__ = 'message'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    receivertip_id = Column(UnicodeText(36), nullable=False)
    content = Column(UnicodeText, nullable=False)
    type = Column(UnicodeText, nullable=False)
    new = Column(Integer, default=True, nullable=False)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['receivertip_id'], ['receivertip.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                CheckConstraint(self.type.in_(['receiver', 'whistleblower'])))


class _Questionnaire(Model):
    __tablename__ = 'questionnaire'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, default=1, nullable=False)

    name = Column(UnicodeText, default=u'', nullable=False)
    enable_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    editable = Column(Boolean, default=True, nullable=False)

    unicode_keys = ['key', 'name']
    bool_keys = ['editable']
    list_keys = ['steps']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _Receiver(Model):
    """
    This model keeps track of receivers settings.
    """
    __tablename__ = 'receiver'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    configuration = Column(UnicodeText, default=u'default', nullable=False)
    can_delete_submission = Column(Boolean, default=False, nullable=False)
    can_postpone_expiration = Column(Boolean, default=False, nullable=False)
    can_grant_permissions = Column(Boolean, default=False, nullable=False)
    tip_notification = Column(Boolean, default=True, nullable=False)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['id'], ['user.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                CheckConstraint(self.configuration.in_(['default', 'forcefully_selected', 'unselectable'])))

    unicode_keys = ['configuration']

    bool_keys = [
        'can_delete_submission',
        'can_postpone_expiration',
        'can_grant_permissions',
        'tip_notification',
    ]

    list_keys = ['contexts']


class _ReceiverContext(Model):
    """
    Class used to implement references between Receivers and Contexts
    """
    __tablename__ = 'receiver_context'

    context_id = Column(UnicodeText(36), primary_key=True, nullable=False)
    receiver_id = Column(UnicodeText(36), primary_key=True, nullable=False)

    presentation_order = Column(Integer, default=0, nullable=False)

    unicode_keys = ['context_id', 'receiver_id']
    int_keys = ['presentation_order']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['context_id'], ['context.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                ForeignKeyConstraint(['receiver_id'], ['receiver.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'))


class _ReceiverFile(Model):
    """
    This model keeps track of files destinated to a specific receiver
    """
    __tablename__ = 'receiverfile'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    internalfile_id = Column(UnicodeText(36), nullable=False)
    receivertip_id = Column(UnicodeText(36), nullable=False)
    filename = Column(UnicodeText(255), nullable=False)
    downloads = Column(Integer, default=0, nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    new = Column(Integer, default=True, nullable=True)
    status = Column(UnicodeText, default=u'processing', nullable=False)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['internalfile_id'], ['internalfile.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                ForeignKeyConstraint(['receivertip_id'], ['receivertip.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                CheckConstraint(self.status.in_(['processing', 'reference', 'encrypted', 'unavailable', 'nokey'])))


class _ReceiverTip(Model):
    """
    This is the table keeping track of ALL the receivers activities and
    date in a Tip, Tip core data are stored in StoredTip. The data here
    provide accountability of Receiver accesses, operations, options.
    """
    __tablename__ = 'receivertip'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    internaltip_id = Column(UnicodeText(36), nullable=False)
    receiver_id = Column(UnicodeText(36), nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    access_counter = Column(Integer, default=0, nullable=False)
    label = Column(UnicodeText, default=u'', nullable=False)
    can_access_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    enable_notifications = Column(Boolean, default=True, nullable=False)

    crypto_tip_prv_key = Column(LargeBinary(72), default=b'', nullable=False)

    binary_keys = ['crypto_tip_prv_key']

    unicode_keys = ['label']

    bool_keys = ['enable_notifications']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['receiver_id'], ['receiver.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                ForeignKeyConstraint(['internaltip_id'], ['internaltip.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'))


class _SecureFileDelete(Model):
    __tablename__ = 'securefiledelete'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    filepath = Column(UnicodeText, nullable=False)


class _Signup(Model):
    __tablename__ = 'signup'

    id = Column(Integer, primary_key=True, nullable=False)
    tid = Column(Integer, nullable=False)
    subdomain = Column(UnicodeText, unique=True, nullable=False)
    language = Column(UnicodeText, nullable=False)
    name = Column(UnicodeText, nullable=False)
    surname = Column(UnicodeText, nullable=False)
    role = Column(UnicodeText, default=u'', nullable=False)
    phone = Column(UnicodeText, default=u'', nullable=False)
    email = Column(UnicodeText, nullable=False)
    use_case = Column(UnicodeText, default=u'', nullable=False)
    use_case_other = Column(UnicodeText, default=u'', nullable=False)
    organization_name = Column(UnicodeText, default=u'', nullable=False)
    organization_type = Column(UnicodeText, default=u'', nullable=False)
    organization_location1 = Column(UnicodeText, default=u'', nullable=False)
    organization_location2 = Column(UnicodeText, default=u'', nullable=False)
    organization_location3 = Column(UnicodeText, default=u'', nullable=False)
    organization_location4 = Column(UnicodeText, default=u'', nullable=False)
    organization_site = Column(UnicodeText, default=u'', nullable=False)
    organization_number_employees = Column(UnicodeText, default=u'', nullable=False)
    organization_number_users = Column(UnicodeText, default=u'', nullable=False)
    hear_channel = Column(UnicodeText, default=u'', nullable=False)
    activation_token = Column(UnicodeText, nullable=False)

    client_ip_address = Column(UnicodeText, default=u'', nullable=False)
    client_user_agent = Column(UnicodeText, default=u'', nullable=False)
    registration_date = Column(DateTime, default=datetime_now, nullable=False)
    tos1 = Column(UnicodeText, default=u'', nullable=False)
    tos2 = Column(UnicodeText, default=u'', nullable=False)

    unicode_keys = ['subdomain', 'language', 'name', 'surname', 'role', 'phone', 'email',
                    'use_case', 'use_case_other',
                    'organization_name', 'organization_type', 'organization_site',
                    'organization_location1', 'organization_location2', 'organization_location3', 'organization_location4',
                    'organization_number_employees', 'organization_number_users',
                    'hear_channel',
                    'client_ip_address', 'client_user_agent',
                    'activation_token']

    bool_keys = ['tos1', 'tos2']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _ShortURL(Model):
    """
    Class used to implement url shorteners
    """
    __tablename__ = 'shorturl'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, default=1, nullable=False)

    shorturl = Column(UnicodeText, nullable=False)
    longurl = Column(UnicodeText, nullable=False)

    unicode_keys = ['shorturl', 'longurl']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _Step(Model):
    __tablename__ = 'step'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    questionnaire_id = Column(UnicodeText(36), nullable=True)
    label = Column(JSON, nullable=False)
    description = Column(JSON, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    triggered_by_score = Column(Integer, default=0, nullable=False)

    unicode_keys = ['questionnaire_id']
    int_keys = ['presentation_order']
    localized_keys = ['label', 'description']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['questionnaire_id'], ['questionnaire.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _Stats(Model):
    __tablename__ = 'stats'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, default=1, nullable=False)

    start = Column(DateTime, nullable=False)
    summary = Column(JSON, nullable=False)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _SubmissionStatus(Model):
    """
    Contains the statuses a submission may be in
    """
    __tablename__ = 'submissionstatus'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    label = Column(JSON, nullable=False)

    system_defined = Column(Boolean, nullable=False, default=False)
    system_usage = Column(UnicodeText, nullable=True)

    presentation_order = Column(Integer, default=0, nullable=False)

    localized_keys = [ 'label']
    int_keys = ['presentation_order']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _SubmissionSubStatus(Model):
    """
    Contains the substatuses that a submission may be in
    """
    __tablename__ = 'submissionsubstatus'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    submissionstatus_id = Column(UnicodeText(36), nullable=False)
    label = Column(JSON, nullable=False)

    presentation_order = Column(Integer, default=0, nullable=False)

    localized_keys = [ 'label']
    int_keys = ['presentation_order']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['submissionstatus_id'], ['submissionstatus.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _SubmissionStatusChange(Model):
    """
    Contains a record of all changes of status of a submission
    """

    __tablename__ = 'submissionstatuschange'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    internaltip_id = Column(UnicodeText(36), nullable=False)
    status = Column(UnicodeText(36), nullable=False)
    substatus = Column(UnicodeText(36), nullable=True)
    changed_on = Column(DateTime, default=datetime_now, nullable=False)
    changed_by = Column(UnicodeText(36), nullable=False)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['internaltip_id'], ['internaltip.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _Tenant(Model):
    """
    Class used to implement tenants
    """
    __tablename__ = 'tenant'

    id = Column(Integer, primary_key=True, nullable=False)

    label = Column(UnicodeText, default=u'', nullable=False)
    active = Column(Boolean, default=False, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    subdomain = Column(UnicodeText, default=u'', nullable=False)

    unicode_keys = ['label', 'subdomain']
    bool_keys = ['active']


class _User(Model):
    """
    This model keeps track of users.
    """
    __tablename__ = 'user'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    tid = Column(Integer, default=1, nullable=False)

    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    username = Column(UnicodeText, default=u'', nullable=False)

    salt = Column(UnicodeText(24), nullable=False)
    hash_alg = Column(UnicodeText, default=u'SCRYPT', nullable=False)
    password = Column(UnicodeText, default=u'', nullable=False)

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

    crypto_prv_key = Column(LargeBinary(72), default=b'', nullable=False)
    crypto_pub_key = Column(LargeBinary(32), default=b'', nullable=False)

    can_edit_general_settings = Column(Boolean, default=False, nullable=False)

    change_email_address = Column(UnicodeText, default=u'', nullable=False)
    change_email_token = Column(UnicodeText, unique=True, nullable=True)
    change_email_date = Column(DateTime, default=datetime_never, nullable=False)

    reset_password_token = Column(UnicodeText, unique=True, nullable=True)
    reset_password_date = Column(UnicodeText, default=datetime_never, nullable=False)

    # BEGIN of PGP key fields
    pgp_key_fingerprint = Column(UnicodeText, default=u'', nullable=False)
    pgp_key_public = Column(UnicodeText, default=u'', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_null, nullable=False)
    # END of PGP key fields

    binary_keys = ['crypto_prv_key', 'crypto_pub_key']

    unicode_keys = ['username', 'role', 'state',
                    'language', 'mail_address', 'name',
                    'language', 'change_email_address',
                    'salt']

    localized_keys = ['description']

    bool_keys = ['password_change_needed', 'can_edit_general_settings']

    date_keys = ['creation_date', 'last_login', 'password_change_date', 'pgp_key_expiration']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                UniqueConstraint('tid', 'username'),
                CheckConstraint(self.role.in_(['admin','receiver', 'custodian'])),
                CheckConstraint(self.state.in_(['disabled', 'enabled'])))


class _UserTenant(Model):
    """
    Class used for implementing user-tenant association
    """
    __tablename__ = 'usertenant'

    user_id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tenant_id = Column(Integer, primary_key=True, default=1, nullable=False)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                ForeignKeyConstraint(['tenant_id'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'))


class _UserImg(Model):
    """
    Class used for storing user pictures
    """
    __tablename__ = 'userimg'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    data = Column(UnicodeText, nullable=False)

    unicode_keys = ['data']

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['id'], ['user.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _WhistleblowerFile(Model):
    """
    This models stores metadata of files uploaded by recipients intended to be
    delivered to the whistleblower. This file is not encrypted and nor is it
    integrity checked in any meaningful way.
    """
    __tablename__ = 'whistleblowerfile'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)

    receivertip_id = Column(UnicodeText(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    filename = Column(UnicodeText(255), nullable=False)
    size = Column(Integer, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    downloads = Column(Integer, default=0, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    description = Column(UnicodeText, nullable=False)
    new = Column(Integer, default=True, nullable=True)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['receivertip_id'], ['receivertip.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _WhistleblowerIdentity(Model):
    __tablename__ = 'whistlebloweridentity'

    id = Column(UnicodeText(36), primary_key=True, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    identity = Column(UnicodeText, default=u'', nullable=False)

    @declared_attr
    def __table_args__(self):
        return (ForeignKeyConstraint(['id'], ['internaltip.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),)


class _WhistleblowerTip(Model):
    __tablename__ = 'whistleblowertip'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    receipt_hash = Column(UnicodeText(128), nullable=False)

    hash_alg = Column(UnicodeText, default=u'SCRYPT', nullable=False)

    crypto_prv_key = Column(LargeBinary(72), default=b'', nullable=False)
    crypto_pub_key = Column(LargeBinary(32), default=b'', nullable=False)
    crypto_tip_prv_key = Column(LargeBinary(72), default=b'', nullable=False)

    binary_keys = ['crypto_prv_key', 'crypto_pub_key', 'crypto_tip_prv_key']

    @declared_attr
    def __table_args__(self):
        return (UniqueConstraint('tid', 'receipt_hash'),
                ForeignKeyConstraint(['id'], ['internaltip.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'),
                ForeignKeyConstraint(['tid'], ['tenant.id'], ondelete='CASCADE', deferrable=True, initially='DEFERRED'))


class Anomalies(_Anomalies, Base): pass
class ArchivedSchema(_ArchivedSchema, Base): pass
class Comment(_Comment, Base): pass
class Config(_Config, Base): pass
class ConfigL10N(_ConfigL10N, Base): pass
class Context(_Context, Base): pass
class ContextImg(_ContextImg, Base): pass
class CustomTexts(_CustomTexts, Base): pass
class EnabledLanguage(_EnabledLanguage, Base): pass
class Field(_Field, Base): pass
class FieldAttr(_FieldAttr, Base): pass
class FieldAnswer(_FieldAnswer, Base): pass
class FieldAnswerGroup(_FieldAnswerGroup, Base): pass
class FieldOption(_FieldOption, Base): pass
class File(_File, Base): pass
class IdentityAccessRequest(_IdentityAccessRequest, Base): pass
class InternalFile(_InternalFile, Base): pass
class InternalTip(_InternalTip, Base): pass
class InternalTipAnswers(_InternalTipAnswers, Base): pass
class InternalTipData(_InternalTipData, Base): pass
class Mail(_Mail, Base): pass
class Message(_Message, Base): pass
class Questionnaire(_Questionnaire, Base): pass
class Receiver(_Receiver, Base): pass
class ReceiverContext(_ReceiverContext, Base): pass
class ReceiverFile(_ReceiverFile, Base): pass
class ReceiverTip(_ReceiverTip, Base): pass
class SecureFileDelete(_SecureFileDelete, Base): pass
class ShortURL(_ShortURL, Base): pass
class Signup(_Signup, Base): pass
class SubmissionStatus(_SubmissionStatus, Base): pass
class SubmissionSubStatus(_SubmissionSubStatus, Base): pass
class SubmissionStatusChange(_SubmissionStatusChange, Base): pass
class Stats(_Stats, Base): pass
class Step(_Step, Base): pass
class Tenant(_Tenant, Base): pass
class User(_User, Base): pass
class UserImg(_UserImg, Base): pass
class UserTenant(_UserTenant, Base): pass
class WhistleblowerFile(_WhistleblowerFile, Base): pass
class WhistleblowerTip(_WhistleblowerTip, Base): pass