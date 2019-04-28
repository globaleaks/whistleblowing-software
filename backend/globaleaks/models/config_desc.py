# -*- coding: utf-8
from six import text_type

from globaleaks import __version__, DATABASE_VERSION
from globaleaks.utils.crypto import GCE
from globaleaks.utils.utility import datetime_now, uuid4


class Item:
    _type = None

    def __init__(self, *args, **kwargs):
        self.default = kwargs['default']


class Unicode(Item):
    _type = text_type

    def __init__(self, *args, **kwargs):
        if 'default' not in kwargs:
            kwargs['default'] = u''

        Item.__init__(self, *args, **kwargs)


class Int(Item):
    _type = int


class Bool(Item):
    _type = bool


ConfigDescriptor = {
    u'id': Unicode(default=uuid4),
    u'creation_date': Int(default=0),
    u'receipt_salt': Unicode(default=GCE.generate_salt),

    u'version': Unicode(default=text_type(__version__)),
    u'version_db': Int(default=DATABASE_VERSION),
    u'latest_version': Unicode(default=text_type(__version__)),

    u'acme': Bool(default=False),
    u'acme_accnt_key': Unicode(),

    u'tor': Bool(default=True),
    u'tor_onion_key': Unicode(),

    u'https_enabled': Bool(default=False),
    u'https_priv_key': Unicode(),
    u'https_priv_gen': Bool(default=False),
    u'https_csr': Unicode(),
    u'https_cert': Unicode(),
    u'https_chain': Unicode(),
    u'https_dh_params': Unicode(),

    u'admin_api_token_digest': Unicode(),

    u'smtp_server': Unicode(default=u'demo.globaleaks.org'),
    u'smtp_port': Int(default=9267),
    u'smtp_username': Unicode(default=u'hey_you_should_change_me'),
    u'smtp_password': Unicode(default=u'yes_you_really_should_change_me'),
    u'smtp_source_name': Unicode(default=u'GlobaLeaks - CHANGE EMAIL ACCOUNT USED FOR NOTIFICATION'),
    u'smtp_source_email': Unicode(default=u'notification@demo.globaleaks.org'),
    u'smtp_security': Unicode(default=u'TLS'),
    u'smtp_authentication': Bool(default=True),

    u'disable_admin_notification_emails': Bool(default=False),
    u'disable_custodian_notification_emails': Bool(default=False),
    u'disable_receiver_notification_emails': Bool(default=False),

    u'tip_expiration_threshold': Int(default=72),  # Hours
    u'notification_threshold_per_hour': Int(default=20),

    u'enable_admin_exception_notification': Bool(default=False),
    u'enable_developers_exception_notification': Bool(default=True),

    u'name': Unicode(default=u''),

    u'basic_auth': Bool(default=False),
    u'basic_auth_username': Unicode(default=u''),
    u'basic_auth_password': Unicode(default=u''),

    u'hostname': Unicode(default=u''),
    u'onionservice': Unicode(default=u''),
    u'rootdomain': Unicode(default=u''),

    u'tb_download_link': Unicode(default=u'https://www.torproject.org/download/download-easy.html'),

    u'default_language': Unicode(default=u'en'),
    u'default_questionnaire': Unicode(default=u'default'),

    u'timezone': Int(default=0),

    u'maximum_filesize': Int(default=30),

    u'https_admin': Bool(default=True),
    u'https_custodian': Bool(default=True),
    u'https_whistleblower': Bool(default=True),
    u'https_receiver': Bool(default=True),
    u'allow_unencrypted': Bool(default=False),
    u'allow_iframes_inclusion': Bool(default=False),

    u'can_postpone_expiration': Bool(default=True),
    u'can_delete_submission': Bool(default=True),
    u'can_grant_permissions': Bool(default=False),

    u'allow_indexing': Bool(default=True),

    u'wizard_done': Bool(default=False),

    u'disable_submissions': Bool(default=False),
    u'disable_privacy_badge': Bool(default=False),
    u'enable_disclaimer': Bool(default=False),
    u'disable_key_code_hint': Bool(default=False),
    u'disable_donation_panel': Bool(default=False),

    u'counter_submissions': Int(default=0),

    u'enable_signup': Bool(default=False),
    u'mode': Unicode(default=u'default'),
    u'signup_tos1_enable': Bool(default=False),
    u'signup_tos2_enable': Bool(default=False),

    u'enable_experimental_features': Bool(default=False),

    u'multisite_login': Bool(default=False),
    u'simplified_login': Bool(default=False),

    u'enable_custom_privacy_badge': Bool(default=False),

    u'landing_page': Unicode(default=u'homepage'),

    u'show_small_context_cards': Bool(default=False),
    u'show_contexts_in_alphabetical_order': Bool(default=True),

    u'password_change_period': Int(default=90),  # Days
    u'wbtip_timetolive': Int(default=90),  # Days

    u'threshold_free_disk_megabytes_high': Int(default=200),
    u'threshold_free_disk_megabytes_low': Int(default=1000),

    u'threshold_free_disk_percentage_high': Int(default=3),
    u'threshold_free_disk_percentage_low': Int(default=10),

    u'context_selector_type': Unicode(default=u'list'),

    u'reachable_via_web': Bool(default=True),
    u'anonymize_outgoing_connections': Bool(default=True),

    u'ip_filter_admin': Unicode(default=u''),
    u'ip_filter_admin_enable': Bool(default=False),
    u'ip_filter_custodian': Unicode(default=u''),
    u'ip_filter_custodian_enable': Bool(default=False),
    u'ip_filter_receiver': Unicode(default=u''),
    u'ip_filter_receiver_enable': Bool(default=False),
    u'ip_filter_whistleblower': Unicode(default=u''),
    u'ip_filter_whistleblower_enable': Bool(default=False),

    u'two_factor_auth': Bool(default=False),

    u'backup': Bool(default=False),
    u'backup_d': Int(default=3),
    u'backup_w': Int(default=3),
    u'backup_m': Int(default=3),
    u'backup_remote': Bool(default=False),
    u'backup_remote_server': Unicode(default=u''),
    u'backup_remote_port': Int(default=22),
    u'backup_remote_username': Unicode(default=u''),
    u'backup_remote_password': Unicode(default=u''),

    u'enable_password_reset': Bool(default=False),
    u'enable_user_pgp_key_upload': Bool(default=True),

    u'log_level': Unicode(default=u'ERROR'),
    u'log_accesses_of_internal_users': Bool(default=False),

    u'encryption': Bool(default=False),
    u'multisite': Bool(default=False),
    u'adminonly': Bool(default=False)
}

