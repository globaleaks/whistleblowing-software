# -*- coding: UTF-8
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.utils.utility import datetime_never, datetime_now, datetime_null


class Context_v_45(Model):
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


class FieldOption_v_45(Model):
    __tablename__ = 'fieldoption'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    field_id = Column(UnicodeText(36), nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    label = Column(JSON, nullable=False)
    score_points = Column(Integer, default=0, nullable=False)
    trigger_field = Column(UnicodeText(36))


class Field_v_45(Model):
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


class Receiver_v_45(Model):
    __tablename__ = 'receiver'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    configuration = Column(UnicodeText, default=u'default', nullable=False)
    can_delete_submission = Column(Boolean, default=False, nullable=False)
    can_postpone_expiration = Column(Boolean, default=False, nullable=False)
    can_grant_permissions = Column(Boolean, default=False, nullable=False)


class User_v_45(Model):
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
    role = Column(UnicodeText, default=u'receiver', nullable=False)
    state = Column(UnicodeText, default=u'enabled', nullable=False)
    last_login = Column(DateTime, default=datetime_never, nullable=False)
    mail_address = Column(UnicodeText, default=u'', nullable=False)
    language = Column(UnicodeText, nullable=False)
    password_change_needed = Column(Boolean, default=True, nullable=False)
    password_change_date = Column(DateTime, default=datetime_never, nullable=False)
    crypto_prv_key = Column(LargeBinary(72), default=b'', nullable=False)
    crypto_pub_key = Column(LargeBinary(32), default=b'', nullable=False)
    change_email_address = Column(UnicodeText, default=u'', nullable=False)
    change_email_token = Column(UnicodeText, unique=True, nullable=True)
    change_email_date = Column(DateTime, default=datetime_never, nullable=False)
    reset_password_token = Column(UnicodeText, unique=True, nullable=True)
    reset_password_date = Column(UnicodeText, default=datetime_never, nullable=False)
    notification = Column(Boolean, default=True, nullable=False)
    pgp_key_fingerprint = Column(UnicodeText, default=u'', nullable=False)
    pgp_key_public = Column(UnicodeText, default=u'', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_never, nullable=False)
    can_edit_general_settings = Column(Boolean, default=False, nullable=False)


class MigrationScript(MigrationBase):
    def migrate_Context(self):
        old_objs = self.session_old.query(self.model_from['Context'])
        for old_obj in old_objs:
            new_obj = self.model_to['Context']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'status':
                    new_obj.status = 1 if old_obj.show_context else 2
                    continue
                elif not hasattr(old_obj, key):
                    continue

                setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_Field(self):
        old_objs = self.session_old.query(self.model_from['Field'])
        for old_obj in old_objs:
            new_obj = self.model_to['Field']()
            for key in [c.key for c in new_obj.__table__.columns]:
                setattr(new_obj, key, getattr(old_obj, key))

            if new_obj.type == 'multichoice':
                new_obj.type = 'selectbox'

            self.session_new.add(new_obj)

    def migrate_FieldOption(self):
        old_objs = self.session_old.query(self.model_from['FieldOption'])
        for old_obj in old_objs:
            new_obj = self.model_to['FieldOption']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'score_type':
                    if old_obj.score_points != 0:
                        new_obj.score_type = 1
                    continue
                elif key in ['trigger_step', 'trigger_field_inverted', 'trigger_step_inverted']:
                    continue

                setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_User(self):
        old_objs = self.session_old.query(self.model_from['User'])
        for old_obj in old_objs:
            receiver = self.session_old.query(self.model_from['Receiver']).filter(self.model_from['Receiver'].id == old_obj.id).one_or_none()
            new_obj = self.model_to['User']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key in ['can_delete_submission', 'can_grant_permissions', 'can_postpone_expiration']:
                    if receiver is not None:
                        setattr(new_obj, key, getattr(receiver, key))
                    continue
                elif key == 'recipient_configuration':
                    if receiver is not None:
                        setattr(new_obj, key, receiver.configuration)
                    continue

                setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def epilogue(self):
        tenants = self.session_new.query(self.model_from['Tenant'])
        for t in tenants:
            m = self.model_from['Config']
            a = self.session_new.query(m.value).filter(m.tid == t.id, m.var_name == u'ip_filter_authenticated_enable').one_or_none()
            b = self.session_new.query(m.value).filter(m.tid == t.id, m.var_name == u'ip_filter_authenticated').one_or_none()

            if a is None or b is None:
                continue

            for c in ['admin', 'custodian', 'receiver']:
                self.session_new.add(self.model_to['Config'](t.id, u'ip_filter_' + c + '_enable', a[0]))
                self.session_new.add(self.model_to['Config'](t.id, u'ip_filter_' + c, b[0]))
                self.entries_count['Config'] += 2
