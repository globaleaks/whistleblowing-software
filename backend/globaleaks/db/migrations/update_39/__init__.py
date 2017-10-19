#i -*- coding: UTF-8

from storm.expr import And
from storm.locals import Bool, Int, Reference, ReferenceSet, Unicode, Storm, JSON

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.handlers.admin import tenant
from globaleaks.models.validators import shorttext_v, longtext_v, \
    shortlocal_v, longlocal_v, shorturl_v, longurl_v, natnum_v, range_v
from globaleaks.models import *
from globaleaks.utils.utility import datetime_now

from globaleaks.models import config_desc
from globaleaks.db.migrations.update_37.config_desc import GLConfig

ROOT_TENANT = 1


class ArchivedSchema_v_38(Model):
    __storm_table__ = 'archivedschema'
    __storm_primary__ = 'hash', 'type'

    hash = Unicode()
    type = Unicode()
    schema = JSON()


class Comment_v_38(ModelWithID):
    __storm_table__ = 'comment'
    creation_date = DateTime(default_factory=datetime_now)
    internaltip_id = Unicode()
    author_id = Unicode()
    content = Unicode(validator=longtext_v)
    type = Unicode()
    new = Int(default=True)


class Config_v_38(Storm):
    __storm_table__ = 'config'
    __storm_primary__ = ('var_group', 'var_name')

    cfg_desc = GLConfig
    var_group = Unicode()
    var_name = Unicode()
    value = JSON()
    customized = Bool(default=False)

    def __init__(self, group=None, name=None, value=None, cfg_desc=None, migrate=False):
        if cfg_desc is not None:
            self.cfg_desc = cfg_desc

        if migrate:
            return

        self.var_group = unicode(group)
        self.var_name = unicode(name)

        self.set_v(value)

    @staticmethod
    def find_descriptor(config_desc_root, var_group, var_name):
        d = config_desc_root.get(var_group, {}).get(var_name, None)
        if d is None:
            raise ValueError('%s.%s descriptor cannot be None' % (var_group, var_name))

        return d

    def set_v(self, val):
        desc = self.find_descriptor(self.cfg_desc, self.var_group, self.var_name)
        if val is None:
            val = desc._type()
        if isinstance(desc, config_desc.Unicode) and isinstance(val, str):
            val = unicode(val)
        if not isinstance(val, desc._type):
            raise ValueError("Cannot assign %s with %s" % (self, type(val)))
        if desc.validator is not None:
            desc.validator(self, self.var_name, val)

        if self.value is None:
            self.value = {'v': val}

        elif self.value['v'] != val:
            self.customized = True
            self.value = {'v': val}

    def get_v(self):
        return self.value['v']

    def __repr__(self):
        return "<Config: %s.%s>" % (self.var_group, self.var_name)


class ConfigL10N_v_38(Storm):
    __storm_table__ = 'config_l10n'
    __storm_primary__ = ('lang', 'var_group', 'var_name')

    lang = Unicode()
    var_group = Unicode()
    var_name = Unicode()
    value = Unicode()
    customized = Bool(default=False)

    def __init__(self, lang_code=None, group=None, var_name=None, value='', migrate=False):
        if migrate:
            return

        self.lang = unicode(lang_code)
        self.var_group = unicode(group)
        self.var_name = unicode(var_name)
        self.value = unicode(value)


    def set_v(self, value):
        value = unicode(value)
        if self.value != value:
            self.value = value
            self.customized = True


class Context_v_38(ModelWithID):
    __storm_table__ = 'context'

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
    enable_attachments = Bool(default=True)
    enable_rc_to_wb_files = Bool(default=False)
    tip_timetolive = Int(validator=range_v(-1, 5*365), default=15)
    name = JSON(validator=shortlocal_v)
    description = JSON(validator=longlocal_v)
    recipients_clarification = JSON(validator=longlocal_v)
    status_page_message = JSON(validator=longlocal_v)
    show_receivers_in_alphabetical_order = Bool(default=False)
    presentation_order = Int(default=0)
    questionnaire_id = Unicode()
    img_id = Unicode()

class CustomTexts_v_38(Model):
    __storm_table__ = 'customtexts'

    lang = Unicode(primary=True, validator=shorttext_v)
    texts = JSON()


class Counter_v_38(Model):
    __storm_table__ = 'counter'

    key = Unicode(primary=True, validator=shorttext_v)
    counter = Int(default=1)
    update_date = DateTime(default_factory=datetime_now)


