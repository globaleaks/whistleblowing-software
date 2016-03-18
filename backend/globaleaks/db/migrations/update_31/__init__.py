# -*- encoding: utf-8 -*-
import os
import shutil

from storm.locals import Int, Bool, Unicode, DateTime, JSON, ReferenceSet

from globaleaks.db.appdata import load_appdata
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.handlers.admin.field import db_import_fields
from globaleaks.handlers.admin.questionnaire import db_get_default_questionnaire_id
from globaleaks.models import Model, BaseModel, Questionnaire, Step, db_forge_obj
from globaleaks.settings import GLSettings


class Node_v_30(Model):
    __storm_table__ = 'node'
    version = Unicode()
    version_db = Unicode()
    name = Unicode()
    public_site = Unicode()
    hidden_service = Unicode()
    receipt_salt = Unicode()
    languages_enabled = JSON()
    default_language = Unicode()
    default_timezone = Int()
    description = JSON()
    presentation = JSON()
    footer = JSON()
    security_awareness_title = JSON()
    security_awareness_text = JSON()
    context_selector_label = JSON()
    maximum_namesize = Int()
    maximum_textsize = Int()
    maximum_filesize = Int()
    tor2web_admin = Bool()
    tor2web_custodian = Bool()
    tor2web_whistleblower = Bool()
    tor2web_receiver = Bool()
    tor2web_unauth = Bool()
    allow_unencrypted = Bool()
    disable_encryption_warnings = Bool()
    allow_iframes_inclusion = Bool()
    submission_minimum_delay = Int()
    submission_maximum_ttl = Int()
    can_postpone_expiration = Bool()
    can_delete_submission = Bool()
    can_grant_permissions = Bool()
    ahmia = Bool()
    wizard_done = Bool()
    disable_submissions = Bool()
    disable_privacy_badge = Bool()
    disable_security_awareness_badge = Bool()
    disable_security_awareness_questions = Bool()
    disable_key_code_hint = Bool()
    disable_donation_panel = Bool()
    enable_captcha = Bool()
    enable_proof_of_work = Bool()
    enable_experimental_features = Bool()
    whistleblowing_question = JSON()
    whistleblowing_button = JSON()
    simplified_login = Bool()
    enable_custom_privacy_badge = Bool()
    custom_privacy_badge_tor = JSON()
    custom_privacy_badge_none = JSON()
    header_title_homepage = JSON()
    header_title_submissionpage = JSON()
    header_title_receiptpage = JSON()
    header_title_tippage = JSON()
    widget_comments_title = JSON()
    widget_messages_title = JSON()
    widget_files_title = JSON()
    landing_page = Unicode()
    show_contexts_in_alphabetical_order = Bool()
    threshold_free_disk_megabytes_high = Int()
    threshold_free_disk_megabytes_medium = Int()
    threshold_free_disk_megabytes_low = Int()
    threshold_free_disk_percentage_high = Int()
    threshold_free_disk_percentage_medium = Int()
    threshold_free_disk_percentage_low = Int()


class MigrationScript(MigrationBase):
    def migrate_Node(self):
        old_node = self.store_old.find(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for _, v in new_node._storm_columns.iteritems():
            if v.name == 'basic_auth':
                new_node.basic_auth = False
                continue

            if v.name == 'basic_auth_username':
                new_node.basic_auth_username = u''
                continue

            if v.name == 'basic_auth_password':
                new_node.basic_auth_password = u''
                continue

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)
