# -*- coding: UTF-8
import os
import shutil

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.db.migrations.update_37.config_desc import GLConfig_v_37
from globaleaks.models import *
from globaleaks.models import config_desc
from globaleaks.models.properties import *
from globaleaks.settings import Settings
from globaleaks.utils.utility import datetime_now


class Anomalies_v_38(Model):
    __tablename__ = 'anomalies'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    date = Column(DateTime)
    alarm = Column(Integer)
    events = Column(JSON)


class ArchivedSchema_v_38(Model):
    __tablename__ = 'archivedschema'
    hash = Column(UnicodeText, primary_key=True)
    type = Column(UnicodeText, primary_key=True)
    schema = Column(JSON)


class Comment_v_38(Model):
    __tablename__ = 'comment'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now)
    internaltip_id = Column(UnicodeText(36))
    author_id = Column(UnicodeText(36))
    content = Column(UnicodeText)
    type = Column(UnicodeText)
    new = Column(Integer, default=True)


class Config_v_38(Model):
    __tablename__ = 'config'
    var_group = Column(UnicodeText, primary_key=True)
    var_name = Column(UnicodeText, primary_key=True)
    value = Column(JSON)
    customized = Column(Boolean, default=False)

    def __init__(self, group=None, name=None, value=None, migrate=False):
        if migrate:
            return

        self.var_group = group
        self.var_name = name

        self.set_v(value)

    @staticmethod
    def find_descriptor(config_desc_root, var_group, var_name):
        d = config_desc_root.get(var_group, {}).get(var_name, None)
        if d is None:
            raise ValueError('%s.%s descriptor cannot be None' % (var_group, var_name))

        return d

    def set_v(self, val):
        if self.var_group is None and self.var_name is None:
            return

        desc = self.find_descriptor(GLConfig_v_37, self.var_group, self.var_name)

        if val is None:
            val = desc._type()

        if not isinstance(val, desc._type):
            raise ValueError("Cannot assign %s with %s" % (self, type(val)))

        if self.value is None:
            self.value = {'v': val}

        elif self.value['v'] != val:
            self.customized = True
            self.value = {'v': val}


class ConfigL10N_v_38(Model):
    __tablename__ = 'config_l10n'
    lang = Column(UnicodeText, primary_key=True)
    var_group = Column(UnicodeText, primary_key=True)
    var_name = Column(UnicodeText, primary_key=True)
    value = Column(UnicodeText)
    customized = Column(Boolean, default=False)

    def __init__(self, lang_code=None, group=None, var_name=None, value='', migrate=False):
        if migrate:
            return

        self.lang = lang_code
        self.var_group = group
        self.var_name = var_name
        self.value = value


class Context_v_38(Model):
    __tablename__ = 'context'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    show_small_receiver_cards = Column(Boolean, default=False)
    show_context = Column(Boolean, default=True)
    show_recipients_details = Column(Boolean, default=False)
    allow_recipients_selection = Column(Boolean, default=False)
    maximum_selectable_receivers = Column(Integer, default=0)
    select_all_receivers = Column(Boolean, default=True)
    enable_two_way_comments = Column(Boolean, default=True)
    enable_attachments = Column(Boolean, default=True)
    enable_rc_to_wb_files = Column(Boolean, default=False)
    tip_timetolive = Column(Integer, default=15)
    name = Column(JSON)
    description = Column(JSON)
    recipients_clarification = Column(JSON)
    status_page_message = Column(JSON)
    show_receivers_in_alphabetical_order = Column(Boolean, default=False)
    presentation_order = Column(Integer, default=0)
    questionnaire_id = Column(UnicodeText(36))
    img_id = Column(UnicodeText(36))


class CustomTexts_v_38(Model):
    __tablename__ = 'customtexts'
    lang = Column(UnicodeText, primary_key=True)
    texts = Column(JSON)


class EnabledLanguage_v_38(Model):
    __tablename__ = 'enabledlanguage'
    name = Column(UnicodeText, primary_key=True)

    def __init__(self, name=None, migrate=False):
        if migrate:
            return

        self.name = name

    @classmethod
    def list(cls, session):
        return [name[0] for name in session.query(cls.name)]