ConfigFilters = {
    'node': [
        u'id',
        u'name',
        u'admin_api_token_digest',
        u'basic_auth',
        u'basic_auth_username',
        u'basic_auth_password',
        u'hostname',
        u'onionservice',
        u'rootdomain',
        u'tb_download_link',
        u'timezone',
        u'default_language',
        u'default_questionnaire',
        u'maximum_filesize',
        u'https_admin',
        u'https_custodian',
        u'https_whistleblower',
        u'https_receiver',
        u'allow_unencrypted',
        u'allow_iframes_inclusion',
        u'can_postpone_expiration',
        u'can_delete_submission',
        u'can_grant_permissions',
        u'allow_indexing',
        u'wizard_done',
        u'disable_submissions',
        u'disable_privacy_badge',
        u'enable_disclaimer',
        u'disable_key_code_hint',
        u'disable_donation_panel',
        u'enable_signup',
        u'mode',
        u'signup_tos1_enable',
        u'signup_tos2_enable',
        u'counter_submissions',
        u'enable_admin_exception_notification',
        u'enable_developers_exception_notification',
        u'enable_experimental_features',
        u'multisite_login',
        u'simplified_login',
        u'enable_custom_privacy_badge',
        u'landing_page',
        u'show_small_context_cards',
        u'show_contexts_in_alphabetical_order',
        u'password_change_period',
        u'wbtip_timetolive',
        u'threshold_free_disk_megabytes_high',
        u'threshold_free_disk_megabytes_low',
        u'threshold_free_disk_percentage_high',
        u'threshold_free_disk_percentage_low',
        u'context_selector_type',
        u'reachable_via_web',
        u'anonymize_outgoing_connections',
        u'creation_date',
        u'receipt_salt',
        u'version',
        u'version_db',
        u'latest_version',
        u'acme',
        u'acme_accnt_key',
        u'tor',
        u'tor_onion_key',
        u'https_enabled',
        u'https_priv_key',
        u'https_priv_gen',
        u'https_csr',
        u'https_cert',
        u'https_chain',
        u'https_dh_params',
        u'admin_api_token_digest',
        u'ip_filter_admin',
        u'ip_filter_admin_enable',
        u'ip_filter_custodian',
        u'ip_filter_custodian_enable',
        u'ip_filter_receiver',
        u'ip_filter_receiver_enable',
        u'ip_filter_whistleblower',
        u'ip_filter_whistleblower_enable',
        u'enable_password_reset',
        u'enable_user_pgp_key_upload',
        u'log_level',
        u'log_accesses_of_internal_users',
        u'encryption',
        u'two_factor_auth',
        u'multisite',
        u'adminonly',
        u'backup',
        u'backup_d',
        u'backup_m',
        u'backup_w',
        u'backup_remote',
        u'backup_remote_server',
        u'backup_remote_port',
        u'backup_remote_username',
        u'backup_remote_password'
    ],
    'notification': [
        u'smtp_server',
        u'smtp_port',
        u'smtp_username',
        u'smtp_password',
        u'smtp_source_name',
        u'smtp_source_email',
        u'smtp_security',
        u'smtp_authentication',
        u'disable_admin_notification_emails',
        u'disable_custodian_notification_emails',
        u'disable_receiver_notification_emails',
        u'tip_expiration_threshold',
        u'notification_threshold_per_hour'
    ]
}


