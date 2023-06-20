# -*- coding: UTF-8
from globaleaks import models
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.handlers.submission import db_set_internaltip_answers, db_set_internaltip_data
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.utility import datetime_never, datetime_now, datetime_null


class Context_v_44(Model):
    __tablename__ = 'context'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    show_context = Column(Boolean, default=True, nullable=False)
    show_recipients_details = Column(Boolean, default=False, nullable=False)
    allow_recipients_selection = Column(Boolean, default=False, nullable=False)
    maximum_selectable_receivers = Column(Integer, default=0, nullable=False)
    select_all_receivers = Column(Boolean, default=True, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    tip_timetolive = Column(Integer, default=30, nullable=False)
    name = Column(JSON, default=dict, nullable=False)
    description = Column(JSON, default=dict, nullable=False)
    show_receivers_in_alphabetical_order = Column(Boolean, default=True, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)
    questionnaire_id = Column(UnicodeText(36), default='default', nullable=False)


class Field_v_44(Model):
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
    triggered_by_score = Column(Integer, default=0, nullable=False)
    template_id = Column(UnicodeText(36))
    fieldgroup_id = Column(UnicodeText(36))
    step_id = Column(UnicodeText(36))
    type = Column(UnicodeText, default='inputbox', nullable=False)
    instance = Column(UnicodeText, default='instance', nullable=False)


class InternalTip_v_44(Model):
    __tablename__ = 'internaltip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    content = Column(UnicodeText, default='')
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    update_date = Column(DateTime, default=datetime_now, nullable=False)
    context_id = Column(UnicodeText(36), nullable=False)
    questionnaire_hash = Column(UnicodeText(64), nullable=False)
    progressive = Column(Integer, default=0, nullable=False)
    https = Column(Boolean, default=False, nullable=False)
    total_score = Column(Integer, default=0, nullable=False)
    expiration_date = Column(DateTime, nullable=False)
    identity_provided = Column(Boolean, default=False, nullable=False)
    identity_provided_date = Column(DateTime, default=datetime_null, nullable=False)
    enable_two_way_comments = Column(Boolean, default=True, nullable=False)
    enable_attachments = Column(Boolean, default=True, nullable=False)
    enable_whistleblower_identity = Column(Boolean, default=False, nullable=False)
    wb_last_access = Column(DateTime, default=datetime_now, nullable=False)
    status = Column(UnicodeText(36), nullable=False)
    substatus = Column(UnicodeText(36), nullable=True)


class Receiver_v_44(Model):
    __tablename__ = 'receiver'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    configuration = Column(UnicodeText, default='default', nullable=False)
    can_delete_submission = Column(Boolean, default=False, nullable=False)
    can_postpone_expiration = Column(Boolean, default=False, nullable=False)
    tip_notification = Column(Boolean, default=True, nullable=False)


class ReceiverFile_v_44(Model):
    __tablename__ = 'receiverfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    internalfile_id = Column(UnicodeText(36), nullable=False)
    receivertip_id = Column(UnicodeText(36), nullable=False)
    filename = Column(UnicodeText(255), nullable=False)
    size = Column(Integer, nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    status = Column(UnicodeText, nullable=False)


class ReceiverTip_v_44(Model):
    __tablename__ = 'receivertip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    internaltip_id = Column(UnicodeText(36), nullable=False)
    receiver_id = Column(UnicodeText(36), nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    label = Column(UnicodeText, default='', nullable=False)
    can_access_whistleblower_identity = Column(Boolean, default=True, nullable=False)
    new = Column(Integer, default=True, nullable=False)
    enable_notifications = Column(Boolean, default=True, nullable=False)


class Step_v_44(Model):
    __tablename__ = 'step'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    questionnaire_id = Column(UnicodeText(36), nullable=True)
    label = Column(JSON, nullable=False)
    description = Column(JSON, nullable=False)
    presentation_order = Column(Integer, default=0, nullable=False)


class User_v_44(Model):
    __tablename__ = 'user'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    username = Column(UnicodeText, default='', nullable=False)
    salt = Column(UnicodeText(24), nullable=False)
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
    can_edit_general_settings = Column(Boolean, default=False, nullable=False)
    change_email_address = Column(UnicodeText, default='', nullable=False)
    change_email_token = Column(UnicodeText, unique=True, nullable=True)
    change_email_date = Column(DateTime, default=datetime_never, nullable=False)
    pgp_key_fingerprint = Column(UnicodeText, default='', nullable=False)
    pgp_key_public = Column(UnicodeText, default='', nullable=False)
    pgp_key_expiration = Column(DateTime, default=datetime_null, nullable=False)


class WhistleblowerFile_v_44(Model):
    __tablename__ = 'whistleblowerfile'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    receivertip_id = Column(UnicodeText(36), nullable=False)
    name = Column(UnicodeText, nullable=False)
    filename = Column(UnicodeText(255), nullable=False)
    size = Column(Integer, nullable=False)
    content_type = Column(UnicodeText, nullable=False)
    creation_date = Column(DateTime, default=datetime_now, nullable=False)
    last_access = Column(DateTime, default=datetime_null, nullable=False)
    description = Column(UnicodeText, nullable=False)


class WhistleblowerTip_v_44(Model):
    __tablename__ = 'whistleblowertip'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    tid = Column(Integer, default=1, nullable=False)
    receipt_hash = Column(UnicodeText(128), nullable=False)


class MigrationScript(MigrationBase):
    def db_serialize_questionnaire_answers_recursively(self, session, answers, answers_by_group, groups_by_answer):
        ret = {}

        for answer in answers:
            if answer.is_leaf:
                ret[answer.key] = answer.value
            else:
                for group in groups_by_answer.get(answer.id, []):
                    ret[answer.key] = [
                        self.db_serialize_questionnaire_answers_recursively(session, answers_by_group.get(group.id, []),
                                                                            answers_by_group, groups_by_answer)]

        return ret

    def db_serialize_questionnaire_answers(self, session, internaltip):
        answers = []
        answers_by_group = {}
        groups_by_answer = {}
        all_answers_ids = []

        for answer in session.query(self.model_from['FieldAnswer']) \
                             .filter(self.model_from['FieldAnswer'].internaltip_id == internaltip.id):
            all_answers_ids.append(answer.id)

            if answer.fieldanswergroup_id is None:
                answers.append(answer)

            else:
                if answer.fieldanswergroup_id not in answers_by_group:
                    answers_by_group[answer.fieldanswergroup_id] = []

                answers_by_group[answer.fieldanswergroup_id].append(answer)

        if all_answers_ids:
            for group in session.query(self.model_from['FieldAnswerGroup']) \
                    .filter(self.model_from['FieldAnswerGroup'].fieldanswer_id.in_(all_answers_ids)) \
                    .order_by(self.model_from['FieldAnswerGroup'].number):

                if group.fieldanswer_id not in groups_by_answer:
                    groups_by_answer[group.fieldanswer_id] = []

                groups_by_answer[group.fieldanswer_id].append(group)

        return self.db_serialize_questionnaire_answers_recursively(session, answers, answers_by_group, groups_by_answer)

    def migrate_FieldAttr(self):
        for old_obj in self.session_old.query(self.model_from['FieldAttr']):
            new_obj = self.model_to['FieldAttr']()
            for key in new_obj.__mapper__.column_attrs.keys():
                setattr(new_obj, key, getattr(old_obj, key))

            if new_obj.type == 'bool':
                new_obj.value = new_obj.value == 'True'

            self.session_new.add(new_obj)

    def migrate_User(self):
        receivers_by_id = {}
        for old_obj in self.session_old.query(self.model_from['Receiver']):
            receivers_by_id[old_obj.id] = old_obj

        for old_obj in self.session_old.query(self.model_from['User']):
            new_obj = self.model_to['User']()
            for key in new_obj.__mapper__.column_attrs.keys():
                if key == 'hash_alg':
                    new_obj.hash_alg = 'SCRYPT'
                elif key in ['notification']:
                    continue
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            if old_obj.id in receivers_by_id:
                new_obj.notification = receivers_by_id[old_obj.id].tip_notification

            self.session_new.add(new_obj)

    def epilogue(self):
        ids = [id[0] for id in self.session_old.query(self.model_from['Field'].id)
                                               .filter(self.model_from['Field'].template_id == 'whistleblower_identity')]

        for internaltip in self.session_old.query(self.model_from['InternalTip']):
            answers = self.db_serialize_questionnaire_answers(self.session_old, internaltip)

            db_set_internaltip_answers(self.session_new, internaltip.id, internaltip.questionnaire_hash, answers)

            for id in ids:
                if id in answers:
                    db_set_internaltip_data(self.session_new, internaltip.id, 'identity_provided', True)
                    db_set_internaltip_data(self.session_new, internaltip.id, 'whistleblower_identity', answers[id])
                    break