class Field_v_38(Model):
    __tablename__ = 'field'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    width = Column(Integer, default=0)
    label = Column(JSON)
    description = Column(JSON)
    hint = Column(JSON)
    required = Column(Boolean, default=False)
    preview = Column(Boolean, default=False)
    multi_entry = Column(Boolean, default=False)
    multi_entry_hint = Column(JSON)
    triggered_by_score = Column(Integer, default=0)
    fieldgroup_id = Column(UnicodeText(36))
    step_id = Column(UnicodeText(36))
    template_id = Column(UnicodeText(36))
    type = Column(UnicodeText, default='inputbox')
    instance = Column(UnicodeText, default='instance')
    editable = Column(Boolean, default=True)


class FieldAttr_v_38(Model):
    __tablename__ = 'fieldattr'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    field_id = Column(UnicodeText(36))
    name = Column(UnicodeText)
    type = Column(UnicodeText)
    value = Column(JSON)

    def update(self, values=None):
        """
        Updated Models attributes from dict.
        """
        super(FieldAttr_v_38, self).update(values)

        if values is None:
            return


class FieldOption_v_38(Model):
    __tablename__ = 'fieldoption'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    field_id = Column(UnicodeText(36))
    presentation_order = Column(Integer, default=0)
    label = Column(JSON)
    score_points = Column(Integer, default=0)
    trigger_field = Column(UnicodeText)


class FieldAnswer_v_38(Model):
    __tablename__ = 'fieldanswer'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    internaltip_id = Column(UnicodeText(36))
    fieldanswergroup_id = Column(UnicodeText(36))
    key = Column(UnicodeText, default='')
    is_leaf = Column(Boolean, default=True)
    value = Column(UnicodeText, default='')


class FieldAnswerGroup_v_38(Model):
    __tablename__ = 'fieldanswergroup'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    number = Column(Integer, default=0)
    fieldanswer_id = Column(UnicodeText(36))


class File_v_38(Model):
    __tablename__ = 'file'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    data = Column(UnicodeText)


class InternalFile_v_38(Model):
    __tablename__ = 'internalfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now)
    internaltip_id = Column(UnicodeText(36))
    name = Column(UnicodeText)
    file_path = Column(UnicodeText)
    content_type = Column(UnicodeText)
    size = Column(Integer)
    new = Column(Integer, default=True)
    submission = Column(Integer, default=False)
    processing_attempts = Column(Integer, default=0)


class InternalTip_v_38(Model):
    __tablename__ = 'internaltip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now)
    update_date = Column(DateTime, default=datetime_now)
    context_id = Column(UnicodeText(36))
    questionnaire_hash = Column(UnicodeText)
    preview = Column(JSON)
    progressive = Column(Integer, default=0)
    tor2web = Column(Boolean, default=False)
    total_score = Column(Integer, default=0)
    expiration_date = Column(DateTime)
    identity_provided = Column(Boolean, default=False)
    identity_provided_date = Column(DateTime, default=datetime_null)
    enable_two_way_comments = Column(Boolean, default=True)
    enable_attachments = Column(Boolean, default=True)
    enable_whistleblower_identity = Column(Boolean, default=False)
    wb_last_access = Column(DateTime, default=datetime_now)
    wb_access_counter = Column(Integer, default=0)


class Mail_v_38(Model):
    __tablename__ = 'mail'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now)
    address = Column(UnicodeText)
    subject = Column(UnicodeText)
    body = Column(UnicodeText)
    processing_attempts = Column(Integer, default=0)


class ReceiverTip_v_38(Model):
    __tablename__ = 'receivertip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    internaltip_id = Column(UnicodeText(36))
    receiver_id = Column(UnicodeText(36))
    last_access = Column(DateTime, default=datetime_null)
    access_counter = Column(Integer, default=0)
    label = Column(UnicodeText, default='')
    can_access_whistleblower_identity = Column(Boolean, default=True)
    new = Column(Integer, default=True)
    enable_notifications = Column(Boolean, default=True)


class Receiver_v_38(Model):
    __tablename__ = 'receiver'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    configuration = Column(UnicodeText, default='default')
    can_delete_submission = Column(Boolean, default=False)
    can_postpone_expiration = Column(Boolean, default=False)
    can_grant_permissions = Column(Boolean, default=False)
    tip_notification = Column(Boolean, default=True)
    presentation_order = Column(Integer, default=0)


class ReceiverContext_v_38(Model):
    __tablename__ = 'receiver_context'
    context_id = Column(UnicodeText(36), primary_key=True)
    receiver_id = Column(UnicodeText(36), primary_key=True)


class ReceiverFile_v_38(Model):
    __tablename__ = 'receiverfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    internalfile_id = Column(UnicodeText(36))
    receivertip_id = Column(UnicodeText(36))
    file_path = Column(UnicodeText)
    size = Column(Integer)
    downloads = Column(Integer, default=0)
    last_access = Column(DateTime, default=datetime_null)
    new = Column(Integer, default=True)
    status = Column(UnicodeText)


