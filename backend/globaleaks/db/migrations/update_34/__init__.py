# -*- coding: utf-8 -*-
import base64
import os

from storm.locals import Int, Bool, Unicode, DateTime, JSON

from globaleaks import models
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.db.migrations.update_34.config import GLConfig_v_35
from globaleaks.models import l10n, properties
from globaleaks.models.config import Config
from globaleaks.models.l10n import ConfigL10N
from globaleaks.models.validators import shorttext_v, longtext_v, shortlocal_v, longlocal_v, \
    natnum_v, range_v
from globaleaks.settings import Settings
from globaleaks.utils.utility import datetime_null

class Node_v_33(models.ModelWithID):
    __storm_table__ = 'node'

    version = Unicode()
    version_db = Unicode()
    name = Unicode(validator=shorttext_v, default=u'')
    basic_auth = Bool(default=False)
    basic_auth_username = Unicode(default=u'')
    basic_auth_password = Unicode(default=u'')
    public_site = Unicode(validator=shorttext_v, default=u'')
    hidden_service = Unicode(validator=shorttext_v, default=u'')
    tb_download_link = Unicode(validator=shorttext_v, default=u'https://www.torproject.org/download/download')
    receipt_salt = Unicode(validator=shorttext_v)
    languages_enabled = JSON()
    default_language = Unicode(validator=shorttext_v, default=u'en')
    default_password = Unicode(validator=longtext_v, default=u'globaleaks')
    description = JSON(validator=longlocal_v, default_factory=dict)
    presentation = JSON(validator=longlocal_v, default_factory=dict)
    footer = JSON(validator=longlocal_v, default_factory=dict)
    security_awareness_title = JSON(validator=longlocal_v, default_factory=dict)
    security_awareness_text = JSON(validator=longlocal_v, default_factory=dict)
    maximum_namesize = Int(validator=natnum_v, default=128)
    maximum_textsize = Int(validator=natnum_v, default=4096)
    maximum_filesize = Int(validator=natnum_v, default=30)
    tor2web_admin = Bool(default=True)
    tor2web_custodian = Bool(default=True)
    tor2web_whistleblower = Bool(default=False)
    tor2web_receiver = Bool(default=True)
    tor2web_unauth = Bool(default=True)
    allow_unencrypted = Bool(default=False)
    disable_encryption_warnings = Bool(default=False)
    allow_iframes_inclusion = Bool(default=False)
    submission_minimum_delay = Int(validator=natnum_v, default=10)
    submission_maximum_ttl = Int(validator=natnum_v, default=10800)
    can_postpone_expiration = Bool(default=False)
    can_delete_submission = Bool(default=False)
    can_grant_permissions = Bool(default=False)
    ahmia = Bool(default=False)
    allow_indexing = Bool(default=False)
    wizard_done = Bool(default=False)
    disable_submissions = Bool(default=False)
    disable_privacy_badge = Bool(default=False)
    disable_security_awareness_badge = Bool(default=False)
    disable_security_awareness_questions = Bool(default=False)
    disable_key_code_hint = Bool(default=False)
    disable_donation_panel = Bool(default=False)
    enable_captcha = Bool(default=True)
    enable_proof_of_work = Bool(default=True)
    enable_experimental_features = Bool(default=False)
    whistleblowing_question = JSON(validator=longlocal_v, default_factory=dict)
    whistleblowing_button = JSON(validator=longlocal_v, default_factory=dict)
    whistleblowing_receipt_prompt = JSON(validator=longlocal_v, default_factory=dict)
    simplified_login = Bool(default=True)
    enable_custom_privacy_badge = Bool(default=False)
    custom_privacy_badge_tor = JSON(validator=longlocal_v, default_factory=dict)
    custom_privacy_badge_none = JSON(validator=longlocal_v, default_factory=dict)
    header_title_homepage = JSON(validator=longlocal_v, default_factory=dict)
    header_title_submissionpage = JSON(validator=longlocal_v, default_factory=dict)
    header_title_receiptpage = JSON(validator=longlocal_v, default_factory=dict)
    header_title_tippage = JSON(validator=longlocal_v, default_factory=dict)
    widget_comments_title = JSON(validator=shortlocal_v, default_factory=dict)
    widget_messages_title = JSON(validator=shortlocal_v, default_factory=dict)
    widget_files_title = JSON(validator=shortlocal_v, default_factory=dict)
    landing_page = Unicode(default=u'homepage')
    contexts_clarification = JSON(validator=longlocal_v, default_factory=dict)
    show_small_context_cards = Bool(default=False)
    show_contexts_in_alphabetical_order = Bool(default=False)
    wbtip_timetolive = Int(validator=natnum_v, default=90)
    threshold_free_disk_megabytes_high = Int(validator=natnum_v, default=200)
    threshold_free_disk_megabytes_medium = Int(validator=natnum_v, default=500)
    threshold_free_disk_megabytes_low = Int(validator=natnum_v, default=1000)
    threshold_free_disk_percentage_high = Int(default=3)
    threshold_free_disk_percentage_medium = Int(default=5)
    threshold_free_disk_percentage_low = Int(default=10)
    context_selector_type = Unicode(validator=shorttext_v, default=u'list')

    localized_keys = [
        'description',
        'presentation',
        'footer',
        'security_awareness_title',
        'security_awareness_text',
        'whistleblowing_question',
        'whistleblowing_button',
        'whistleblowing_receipt_prompt',
        'custom_privacy_badge_tor',
        'custom_privacy_badge_none',
        'header_title_homepage',
        'header_title_submissionpage',
        'header_title_receiptpage',
        'header_title_tippage',
        'contexts_clarification',
        'widget_comments_title',
        'widget_messages_title',
        'widget_files_title'
    ]