class EnabledLanguage_v_38(Model):
    __storm_table__ = 'enabledlanguage'

    name = Unicode(primary=True)

    def __init__(self, name=None, migrate=False):
        if migrate:
            return

        self.name = unicode(name)

    @classmethod
    def list(cls, store):
        return [name for name in store.find(cls.name)]


class Field_v_38(ModelWithID):
    __storm_table__ = 'field'

    x = Int(default=0)
    y = Int(default=0)
    width = Int(default=0)
    label = JSON(validator=longlocal_v)
    description = JSON(validator=longlocal_v)
    hint = JSON(validator=longlocal_v)
    required = Bool(default=False)
    preview = Bool(default=False)
    multi_entry = Bool(default=False)
    multi_entry_hint = JSON(validator=shortlocal_v)
    stats_enabled = Bool(default=False)
    triggered_by_score = Int(default=0)
    fieldgroup_id = Unicode()
    step_id = Unicode()
    template_id = Unicode()
    type = Unicode(default=u'inputbox')
    instance = Unicode(default=u'instance')
    editable = Bool(default=True)


class FieldAttr_v_38(ModelWithID):
    __storm_table__ = 'fieldattr'
    field_id = Unicode()
    name = Unicode()
    type = Unicode()
    value = JSON()

    def update(self, values=None):
        """
        Updated ModelWithIDs attributes from dict.
        """
        super(FieldAttr_v_38, self).update(values)

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


class FieldOption_v_38(ModelWithID):
    __storm_table__ = 'fieldoption'
    field_id = Unicode()
    presentation_order = Int(default=0)
    label = JSON()
    score_points = Int(default=0)
    trigger_field = Unicode()
    trigger_step = Unicode()


class FieldAnswer_v_38(ModelWithID):
    __storm_table__ = 'fieldanswer'

    internaltip_id = Unicode()
    fieldanswergroup_id = Unicode()
    key = Unicode(default=u'')
    is_leaf = Bool(default=True)
    value = Unicode(default=u'')


class FieldAnswerGroup_v_38(ModelWithID):
    __storm_table__ = 'fieldanswergroup'

    number = Int(default=0)
    fieldanswer_id = Unicode()


class File_v_38(ModelWithID):
    __storm_table__ = 'file'

    data = Unicode()


class InternalFile_v_38(ModelWithID):
    __storm_table__ = 'internalfile'

    creation_date = DateTime(default_factory=datetime_now)
    internaltip_id = Unicode()
    name = Unicode(validator=longtext_v)
    file_path = Unicode()
    content_type = Unicode()
    size = Int()
    new = Int(default=True)
    submission = Int(default = False)
    processing_attempts = Int(default=0)


class InternalTip_v_38(ModelWithID):
    __storm_table__ = 'internaltip'

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


class Mail_v_38(ModelWithID):
    __storm_table__ = 'mail'

    creation_date = DateTime(default_factory=datetime_now)
    address = Unicode()
    subject = Unicode()
    body = Unicode()
    processing_attempts = Int(default=0)


class ReceiverTip_v_38(ModelWithID):
    __storm_table__ = 'receivertip'

    internaltip_id = Unicode()
    receiver_id = Unicode()
    last_access = DateTime(default_factory=datetime_null)
    access_counter = Int(default=0)
    label = Unicode(default=u'')
    can_access_whistleblower_identity = Bool(default=False)
    new = Int(default=True)
    enable_notifications = Bool(default=True)


class Receiver_v_38(ModelWithID):
    __storm_table__ = 'receiver'

    configuration = Unicode(default=u'default')
    can_delete_submission = Bool(default=False)
    can_postpone_expiration = Bool(default=False)
    can_grant_permissions = Bool(default=False)
    tip_notification = Bool(default=True)
    presentation_order = Int(default=0)


class ReceiverContext_v_38(Model):
    __storm_table__ = 'receiver_context'
    __storm_primary__ = 'context_id', 'receiver_id'

    context_id = Unicode()
    receiver_id = Unicode()


class ReceiverFile_v_38(ModelWithID):
    __storm_table__ = 'receiverfile'

    internalfile_id = Unicode()
    receivertip_id = Unicode()
    file_path = Unicode()
    size = Int()
    downloads = Int(default=0)
    last_access = DateTime(default_factory=datetime_null)
    new = Int(default=True)
    status = Unicode()


class ShortURL_v_38(ModelWithID):
    __storm_table__ = 'shorturl'

    shorturl = Unicode(validator=shorturl_v)
    longurl = Unicode(validator=longurl_v)


