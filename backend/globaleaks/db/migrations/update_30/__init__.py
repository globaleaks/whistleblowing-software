# -*- coding: utf-8 -*-
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *


class Node_v_29(Model):
    __tablename__ = 'node'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    version = Column(UnicodeText)
    version_db = Column(UnicodeText)
    name = Column(UnicodeText)
    public_site = Column(UnicodeText)
    hidden_service = Column(UnicodeText)
    receipt_salt = Column(UnicodeText)
    languages_enabled = Column(JSON)
    default_language = Column(UnicodeText)
    default_timezone = Column(Integer)
    description = Column(JSON)
    presentation = Column(JSON)
    footer = Column(JSON)
    security_awareness_title = Column(JSON)
    security_awareness_text = Column(JSON)
    context_selector_label = Column(JSON)
    maximum_namesize = Column(Integer)
    maximum_textsize = Column(Integer)
    maximum_filesize = Column(Integer)
    tor2web_admin = Column(Boolean)
    tor2web_custodian = Column(Boolean)
    tor2web_whistleblower = Column(Boolean)
    tor2web_receiver = Column(Boolean)
    tor2web_unauth = Column(Boolean)
    allow_unencrypted = Column(Boolean)
    allow_iframes_inclusion = Column(Boolean)
    submission_minimum_delay = Column(Integer)
    submission_maximum_ttl = Column(Integer)
    can_postpone_expiration = Column(Boolean)
    can_delete_submission = Column(Boolean)
    can_grant_permissions = Column(Boolean)
    ahmia = Column(Boolean)
    wizard_done = Column(Boolean)
    disable_submissions = Column(Boolean)
    disable_privacy_badge = Column(Boolean)
    disable_security_awareness_badge = Column(Boolean)
    disable_security_awareness_questions = Column(Boolean)
    disable_key_code_hint = Column(Boolean)
    disable_donation_panel = Column(Boolean)
    enable_captcha = Column(Boolean)
    enable_proof_of_work = Column(Boolean)
    enable_experimental_features = Column(Boolean)
    whistleblowing_question = Column(JSON)
    whistleblowing_button = Column(JSON)
    simplified_login = Column(Boolean)
    enable_custom_privacy_badge = Column(Boolean)
    custom_privacy_badge_tor = Column(JSON)
    custom_privacy_badge_none = Column(JSON)
    header_title_homepage = Column(JSON)
    header_title_submissionpage = Column(JSON)
    header_title_receiptpage = Column(JSON)
    header_title_tippage = Column(JSON)
    widget_comments_title = Column(JSON)
    widget_messages_title = Column(JSON)
    widget_files_title = Column(JSON)
    landing_page = Column(UnicodeText)
    show_contexts_in_alphabetical_order = Column(Boolean)
    threshold_free_disk_megabytes_high = Column(Integer)
    threshold_free_disk_megabytes_medium = Column(Integer)
    threshold_free_disk_megabytes_low = Column(Integer)
    threshold_free_disk_percentage_high = Column(Integer)
    threshold_free_disk_percentage_medium = Column(Integer)
    threshold_free_disk_percentage_low = Column(Integer)


class Context_v_29(Model):
    __tablename__ = 'context'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    show_small_cards = Column(Boolean)
    show_context = Column(Boolean)
    show_steps_navigation_bar = Column(Boolean)
    steps_navigation_requires_completion = Column(Boolean)
    show_recipients_details = Column(Boolean)
    allow_recipients_selection = Column(Boolean)
    maximum_selectable_receivers = Column(Integer)
    select_all_receivers = Column(Boolean)
    enable_comments = Column(Boolean)
    enable_messages = Column(Boolean)
    enable_two_way_comments = Column(Boolean)
    enable_two_way_messages = Column(Boolean)
    enable_attachments = Column(Boolean)
    enable_whistleblower_identity = Column(Boolean)
    tip_timetolive = Column(Integer)
    name = Column(JSON)
    description = Column(JSON)
    recipients_clarification = Column(JSON)
    questionnaire_layout = Column(UnicodeText)
    show_receivers_in_alphabetical_order = Column(Boolean)
    presentation_order = Column(Integer)


class Step_v_29(Model):
    __tablename__ = 'step'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    context_id = Column(Unicode(36))
    label = Column(JSON)
    description = Column(JSON)
    presentation_order = Column(Integer)
    triggered_by_score = Column(Integer)