ConfigFilters['admin_node'] = list(set(ConfigFilters['node']) - set([
    u'id',
    u'receipt_salt',
    u'acme_accnt_key',
    u'tor_onion_key',
    u'https_priv_key',
    u'https_priv_gen',
    u'https_csr',
    u'https_cert',
    u'https_chain',
    u'https_dh_params',
    u'admin_api_token_digest'
]))


ConfigFilters['admin_notification'] = list(set(ConfigFilters['notification']) - set([
    u'smtp_password'
]))


ConfigFilters['public_node'] = list(set(ConfigFilters['admin_node']) - set([
    'id',
    'version',
    'version_db',
    'basic_auth',
    'basic_auth_username',
    'basic_auth_password',
    'timezone',
    'ip_filter_admin',
    'ip_filter_admin_enable',
    'ip_filter_custodian',
    'ip_filter_custodian_enable',
    'ip_filter_receiver',
    'ip_filter_receiver_enable',
    'ip_filter_whistleblower',
    'ip_filter_whistleblower_enable',
    'threshold_free_disk_megabytes_high',
    'threshold_free_disk_megabytes_low',
    'threshold_free_disk_percentage_high',
    'threshold_free_disk_percentage_low',
    'anonymize_outgoing_connections',
    'counter_submissions',
    'encryption',
    'two_factor_auth',
    'backup',
    'backup_d',
    'backup_w',
    'backup_m',
    'backup_remote',
    'backup_remote_server',
    'backup_remote_port',
    'backup_remote_username',
    'backup_remote_password'
]))


# Settings related to general settings
ConfigFilters['general_settings'] = [
    'logo',
    'name',
    'header_title_homepage',
    'header_title_submissionpage',
    'header_title_receiptpage',
    'header_title_tippage',
    'presentation',
    'description',
    'whistleblowing_question',
    'whistleblowing_button',
    'footer',
    'maximum_filesize',
    'favicon',
    'languages_enabled',
    'default_language',
    'languages_supported'
]


ConfigL10NFilters = {
    'node': [
        u'description',
        u'presentation',
        u'footer',
        u'disclaimer_title',
        u'disclaimer_text',
        u'whistleblowing_question',
        u'whistleblowing_button',
        u'custom_privacy_badge_text',
        u'header_title_homepage',
        u'header_title_submissionpage',
        u'header_title_receiptpage',
        u'header_title_tippage',
        u'contexts_clarification',
        u'signup_tos1_title',
        u'signup_tos1_text',
        u'signup_tos1_checkbox_label',
        u'signup_tos2_title',
        u'signup_tos2_text',
        u'signup_tos2_checkbox_label'
    ],

    'notification': [
        u'activation_mail_template',
        u'activation_mail_title',
        u'admin_anomaly_activities',
        u'admin_anomaly_disk_high',
        u'admin_anomaly_disk_low',
        u'admin_anomaly_mail_template',
        u'admin_anomaly_mail_title',
        u'admin_pgp_alert_mail_template',
        u'admin_pgp_alert_mail_title',
        u'admin_signup_alert_mail_template',
        u'admin_signup_alert_mail_title',
        u'admin_test_mail_template',
        u'admin_test_mail_title',
        u'comment_mail_template',
        u'comment_mail_title',
        u'email_validation_mail_template',
        u'email_validation_mail_title',
        u'export_message_recipient',
        u'export_message_whistleblower',
        u'export_template',
        u'file_mail_template',
        u'file_mail_title',
        u'https_certificate_expiration_mail_template',
        u'https_certificate_expiration_mail_title',
        u'https_certificate_renewal_failure_mail_template',
        u'https_certificate_renewal_failure_mail_title',
        u'identity_access_authorized_mail_template',
        u'identity_access_authorized_mail_title',
        u'identity_access_denied_mail_template',
        u'identity_access_denied_mail_title',
        u'identity_access_request_mail_template',
        u'identity_access_request_mail_title',
        u'identity_provided_mail_template',
        u'identity_provided_mail_title',
        u'message_mail_template',
        u'message_mail_title',
        u'password_reset_complete_mail_template',
        u'password_reset_complete_mail_title',
        u'password_reset_validation_mail_template',
        u'password_reset_validation_mail_title',
        u'pgp_alert_mail_template',
        u'pgp_alert_mail_title',
        u'receiver_notification_limit_reached_mail_template',
        u'receiver_notification_limit_reached_mail_title',
        u'signup_mail_template',
        u'signup_mail_title',
        u'software_update_available_mail_template',
        u'software_update_available_mail_title',
        u'tip_expiration_summary_mail_template',
        u'tip_expiration_summary_mail_title',
        u'tip_mail_template',
        u'tip_mail_title',
        u'user_credentials',
        u'2fa_mail_template',
        u'2fa_mail_title'
    ]
}
