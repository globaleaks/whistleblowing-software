# -*- coding: utf-8 -*-
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *


class Node_v_28(Model):
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


class Context_v_28(Model):
    __tablename__ = 'context'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    show_small_cards = Column(Boolean)
    show_context = Column(Boolean)
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


class MigrationScript(MigrationBase):
    def migrate_Node(self):
        old_node = self.session_old.query(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for key in [c.key for c in new_node.__table__.columns]:
            if key == 'disable_submissions':
                new_node.disable_submissions = False
            else:
                setattr(new_node, key, getattr(old_node, key))

        self.session_new.add(new_node)


    def migrate_Context(self):
        old_objs = self.session_old.query(self.model_from['Context'])
        for old_obj in old_objs:
            new_obj = self.model_to['Context']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'show_steps_navigation_bar':
                    new_obj.show_steps_navigation_bar = True
                elif key == 'steps_navigation_requires_completion':
                    new_obj.steps_navigation_requires_completion = False
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)