class ShortURL_v_38(Model):
    __tablename__ = 'shorturl'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    shorturl = Column(UnicodeText)
    longurl = Column(UnicodeText)


class Step_v_38(Model):
    __tablename__ = 'step'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    questionnaire_id = Column(UnicodeText(36))
    label = Column(JSON)
    description = Column(JSON)
    presentation_order = Column(Integer, default=0)
    triggered_by_score = Column(Integer, default=0)


class IdentityAccessRequest_v_38(Model):
    __tablename__ = 'identityaccessrequest'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    receivertip_id = Column(UnicodeText(36))
    request_date = Column(DateTime, default=datetime_now)
    request_motivation = Column(UnicodeText, default='')
    reply_date = Column(DateTime, default=datetime_null)
    reply_user_id = Column(UnicodeText(36))
    reply_motivation = Column(UnicodeText, default='')
    reply = Column(UnicodeText, default='pending')


class Message_v_38(Model):
    __tablename__ = 'message'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now)
    receivertip_id = Column(UnicodeText(36))
    content = Column(UnicodeText)
    type = Column(UnicodeText)
    new = Column(Integer, default=True)


class Questionnaire_v_38(Model):
    __tablename__ = 'questionnaire'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    name = Column(UnicodeText)
    show_steps_navigation_bar = Column(Boolean, default=False)
    steps_navigation_requires_completion = Column(Boolean, default=False)
    enable_whistleblower_identity = Column(Boolean, default=False)
    editable = Column(Boolean, default=True)


class SecureFileDelete_v_38(Model):
    __tablename__ = 'securefiledelete'
    filepath = Column(UnicodeText, primary_key=True)


class User_v_38(Model):
    __tablename__ = 'user'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime, default=datetime_now)
    username = Column(UnicodeText, default='')
    password = Column(UnicodeText, default='')
    salt = Column(UnicodeText)
    name = Column(UnicodeText, default='')
    description = Column(JSON, default=dict)
    public_name = Column(UnicodeText, default='')
    role = Column(UnicodeText, default='receiver')
    state = Column(UnicodeText, default='enabled')
    last_login = Column(DateTime, default=datetime_null)
    mail_address = Column(UnicodeText, default='')
    language = Column(UnicodeText)
    password_change_needed = Column(Boolean, default=True)
    password_change_date = Column(DateTime, default=datetime_null)
    pgp_key_fingerprint = Column(UnicodeText, default='')
    pgp_key_public = Column(UnicodeText, default='')
    pgp_key_expiration = Column(DateTime, default=datetime_null)
    img_id = Column(UnicodeText(36))


class WhistleblowerTip_v_38(Model):
    __tablename__ = 'whistleblowertip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    receipt_hash = Column(UnicodeText)


class WhistleblowerFile_v_38(Model):
    __tablename__ = 'whistleblowerfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    receivertip_id = Column(UnicodeText(36))
    name = Column(UnicodeText)
    file_path = Column(UnicodeText)
    size = Column(Integer)
    content_type = Column(UnicodeText)
    downloads = Column(Integer, default=0)
    creation_date = Column(DateTime, default=datetime_now)
    last_access = Column(DateTime, default=datetime_null)
    description = Column(UnicodeText)


