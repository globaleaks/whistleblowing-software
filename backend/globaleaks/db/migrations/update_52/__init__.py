# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.enums import EnumFieldAttrType
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_now, datetime_never, datetime_null


class Context_v_51(Model):
    __tablename__ = 'context'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, default=1, nullable=False)
    show_steps_navigation_interface = Column(Boolean, default=True, nullable=False)
    show_recipients_details = Column(Boolean, default=False, nullable=False)
    allow_recipients_selection = Column(Boolean, default=False, nullable=False)
    maximum_selectable_receivers = Column(Integer, default=0, nullable=False)
    select_all_receivers = Column(Boolean, default=True, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    tip_timetolive = Column(Integer, default=90, nullable=False)
    name = Column(JSON, default=dict, nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    show_receivers_in_alphabetical_order = Column(Boolean, default=True, nullable=False)
    score_threshold_high = Column(Integer, default=0, nullable=False)
    score_threshold_medium = Column(Integer, default=0, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    questionnaire_id = Column(UnicodeText(36), default='default', nullable=False)
    additional_questionnaire_id = Column(UnicodeText(36))
    status = Column(Integer, default=2, nullable=False)


class Field_v_51(Model):
    __tablename__ = 'field'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, default=1, nullable=False)
    x = Column(Integer, default=0, nullable=False)
    y = Column(Integer, default=0, nullable=False)
    width = Column(Integer, default=0, nullable=False)
    label = Column(JSON, default=dict, nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    hint = Column(JSON, default=dict, nullable=False)
    placeholder = Column(JSON, default=dict, nullable=False)
    required = Column(Boolean, default=False, nullable=False)
    preview = Column(Boolean, default=False, nullable=False)
    multi_entry = Column(Boolean, default=False, nullable=False)
    triggered_by_score = Column(Integer, default=0, nullable=False)
    step_id = Column(UnicodeText(36))
    fieldgroup_id = Column(UnicodeText(36))
    type = Column(UnicodeText, default='inputbox', nullable=False)
    instance = Column(UnicodeText, default='instance', nullable=False)
    template_id = Column(UnicodeText(36))
    template_override_id = Column(UnicodeText(36), nullable=True)


class FieldAttr_v_51(Model):
    __tablename__ = 'fieldattr'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    field_id = Column(UnicodeText(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    type = Column(UnicodeText, nullable=False)
    value = Column(JSON, default=dict, nullable=False)


class FieldOption_v_51(Model):
    __tablename__ = 'fieldoption'

    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    field_id = Column(UnicodeText(36), nullable=False)
    label = Column(JSON, default=dict, nullable=False)
    hint1 = Column(JSON, default=dict, nullable=False)
    hint2 = Column(JSON, default=dict, nullable=False)
    score_points = Column(Integer, default=0, nullable=False)
    score_type = Column(Integer, default=0, nullable=False)
    block_submission = Column(Boolean, default=False, nullable=False)
    trigger_receiver = Column(JSON, default=list, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)


class InternalTip_v_51(Model):
    __tablename__ = 'internaltip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    update_date = Column(DateTime, default=datetime_now, nullable=False)
    context_id = Column(UnicodeText(36), nullable=False)
    progressive = Column(Integer, default=0, nullable=False)
    https = Column(Boolean, default=False, nullable=False)
    mobile = Column(Boolean, default=False, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    expiration_date = Column(DateTime, default=datetime_never, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    enable_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    wb_last_access = Column(DateTime, default=datetime_now, nullable=False)
    status = Column(UnicodeText(36), nullable=True)
    substatus = Column(UnicodeText(36), nullable=True)


class InternalTipData_v_51(Model):
    __tablename__ = 'InternalTipData'
    internaltip_id = Column(UnicodeText(36), primary_key=True)
    key = Column(UnicodeText, primary_key=True)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    value = Column(JSON, default=dict, nullable=False)


class Message_v_51(Model):
    __tablename__ = 'message'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    receivertip_id = Column(UnicodeText(36), nullable=False)
    content = Column(UnicodeText, nullable=False)
    type = Column(UnicodeText, nullable=False)
    new = Column(Boolean, default=True, nullable=False)


class ReceiverContext_v_51(Model):
    __tablename__ = 'receiver_context'
    context_id = Column(UnicodeText(36), primary_key=True)
    receiver_id = Column(UnicodeText(36), primary_key=True)
    presentation_order = Column(Integer, default=0, nullable=False)


class ReceiverFile_v_51(Model):
    __tablename__ = 'receiverfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    internalfile_id = Column(UnicodeText(36), nullable=False)
    receivertip_id = Column(UnicodeText(36), nullable=False)
    filename = Column(UnicodeText(255), nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    new = Column(Boolean, default=True, nullable=False)
    status = Column(UnicodeText, default='processing', nullable=False)


class Step_v_51(Model):
    __tablename__ = 'step'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    questionnaire_id = Column(UnicodeText(36), nullable=False)
    label = Column(JSON, default=dict, nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    triggered_by_score = Column(Integer, default=0, nullable=False)


class SubmissionStatus_v_51(Model):
    __tablename__ = 'submissionstatus'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, primary_key=True, default=1, nullable=False)
    label = Column(JSON, default=dict, nullable=False)
    system_defined = Column(Boolean, nullable=False, default=False)
    presentation_order = Column(Integer, default=0, nullable=False)


class SubmissionSubStatus_v_51(Model):
    __tablename__ = 'submissionsubstatus'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, primary_key=True, default=1, nullable=False)
    submissionstatus_id = Column(UnicodeText(36), nullable=False)
    label = Column(JSON, default=dict, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)


class User_v_51(Model):
    __tablename__ = 'user'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    username = Column(UnicodeText, default='', nullable=False)
    salt = Column(UnicodeText(24), nullable=False)
    hash_alg = Column(UnicodeText, default='ARGON2', nullable=False)
    password = Column(UnicodeText, default='', nullable=False)
    name = Column(UnicodeText, default='', nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    role = Column(UnicodeText, default='receiver', nullable=False)
    state = Column(UnicodeText, default='enabled', nullable=False)
    last_login = Column(DateTime, default=datetime_null, nullable=False)
    mail_address = Column(UnicodeText, default='', nullable=False)
    language = Column(UnicodeText, nullable=False)
    password_change_needed = Column(Boolean, default=True, nullable=False)
    password_change_date = Column(DateTime, default=datetime_null, nullable=False)
    change_email_address = Column(UnicodeText, default='', nullable=False)
    change_email_token = Column(UnicodeText, unique=True, nullable=True)
    change_email_date = Column(DateTime, default=datetime_null, nullable=False)
    notification = Column(Boolean, default=True, nullable=False)
    recipient_configuration = Column(UnicodeText, default='default', nullable=False)
    can_delete_submission = Column(Boolean, default=False, nullable=False)
    can_postpone_expiration = Column(Boolean, default=False, nullable=False)
    can_edit_general_settings = Column(Boolean, default=False, nullable=False)
    two_factor_enable = Column(Boolean, default=False, nullable=False)
    two_factor_secret = Column(LargeBinary(64), default=b'', nullable=False)
    pgp_key_fingerprint = Column(UnicodeText, default='', nullable=False)
    pgp_key_public = Column(UnicodeText, default='', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_null, nullable=False)


class MigrationScript(MigrationBase):
    skip_count_check = {
        'Config': True
    }

    renamed_attrs = {
        'FieldOption': {'order': 'presentation_order'},
        'ReceiverContext': {'order': 'presentation_order'},
        'Step': {'order': 'presentation_order'},
        'SubmissionStatus': {'order': 'presentation_order'},
        'SubmissionSubStatus': {'order': 'presentation_order'}
    }

    def migrate_Context(self):
        for old_obj in self.session_old.query(self.model_from['Context']):
            new_obj = self.model_to['Context']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key not in old_obj.__mapper__.column_attrs.keys():
                    continue

                value = getattr(old_obj, key)

                if key == 'status':
                    if value == 0:
                        value = 'disabled'
                    elif value == 1:
                        value = 'enabled'
                    else:
                        value = 'hidden'

                setattr(new_obj, key, value)

            self.session_new.add(new_obj)

    def migrate_FieldAttr(self):
        for old_obj in self.session_old.query(self.model_from['FieldAttr']):
            new_obj = self.model_to['FieldAttr']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key in old_obj.__mapper__.column_attrs.keys():
                    setattr(new_obj, key, getattr(old_obj, key))

            if new_obj.name == 'attachment_url':
                x = {}
                for language in self.session_old.query(self.model_from['EnabledLanguage'].name):
                    x[language[0]] = old_obj.value

                new_obj.type = EnumFieldAttrType.localized.name
                new_obj.value = x

            self.session_new.add(new_obj)

    def migrate_User(self):
        x = self.session_old.query(self.model_from['Config'].value).filter(self.model_from['Config'].tid == 1, self.model_from['Config'].var_name == 'do_not_expose_users_names').one_or_none()
        x = x[0] if x is not None else False

        platform_name = self.session_new.query(self.model_from['Config'].value).filter(self.model_from['Config'].tid == 1, self.model_from['Config'].var_name == 'name').one()[0]

        for old_obj in self.session_old.query(self.model_from['User']):
            new_obj = self.model_to['User']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key.startswith('crypto_') or key == 'readonly' or key == 'two_factor_secret':
                    continue

                if key == 'public_name':
                    new_obj.public_name = platform_name if x else old_obj.name
                elif key == 'recipient_configuration':
                    if old_obj.recipient_configuration == 'default':
                        new_obj.recipient_configuration = 0
                    else:
                        new_obj.recipient_configuration = 1
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def epilogue(self):
        # This migration epilogue is necessary because the default variable of the variables is
        # the opposite of what it is necessary to be configured on migrated nodes
        self.session_new.query(self.model_to['Config']).filter(self.model_to['Config'].var_name.in_(['encryption'])).delete(synchronize_session=False)

        # Fix for issue: https://github.com/globaleaks/GlobaLeaks/issues/2612
        # The bug is due to the fact that the data was initially saved as an array of one entry
        for data in self.session_new.query(self.model_to['InternalTipData']).filter(self.model_to['InternalTipData'].key == 'whistleblower_identity'):
            if isinstance(data.value, list):
                data.value = data.value[0]

        for t in self.session_new.query(self.model_from['Tenant']):
            self.session_new.add(self.model_to['Config']({'tid': t.id, 'var_name': 'encryption', 'value': False}))
            self.session_new.add(self.model_to['Config']({'tid': t.id, 'var_name': 'escrow', 'value': False}))

            x = self.model_to['Config']()
            x.tid = t.id
            x.var_name = 'enable_private_labels'
            x.value = True
            self.session_new.add(x)