class Stats_v_38(ModelWithID):
    __storm_table__ = 'stats'

    start = DateTime()
    summary = JSON()
    free_disk_space = Int()


class Step_v_38(ModelWithID):
    __storm_table__ = 'step'
    questionnaire_id = Unicode()
    label = JSON()
    description = JSON()
    presentation_order = Int(default=0)
    triggered_by_score = Int(default=0)


class IdentityAccessRequest_v_38(ModelWithID):
    __storm_table__ = 'identityaccessrequest'

    receivertip_id = Unicode()
    request_date = DateTime(default_factory=datetime_now)
    request_motivation = Unicode(default=u'')
    reply_date = DateTime(default_factory=datetime_null)
    reply_user_id = Unicode()
    reply_motivation = Unicode(default=u'')
    reply = Unicode(default=u'pending')


class Message_v_38(ModelWithID):
    __storm_table__ = 'message'
    creation_date = DateTime(default_factory=datetime_now)
    receivertip_id = Unicode()
    content = Unicode(validator=longtext_v)
    type = Unicode()
    new = Int(default=True)


class Questionnaire_v_38(ModelWithID):
    __storm_table__ = 'questionnaire'

    name = Unicode()
    show_steps_navigation_bar = Bool(default=False)
    steps_navigation_requires_completion = Bool(default=False)
    enable_whistleblower_identity = Bool(default=False)
    editable = Bool(default=True)


class User_v_38(ModelWithID):
    __storm_table__ = 'user'

    creation_date = DateTime(default_factory=datetime_now)
    username = Unicode(validator=shorttext_v, default=u'')
    password = Unicode(default=u'')
    salt = Unicode()
    deletable = Bool(default=True)
    name = Unicode(validator=shorttext_v, default=u'')
    description = JSON(validator=longlocal_v, default={})
    public_name = Unicode(validator=shorttext_v, default=u'')
    role = Unicode(default=u'receiver')
    state = Unicode(default=u'enabled')
    last_login = DateTime(default_factory=datetime_null)
    mail_address = Unicode(default=u'')
    language = Unicode()
    password_change_needed = Bool(default=True)
    password_change_date = DateTime(default_factory=datetime_null)
    pgp_key_fingerprint = Unicode(default=u'')
    pgp_key_public = Unicode(default=u'')
    pgp_key_expiration = DateTime(default_factory=datetime_null)
    img_id = Unicode()


class WhistleblowerTip_v_38(ModelWithID):
    __storm_table__ = 'whistleblowertip'

    receipt_hash = Unicode()


class WhistleblowerFile_v_38(ModelWithID):
    __storm_table__ = 'whistleblowerfile'

    receivertip_id = Unicode()
    name = Unicode(validator=shorttext_v)
    file_path = Unicode()
    size = Int()
    content_type = Unicode()
    downloads = Int(default=0)
    creation_date = DateTime(default_factory=datetime_now)
    last_access = DateTime(default_factory=datetime_null)
    description = Unicode(validator=longtext_v)


class MigrationScript(MigrationBase):
    def migrate_ReceiverContext(self):
        used_presentation_order = []
        old_objs = self.store_old.find(self.model_from['ReceiverContext'])
        for old_obj in old_objs:
            new_obj = self.model_to['ReceiverContext']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'tid':
                    new_obj.tid = ROOT_TENANT
                elif v.name == 'presentation_order':
                    presentation_order = self.store_old.find(self.model_from['Receiver'], id=old_obj.receiver_id).one().presentation_order
                    while presentation_order in used_presentation_order:
                        presentation_order += 1

                    used_presentation_order.append(presentation_order)
                    new_obj.presentation_order = presentation_order
                else:
                    setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_File(self):
        old_objs = self.store_old.find(self.model_from['File'])
        for old_obj in old_objs:
            u = self.store_old.find(self.model_from['User'], img_id=old_obj.id).one()
            c = self.store_old.find(self.model_from['Context'], img_id=old_obj.id).one()
            if u is not None:
                new_obj = self.model_to['UserImg']()
                new_obj.id = u.id
                self.entries_count['UserImg'] += 1
                self.entries_count['File'] -= 1
            elif c is not None:
                new_obj = self.model_to['ContextImg']()
                new_obj.id = c.id
                self.entries_count['ContextImg'] += 1
                self.entries_count['File'] -= 1
            else:
                new_obj = self.model_to['File']()

            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'tid':
                    new_obj.tid = ROOT_TENANT
                else:
                    setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def epilogue(self):
        self.store_new.add(self.model_to['Tenant']({'label': ''}))