class Notification_v_33(models.ModelWithID):
    __storm_table__ = 'notification'

    server = Unicode(validator=shorttext_v, default=u'demo.globaleaks.org')
    port = Int(default=9267)
    username = Unicode(validator=shorttext_v, default=u'hey_you_should_change_me')
    password = Unicode(validator=shorttext_v, default=u'yes_you_really_should_change_me')
    source_name = Unicode(validator=shorttext_v, default=u'GlobaLeaks - CHANGE EMAIL ACCOUNT USED FOR NOTIFICATION')
    source_email = Unicode(validator=shorttext_v, default=u'notification@demo.globaleaks.org')
    security = Unicode(validator=shorttext_v, default=u'TLS')
    admin_pgp_alert_mail_title = JSON(validator=longlocal_v)
    admin_pgp_alert_mail_template = JSON(validator=longlocal_v)
    admin_anomaly_mail_template = JSON(validator=longlocal_v)
    admin_anomaly_mail_title = JSON(validator=longlocal_v)
    admin_anomaly_disk_low = JSON(validator=longlocal_v)
    admin_anomaly_disk_medium = JSON(validator=longlocal_v)
    admin_anomaly_disk_high = JSON(validator=longlocal_v)
    admin_anomaly_activities = JSON(validator=longlocal_v)
    admin_test_static_mail_template = JSON(validator=longlocal_v)
    admin_test_static_mail_title = JSON(validator=longlocal_v)
    tip_mail_template = JSON(validator=longlocal_v)
    tip_mail_title = JSON(validator=longlocal_v)
    file_mail_template = JSON(validator=longlocal_v)
    file_mail_title = JSON(validator=longlocal_v)
    comment_mail_template = JSON(validator=longlocal_v)
    comment_mail_title = JSON(validator=longlocal_v)
    message_mail_template = JSON(validator=longlocal_v)
    message_mail_title = JSON(validator=longlocal_v)
    tip_expiration_mail_template = JSON(validator=longlocal_v)
    tip_expiration_mail_title = JSON(validator=longlocal_v)
    pgp_alert_mail_title = JSON(validator=longlocal_v)
    pgp_alert_mail_template = JSON(validator=longlocal_v)
    receiver_notification_limit_reached_mail_template = JSON(validator=longlocal_v)
    receiver_notification_limit_reached_mail_title = JSON(validator=longlocal_v)
    export_template = JSON(validator=longlocal_v)
    export_message_recipient = JSON(validator=longlocal_v)
    export_message_whistleblower = JSON(validator=longlocal_v)
    identity_access_authorized_mail_template = JSON(validator=longlocal_v)
    identity_access_authorized_mail_title = JSON(validator=longlocal_v)
    identity_access_denied_mail_template = JSON(validator=longlocal_v)
    identity_access_denied_mail_title = JSON(validator=longlocal_v)
    identity_access_request_mail_template = JSON(validator=longlocal_v)
    identity_access_request_mail_title = JSON(validator=longlocal_v)
    identity_provided_mail_template = JSON(validator=longlocal_v)
    identity_provided_mail_title = JSON(validator=longlocal_v)
    disable_admin_notification_emails = Bool(default=False)
    disable_custodian_notification_emails = Bool(default=False)
    disable_receiver_notification_emails = Bool(default=False)
    send_email_for_every_event = Bool(default=True)
    tip_expiration_threshold = Int(validator=natnum_v, default=72)
    notification_threshold_per_hour = Int(validator=natnum_v, default=20)
    notification_suspension_time=Int(validator=natnum_v, default=(2 * 3600))
    exception_email_address = Unicode(validator=shorttext_v, default=u'globaleaks-stackexception@lists.globaleaks.org')
    exception_email_pgp_key_fingerprint = Unicode(default=u'')
    exception_email_pgp_key_public = Unicode(default=u'')
    exception_email_pgp_key_expiration = DateTime(default_factory=datetime_null)

    localized_keys = [
        'admin_anomaly_mail_title',
        'admin_anomaly_mail_template',
        'admin_anomaly_disk_low',
        'admin_anomaly_disk_medium',
        'admin_anomaly_disk_high',
        'admin_anomaly_activities',
        'admin_pgp_alert_mail_title',
        'admin_pgp_alert_mail_template',
        'admin_test_static_mail_template',
        'admin_test_static_mail_title',
        'pgp_alert_mail_title',
        'pgp_alert_mail_template',
        'tip_mail_template',
        'tip_mail_title',
        'file_mail_template',
        'file_mail_title',
        'comment_mail_template',
        'comment_mail_title',
        'message_mail_template',
        'message_mail_title',
        'tip_expiration_mail_template',
        'tip_expiration_mail_title',
        'receiver_notification_limit_reached_mail_template',
        'receiver_notification_limit_reached_mail_title',
        'identity_access_authorized_mail_template',
        'identity_access_authorized_mail_title',
        'identity_access_denied_mail_template',
        'identity_access_denied_mail_title',
        'identity_access_request_mail_template',
        'identity_access_request_mail_title',
        'identity_provided_mail_template',
        'identity_provided_mail_title',
        'export_template',
        'export_message_whistleblower',
        'export_message_recipient'
    ]


