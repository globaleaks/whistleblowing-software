import os

from globaleaks.db.migrations.update import MigrationBase
from globaleaks import DATABASE_VERSION
from globaleaks.models import *
from globaleaks.models import l10n
from globaleaks.db.appdata import load_archived_appdata


class Node_v_33(Model):
    __storm_table__ = 'node'
    version = Unicode()
    version_db = Unicode()
    name = Unicode(validator=shorttext_v, default=u'')
    basic_auth = Bool(default=False)
    basic_auth_username = Unicode(default=u'')
    basic_auth_password = Unicode(default=u'')
    public_site = Unicode(validator=shorttext_v, default=u'')
    hidden_service = Unicode(validator=shorttext_v, default=u'')
    receipt_salt = Unicode(validator=shorttext_v)
    languages_enabled = JSON()
    default_language = Unicode(validator=shorttext_v, default=u'en')
    default_timezone = Int(default=0)
    default_password = Unicode(validator=longtext_v, default=u'globaleaks')
    description = JSON(validator=longlocal_v, default=empty_localization)
    presentation = JSON(validator=longlocal_v, default=empty_localization)
    footer = JSON(validator=longlocal_v, default=empty_localization)
    security_awareness_title = JSON(validator=longlocal_v, default=empty_localization)
    security_awareness_text = JSON(validator=longlocal_v, default=empty_localization)
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
    whistleblowing_question = JSON(validator=longlocal_v, default=empty_localization)
    whistleblowing_button = JSON(validator=longlocal_v, default=empty_localization)
    whistleblowing_receipt_prompt = JSON(validator=longlocal_v, default=empty_localization)
    simplified_login = Bool(default=True)
    enable_custom_privacy_badge = Bool(default=False)
    custom_privacy_badge_tor = JSON(validator=longlocal_v, default=empty_localization)
    custom_privacy_badge_none = JSON(validator=longlocal_v, default=empty_localization)
    header_title_homepage = JSON(validator=longlocal_v, default=empty_localization)
    header_title_submissionpage = JSON(validator=longlocal_v, default=empty_localization)
    header_title_receiptpage = JSON(validator=longlocal_v, default=empty_localization)
    header_title_tippage = JSON(validator=longlocal_v, default=empty_localization)
    widget_comments_title = JSON(validator=shortlocal_v, default=empty_localization)
    widget_messages_title = JSON(validator=shortlocal_v, default=empty_localization)
    widget_files_title = JSON(validator=shortlocal_v, default=empty_localization)
    landing_page = Unicode(default=u'homepage')
    contexts_clarification = JSON(validator=longlocal_v, default=empty_localization)
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

class Notification_v_33(Model):
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
    exception_email_pgp_key_info = Unicode(default=u'')
    exception_email_pgp_key_fingerprint = Unicode(default=u'')
    exception_email_pgp_key_public = Unicode(default=u'')
    exception_email_pgp_key_expiration = DateTime(default_factory=datetime_null)
    exception_email_pgp_key_status = Unicode(default=u'disabled')

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
    x = ['globaleaks', 'db', 'migrations', 'update_%s' % DATABASE_VERSION, 'appdata_v2_62_8.json']
    path = os.path.join(GLSettings.root_path, *x)
    appdata = load_archived_appdata(path)


    def prologue(self):
        old_node = self.store_old.find(self.model_from['Node']).one()

        # Fill out enabled langs table
        for lang in old_node.languages_enabled:
            self.store_new.add(l10n.EnabledLanguage(lang))
            #l10n.EnabledLanguage.add_new_lang(self.store_new, lang, self.appdata['node'])


    def _migrate_l10n_static_config(self, old_obj, appd_key):

        langs_enabled = l10n.EnabledLanguage.get_all(self.store_new)
        obj_appdata = self.appdata[appd_key]

        for name in old_obj.localized_keys:
            
            xx_json_dict = getattr(old_obj, name)
            app_data_langs = obj_appdata.get(name, None)
            for lang in langs_enabled:
                # if the string for the lang string is not the old_obj, simply use the
                # default. In the other case use whatever string is their even if it is
                # the empty string.
                val = xx_json_dict.get(lang, None)
                default_value = u''
                if app_data_langs is not None:
                  default_value = app_data_langs.get(lang, u'')
                s = Static_L10N(lang, old_obj.__storm_table__, name, default_value, val)
                self.store_new.add(s)


    def migrate_Node(self):
        old_node = self.store_old.find(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for _, v in new_node._storm_columns.iteritems():

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)

        self._migrate_l10n_static_config(old_node, 'node')


    def migrate_Notification(self):
        old_notif = self.store_old.find(self.model_from['Notification']).one()
        new_notif = self.model_to['Notification']()
        for _, v in new_notif._storm_columns.iteritems():

            setattr(new_notif, v.name, getattr(old_notif, v.name))

        self.store_new.add(new_notif)

        self._migrate_l10n_static_config(old_notif, 'templates')