class FieldAnswer_v_29(Model):
    __tablename__ = 'fieldanswer'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    internaltip_id = Column(Unicode(36))
    key = Column(UnicodeText, default=u'')
    is_leaf = Column(Boolean, default=True)
    value = Column(UnicodeText, default=u'')


class FieldAnswerGroup_v_29(Model):
    __tablename__ = 'fieldanswergroup'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    number = Column(Integer, default=0)
    fieldanswer_id = Column(Unicode(36))


class FieldAnswerGroupFieldAnswer_v_29(Model):
    __tablename__ = 'fieldanswergroup_fieldanswer'

    fieldanswergroup_id = Column(Unicode(36), primary_key=True)
    fieldanswer_id = Column(Unicode(36), primary_key=True)


class MigrationScript(MigrationBase):
    def migrate_Node(self):
        old_node = self.session_old.query(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for key in [c.key for c in new_node.__table__.columns]:
            if key == 'disable_encryption_warnings':
                new_node.disable_encryption_warnings = False
                continue

            setattr(new_node, key, getattr(old_node, key))

        self.session_new.add(new_node)

    def migrate_FieldAnswer(self):
        old_objs = self.session_old.query(self.model_from['FieldAnswer'])
        for old_obj in old_objs:
            new_obj = self.model_to['FieldAnswer']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'fieldanswergroup_id':
                    old_ref = self.session_old.query(self.model_from['FieldAnswerGroupFieldAnswer']) \
                                            .filter(self.model_from['FieldAnswerGroupFieldAnswer'].fieldanswer_id == old_obj.id).one_or_none()
                    if old_ref is not None:
                        new_obj.fieldanswergroup_id = old_ref.fieldanswergroup_id
                    continue

                setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

    def migrate_Context(self):
        # Migrated in the epilogue
        pass

    def migrate_Step(self):
        # Migrated in the epilogue
        pass

    def epilogue(self):
        self.fail_on_count_mismatch['Step'] = False
        self.fail_on_count_mismatch['Field'] = False
        self.fail_on_count_mismatch['FieldOption'] = False
        self.fail_on_count_mismatch['FieldAttr'] = False

        default_language = self.session_old.query(self.model_from['Node']).one().default_language

        old_contexts = self.session_old.query(self.model_from['Context'])
        for old_context in old_contexts:
            map_on_default = False
            new_questionnaire_id = None

            for old_step in self.session_old.query(self.model_from['Step']).filter(self.model_from['Step'].context_id == old_context.id):
                if self.session_old.query(self.model_from['Field']).filter(self.model_from['Field'].step_id == old_step.id).count() != 4:
                    break

                for field in self.session_old.query(self.model_from['Field']).filter(self.model_from['Field'].step_id == old_step.id):
                    if 'en' in field.label and field.label['en'] == 'Short title':
                        map_on_default = True
                        break

                if map_on_default:
                    break

            if not map_on_default:
                new_questionnaire = self.model_to['Questionnaire']()
                new_questionnaire.name = old_context.name[default_language] if default_language in old_context.name else ''
                new_questionnaire.layout = old_context.questionnaire_layout
                new_questionnaire.show_steps_navigation_bar = old_context.show_steps_navigation_bar
                new_questionnaire.steps_navigation_requires_completion = old_context.steps_navigation_requires_completion
                new_questionnaire.enable_whistleblower_identity = old_context.enable_whistleblower_identity
                self.session_new.add(new_questionnaire)
                new_questionnaire_id = new_questionnaire.id

                for old_step in self.session_old.query(self.model_from['Step']).filter(self.model_from['Step'].context_id == old_context.id):
                    new_step = self.model_to['Step']()
                    for key in [c.key for c in new_step.__table__.columns]:
                        if key == 'questionnaire_id':
                            new_step.questionnaire_id = new_questionnaire.id
                        else:
                            setattr(new_step, key, getattr(old_step, key))

                    self.session_new.add(new_step)

            new_context = self.model_to['Context']()
            for key in [c.key for c in new_context.__table__.columns]:
                if key == 'status_page_message':
                    new_context.status_page_message = ''
                elif key == 'questionnaire_id':
                    if new_questionnaire_id is not None:
                        new_context.questionnaire_id = new_questionnaire_id
                else:
                    setattr(new_context, key, getattr(old_context, key))

            self.session_new.add(new_context)