class MigrationScript(MigrationBase):
    def epilogue(self):
        old_node = self.store_old.find(self.model_from['Node']).one()
        old_notif = self.store_old.find(self.model_from['Notification']).one()

        with open(os.path.join(Settings.client_path, 'data', 'favicon.ico'), 'r') as favicon_file:
            data = favicon_file.read()
            new_file = self.model_to['File']()
            new_file.id = u'favicon'
            new_file.data = base64.b64encode(data)
            self.store_new.add(new_file)
            self.entries_count['File'] += 1

        file_path = os.path.join(Settings.files_path, 'custom_homepage.html')
        if os.path.exists(file_path):
            with open(file_path, 'r') as homepage_file:
                data = homepage_file.read()
                new_file = self.model_to['File']()
                new_file.id = u'homepage'
                new_file.data = base64.b64encode(data)
                self.store_new.add(new_file)
                self.entries_count['File'] += 1

            os.remove(file_path)

        #### Create ConfigL10N table and rows ####
        for lang in old_node.languages_enabled:
            self.store_new.add(self.model_to['EnabledLanguage'](lang))

        self._migrate_l10n_static_config(old_node, 'node')
        self._migrate_l10n_static_config(old_notif, 'templates')

        # TODO assert that localized_keys matches exactly what is stored in the DB

        #### Create Config table and rows ####

        # Migrate Config saved in Node
        for var_name, _ in GLConfig_v_35['node'].items():
            old_val = getattr(old_node, var_name)
            self.store_new.add(self.model_to['Config']('node', var_name, old_val, cfg_desc=GLConfig_v_35))

        # Migrate Config saved in Notification
        for var_name, _ in GLConfig_v_35['notification'].items():
            old_val = getattr(old_notif, var_name)

            if var_name == 'exception_email_pgp_key_expiration' and old_val is not None:
                old_val = properties.iso_strf_time(old_val)

            self.store_new.add(self.model_to['Config']('notification', var_name, old_val, cfg_desc=GLConfig_v_35))

        # Migrate private fields
        self.store_new.add(self.model_to['Config']('private', 'receipt_salt', old_node.receipt_salt))
        self.store_new.add(self.model_to['Config']('private', 'smtp_password', old_notif.password))

        # Set old verions that will be then handled by the version update
        self.store_new.add(self.model_to['Config']('private', 'version', 'X.Y.Z'))
        self.store_new.add(self.model_to['Config']('private', 'version_db', 0))

    def _migrate_l10n_static_config(self, old_obj, appd_key):
        langs_enabled = self.model_to['EnabledLanguage'].list(self.store_new)

        new_obj_appdata = self.appdata[appd_key]

        for name in old_obj.localized_keys:
            xx_json_dict = getattr(old_obj, name, {})
            if xx_json_dict is None:
                xx_json_dict = {} # protects against Nones in early db versions
            app_data_item = new_obj_appdata.get(name, {})
            for lang in langs_enabled:
                val = xx_json_dict.get(lang, None)
                val_def = app_data_item.get(lang, "")

                if val is not None:
                    val_f = val
                elif val is None and val_def != "":
                    # This is the reset of the new default
                    val_f = val_def
                else: # val is None and val_def == ""
                    val_f = ""

                s = self.model_to['ConfigL10N'](lang, old_obj.__storm_table__, name, val_f)
                # Set the cfg item to customized if the final assigned val does
                # not equal the current default template value
                s.customized = val_f != val_def

                self.store_new.add(s)

    def migrate_Field(self):
        old_objs = self.store_old.find(self.model_from['Field'])
        for old_obj in old_objs:
            new_obj = self.model_to['Field']()
            for _, v in new_obj._storm_columns.items():
                setattr(new_obj, v.name, getattr(old_obj, v.name))

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

            self.store_new.add(new_obj)