class MigrationScript(MigrationBase):
    skip_model_migration = {
        'ArchivedSchema': True,
        'ShortURL': True
    }

    skip_count_check = {
        'ShortURL': True
    }

    def migrate_Config(self):
        for old_obj in self.session_old.query(self.model_from['Config']):
            new_obj = self.model_to['Config']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'tid':
                    new_obj.tid = 1
                elif key == 'var_name':
                    if old_obj.var_name == 'server':
                        new_obj.var_name = 'smtp_server'
                    elif old_obj.var_name == 'port':
                        new_obj.var_name = 'smtp_port'
                    elif old_obj.var_name == 'security':
                        new_obj.var_name = 'smtp_security'
                    elif old_obj.var_name == 'username':
                        new_obj.var_name = 'smtp_username'
                    elif old_obj.var_name == 'source_email':
                        new_obj.var_name = 'smtp_source_email'
                    else:
                        new_obj.var_name = old_obj.var_name
                elif key == 'value':
                    new_obj.value = old_obj.value['v']
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_FieldAttr(self):
        for old_obj in self.session_old.query(self.model_from['FieldAttr']):
            new_obj = self.model_to['FieldAttr']()
            for key in new_obj.__mapper__.column_attrs.keys():
                setattr(new_obj, key, getattr(old_obj, key))

            if new_obj.name == 'display_alphabetically':
                new_obj.value = False

            self.session_new.add(new_obj)

    def migrate_InternalTip(self):
        for old_obj in self.session_old.query(self.model_from['InternalTip']):
            new_obj = self.model_to['InternalTip']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'tid':
                    new_obj.tid = 1
                elif key == 'receipt_hash':
                    wbtip = self.session_old.query(self.model_from['WhistleblowerTip']) \
                                          .filter(self.model_from['WhistleblowerTip'].id == old_obj.id).one_or_none()
                    new_obj.receipt_hash = wbtip.receipt_hash if wbtip is not None else ''
                elif key == 'https':
                    new_obj.https = old_obj.tor2web
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)


    def migrate_File(self):
        for old_obj in self.session_old.query(self.model_from['File']):
            obj_id = None
            u = self.session_old.query(self.model_from['User']).filter(self.model_from['User'].img_id == old_obj.id).one_or_none()
            c = self.session_old.query(self.model_from['Context']).filter(self.model_from['Context'].img_id == old_obj.id).one_or_none()
            if u is not None:
                new_obj = self.model_to['UserImg']()
                obj_id = u.id
                self.entries_count['UserImg'] += 1
                self.entries_count['File'] -= 1
            elif c is not None:
                new_obj = self.model_to['ContextImg']()
                obj_id = c.id
                self.entries_count['ContextImg'] += 1
                self.entries_count['File'] -= 1
            else:
                new_obj = self.model_to['File']()

            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'tid':
                    new_obj.tid = 1
                elif key == 'name':
                    new_obj.name = ''
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            if obj_id is not None:
                new_obj.id = obj_id

            self.session_new.add(new_obj)

    def migrate_File_XXX(self, XXX):
        for old_obj in self.session_old.query(self.model_from[XXX]):
            new_obj = self.model_to[XXX]()

            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'tid':
                    new_obj.tid = 1
                elif key == 'file_path':
                    new_obj.file_path = old_obj.file_path.replace('files/submission', 'attachments')
                    try:
                        shutil.move(old_obj.file_path, new_obj.file_path)
                    except Exception:
                        pass
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_InternalFile(self):
        return self.migrate_File_XXX('InternalFile')

    def migrate_ReceiverFile(self):
        return self.migrate_File_XXX('ReceiverFile')

    def migrate_WhistleblowerFile(self):
        return self.migrate_File_XXX('WhistleblowerFile')

    def epilogue(self):
        self.session_new.add(self.model_to['Tenant'](
            {'label': '', 'active': True}))

        for q in self.session_old.query(self.model_from['ArchivedSchema']).filter(self.model_from['ArchivedSchema'].type == 'questionnaire'):
            p = self.session_old.query(self.model_from['ArchivedSchema']).filter(self.model_from['ArchivedSchema'].hash == q.hash,
                                                                                 self.model_from['ArchivedSchema'].type == 'preview').one()

            new_obj = self.model_to['ArchivedSchema']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'tid':
                    new_obj.tid = 1
                elif key == 'preview':
                    new_obj.preview = p.schema
                else:
                    setattr(new_obj, key, getattr(q, key))

            self.session_new.add(new_obj)

            self.entries_count['ArchivedSchema'] -= 1

        static_path = os.path.abspath(os.path.join(Settings.working_path, 'files/static'))
        if os.path.exists(static_path):
            for filename in os.listdir(static_path):
                filepath = os.path.abspath(os.path.join(static_path, filename))
                if not os.path.isfile(filepath):
                    continue

                new_file = File()
                new_file.id = uuid4()
                new_file.name = filename
                new_file.data = ''
                self.session_new.add(new_file)
                shutil.move(filepath,
                            os.path.abspath(os.path.join(Settings.files_path, new_file.id)))

                self.entries_count['File'] += 1

        shutil.rmtree(os.path.abspath(os.path.join(Settings.working_path, 'files/static')), True)
        shutil.rmtree(os.path.abspath(os.path.join(Settings.working_path, 'files/submission')), True)
        shutil.rmtree(os.path.abspath(os.path.join(Settings.working_path, 'files/tmp')), True)

        try:
            # Depending of when the system was installed this directory may not exist
            shutil.rmtree(os.path.abspath(os.path.join(Settings.working_path, 'files/encrypted_upload')))
        except Exception:
            pass
