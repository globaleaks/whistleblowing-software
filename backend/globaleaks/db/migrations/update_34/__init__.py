# -*- coding: utf-8 -*-
import base64
import os

from globaleaks import models
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.db.migrations.update_34.config_desc import GLConfig_v_35
from globaleaks.models.properties import *
from globaleaks.settings import Settings
from globaleaks.utils.utility import datetime_null, iso_strf_time


class Node_v_33(models.Model):
    __tablename__ = 'node'
    id = Column(UnicodeText(36), primary_key=True, default=uuid4, nullable=False)
    version = Column(UnicodeText)
    version_db = Column(UnicodeText)
    name = Column(UnicodeText, default='')
    basic_auth = Column(Boolean, default=False)
    basic_auth_username = Column(UnicodeText, default='')
    basic_auth_password = Column(UnicodeText, default='')
    public_site = Column(UnicodeText, default='')
    hidden_service = Column(UnicodeText, default='')
    tb_download_link = Column(UnicodeText, default='https://www.torproject.org/download/download')
    receipt_salt = Column(UnicodeText)
    languages_enabled = Column(JSON)
    default_language = Column(UnicodeText, default='en')
    description = Column(JSON, default=dict)
    presentation = Column(JSON, default=dict)
    footer = Column(JSON, default=dict)
    maximum_filesize = Column(Integer, default=30)
    tor2web_admin = Column(Boolean, default=True)
    tor2web_custodian = Column(Boolean, default=True)
    tor2web_whistleblower = Column(Boolean, default=False)
    tor2web_receiver = Column(Boolean, default=True)
    tor2web_unauth = Column(Boolean, default=True)
    allow_unencrypted = Column(Boolean, default=False)
    disable_encryption_warnings = Column(Boolean, default=False)
    allow_iframes_inclusion = Column(Boolean, default=False)
    submission_minimum_delay = Column(Integer, default=10)
    can_postpone_expiration = Column(Boolean, default=False)
    can_delete_submission = Column(Boolean, default=False)
    can_grant_permissions = Column(Boolean, default=False)
    allow_indexing = Column(Boolean, default=False)
    wizard_done = Column(Boolean, default=False)
    disable_submissions = Column(Boolean, default=False)
    disable_privacy_badge = Column(Boolean, default=False)
    disable_key_code_hint = Column(Boolean, default=False)
    enable_captcha = Column(Boolean, default=True)
    whistleblowing_question = Column(JSON, default=dict)
    whistleblowing_button = Column(JSON, default=dict)
    simplified_login = Column(Boolean, default=True)
    enable_custom_privacy_badge = Column(Boolean, default=False)
    header_title_homepage = Column(JSON, default=dict)
    header_title_submissionpage = Column(JSON, default=dict)
    header_title_receiptpage = Column(JSON, default=dict)
    header_title_tippage = Column(JSON, default=dict)
    landing_page = Column(UnicodeText, default='homepage')
    contexts_clarification = Column(JSON, default=dict)
    show_small_context_cards = Column(Boolean, default=False)
    show_contexts_in_alphabetical_order = Column(Boolean, default=False)
    threshold_free_disk_megabytes_high = Column(Integer, default=200)
    threshold_free_disk_megabytes_medium = Column(Integer, default=500)
    threshold_free_disk_megabytes_low = Column(Integer, default=1000)
    threshold_free_disk_percentage_high = Column(Integer, default=3)
    threshold_free_disk_percentage_medium = Column(Integer, default=5)
    threshold_free_disk_percentage_low = Column(Integer, default=10)
    context_selector_type = Column(UnicodeText, default='list')


class MigrationScript(MigrationBase):
    def epilogue(self):
        old_node = self.session_old.query(self.model_from['Node']).one()

        for lang in old_node.languages_enabled:
            self.session_new.add(self.model_to['EnabledLanguage'](lang))

        self._migrate_l10n_static_config(old_node, 'node')

        for var_name, _ in GLConfig_v_35['node'].items():
            old_val = getattr(old_node, var_name)
            self.session_new.add(self.model_to['Config']('node', var_name, old_val))

        # Migrate private fields
        self.session_new.add(self.model_to['Config']('private', 'receipt_salt', old_node.receipt_salt))

        # Set old verions that will be then handled by the version update
        self.session_new.add(self.model_to['Config']('private', 'version', 'X.Y.Z'))
        self.session_new.add(self.model_to['Config']('private', 'version_db', 0))

    def _migrate_l10n_static_config(self, old_obj, appd_key):
        langs_enabled = self.model_to['EnabledLanguage'].list(self.session_new)

        new_obj_appdata = self.appdata[appd_key]

        for name in old_obj.localized_keys:
            xx_json_dict = getattr(old_obj, name, {})
            if xx_json_dict is None:
                xx_json_dict = {}  # protects against Nones in early db versions
            app_data_item = new_obj_appdata.get(name, {})
            for lang in langs_enabled:
                val = xx_json_dict.get(lang, None)
                val_def = app_data_item.get(lang, "")

                if val is not None:
                    val_f = val
                elif val is None and val_def != "":
                    # This is the reset of the new default
                    val_f = val_def
                else:  # val is None and val_def == ""
                    val_f = ""

                s = self.model_to['ConfigL10N'](lang, old_obj.__tablename__, name, val_f)
                # Set the cfg item to customized if the final assigned val does
                # not equal the current default template value
                s.customized = val_f != val_def

                self.session_new.add(s)

    def migrate_Field(self):
        for old_obj in self.session_old.query(self.model_from['Field']):
            new_obj = self.model_to['Field']()
            for key in new_obj.__mapper__.column_attrs.keys():
                setattr(new_obj, key, getattr(old_obj, key))

            if (new_obj.instance == 'instance' and new_obj.step_id is None and new_obj.fieldgroup_id is None or
               new_obj.instance == 'reference' and new_obj.step_id is None and new_obj.fieldgroup_id is None or
               new_obj.instance == 'template' and not(new_obj.step_id is None or new_obj.fieldgroup_id is None)):

                # This fix is necessary in order to remove zombies caused by a step removal or a parent field removal
                # The issue was caused by the db reference deleting only the StepField/FieldField relations but not the childrens hierarchy
                # The issue affected al releases before database 28 and the fix is added here in order to remove the dead fields
                # that are still stored inside databases migrated from a version <28 up to the current version.
                self.entries_count['Field'] -= 1
                continue

            # Produce something of value

            self.session_new.add(new_obj)
