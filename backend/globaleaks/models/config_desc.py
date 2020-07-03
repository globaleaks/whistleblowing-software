# -*- coding: utf-8
from globaleaks import __version__, DATABASE_VERSION
from globaleaks.utils.crypto import GCE
from globaleaks.utils.utility import uuid4


class Item:
    _type = None

    def __init__(self, *args, **kwargs):
        self.default = kwargs['default']


class Unicode(Item):
    _type = str

    def __init__(self, *args, **kwargs):
        if 'default' not in kwargs:
            kwargs['default'] = ''

        Item.__init__(self, *args, **kwargs)


class Int(Item):
    _type = int


class Bool(Item):
    _type = bool


ConfigDescriptor = {
    'id': Unicode(default=uuid4),
    'creation_date': Int(default=0),
    'receipt_salt': Unicode(default=GCE.generate_salt),

    'version': Unicode(default=str(__version__)),
    'version_db': Int(default=DATABASE_VERSION),
    'latest_version': Unicode(default=str(__version__)),

    'acme': Bool(default=False),
    'acme_accnt_key': Unicode(),

    'tor': Bool(default=True),
    'tor_onion_key': Unicode(),

    'https_enabled': Bool(default=False),
    'https_priv_key': Unicode(),
    'https_priv_gen': Bool(default=False),
    'https_csr': Unicode(),
    'https_cert': Unicode(),
    'https_chain': Unicode(),
    'https_preload': Bool(default=False),

    'admin_api_token_digest': Unicode(),

    'smtp_server': Unicode(default='mail.globaleaks.org'),
    'smtp_port': Int(default=9267),
    'smtp_username': Unicode(default='globaleaks'),
    'smtp_password': Unicode(default='globaleaks'),
    'smtp_source_email': Unicode(default='notification@mail.globaleaks.org'),
    'smtp_security': Unicode(default='TLS'),
    'smtp_authentication': Bool(default=True),

    'disable_admin_notification_emails': Bool(default=False),
    'disable_custodian_notification_emails': Bool(default=False),
    'disable_receiver_notification_emails': Bool(default=False),

    'tip_expiration_threshold': Int(default=72),  # Hours

    'enable_admin_exception_notification': Bool(default=False),
    'enable_developers_exception_notification': Bool(default=True),

    'name': Unicode(default=''),

    'basic_auth': Bool(default=False),
    'basic_auth_username': Unicode(default=''),
    'basic_auth_password': Unicode(default=''),

    'hostname': Unicode(default=''),
    'onionservice': Unicode(default=''),
    'rootdomain': Unicode(default=''),

    'tb_download_link': Unicode(default='https://www.torproject.org/download/download-easy.html'),

    'default_language': Unicode(default='en'),
    'default_questionnaire': Unicode(default='default'),

    'timezone': Int(default=0),

    'maximum_filesize': Int(default=30),

    'https_admin': Bool(default=True),
    'https_custodian': Bool(default=True),
    'https_whistleblower': Bool(default=True),
    'https_receiver': Bool(default=True),
    'frame_ancestors': Unicode(default=''),

    'can_postpone_expiration': Bool(default=True),
    'can_delete_submission': Bool(default=True),
    'can_grant_permissions': Bool(default=False),

    'allow_indexing': Bool(default=True),

    'wizard_done': Bool(default=False),

    'disable_submissions': Bool(default=False),
    'disable_privacy_badge': Bool(default=False),
    'enable_disclaimer': Bool(default=False),
    'enable_receipt_hint': Bool(default=False),
    'enable_private_labels': Bool(default=False),

    'enable_ricochet_panel': Bool(default=False),
    'ricochet_address': Unicode(default=''),

    'do_not_expose_users_names': Bool(default=False),

    'counter_submissions': Int(default=0),

    'enable_signup': Bool(default=False),
    'mode': Unicode(default='default'),
    'signup_tos1_enable': Bool(default=False),
    'signup_tos2_enable': Bool(default=False),

    'enable_custodian': Bool(default=False),
    'enable_scoring_system': Bool(default=False),

    'multisite_login': Bool(default=False),
    'simplified_login': Bool(default=False),

    'enable_custom_privacy_badge': Bool(default=False),

    'show_contexts_in_alphabetical_order': Bool(default=True),

    'password_change_period': Int(default=365),  # Days
    'wbtip_timetolive': Int(default=365),  # Days

    'threshold_free_disk_megabytes_high': Int(default=200),
    'threshold_free_disk_megabytes_low': Int(default=1000),

    'threshold_free_disk_percentage_high': Int(default=3),
    'threshold_free_disk_percentage_low': Int(default=10),

    'context_selector_type': Unicode(default='list'),

    'reachable_via_web': Bool(default=True),
    'anonymize_outgoing_connections': Bool(default=False),

    'ip_filter_admin': Unicode(default=''),
    'ip_filter_admin_enable': Bool(default=False),
    'ip_filter_custodian': Unicode(default=''),
    'ip_filter_custodian_enable': Bool(default=False),
    'ip_filter_receiver': Unicode(default=''),
    'ip_filter_receiver_enable': Bool(default=False),
    'ip_filter_whistleblower': Unicode(default=''),
    'ip_filter_whistleblower_enable': Bool(default=False),

    'two_factor': Bool(default=False),

    'backup': Bool(default=False),
    'backup_d': Int(default=3),
    'backup_w': Int(default=3),
    'backup_m': Int(default=3),
    'backup_remote': Bool(default=False),
    'backup_remote_server': Unicode(default=''),
    'backup_remote_port': Int(default=22),
    'backup_remote_username': Unicode(default=''),
    'backup_remote_password': Unicode(default=''),

    'log_level': Unicode(default='ERROR'),
    'log_accesses_of_internal_users': Bool(default=False),

    'encryption': Bool(default=True),
    'escrow': Bool(default=True),
    'crypto_escrow_pub_key': Unicode(default=''),

    'multisite': Bool(default=False),
    'adminonly': Bool(default=False)
}

ConfigFilters = {
    'node': [
        'id',
        'name',
        'admin_api_token_digest',
        'basic_auth',
        'basic_auth_username',
        'basic_auth_password',
        'hostname',
        'onionservice',
        'rootdomain',
        'tb_download_link',
        'timezone',
        'default_language',
        'default_questionnaire',
        'maximum_filesize',
        'https_admin',
        'https_custodian',
        'https_whistleblower',
        'https_receiver',
        'frame_ancestors',
        'can_postpone_expiration',
        'can_delete_submission',
        'can_grant_permissions',
        'allow_indexing',
        'wizard_done',
        'disable_submissions',
        'disable_privacy_badge',
        'enable_disclaimer',
        'enable_receipt_hint',
        'enable_private_labels',
        'enable_ricochet_panel',
        'ricochet_address',
        'do_not_expose_users_names',
        'enable_signup',
        'mode',
        'signup_tos1_enable',
        'signup_tos2_enable',
        'counter_submissions',
        'enable_admin_exception_notification',
        'enable_developers_exception_notification',
        'enable_custodian',
        'enable_scoring_system',
        'multisite_login',
        'simplified_login',
        'enable_custom_privacy_badge',
        'show_contexts_in_alphabetical_order',
        'password_change_period',
        'wbtip_timetolive',
        'threshold_free_disk_megabytes_high',
        'threshold_free_disk_megabytes_low',
        'threshold_free_disk_percentage_high',
        'threshold_free_disk_percentage_low',
        'context_selector_type',
        'reachable_via_web',
        'anonymize_outgoing_connections',
        'creation_date',
        'receipt_salt',
        'version',
        'version_db',
        'latest_version',
        'acme',
        'acme_accnt_key',
        'tor',
        'tor_onion_key',
        'https_enabled',
        'https_priv_key',
        'https_priv_gen',
        'https_csr',
        'https_cert',
        'https_chain',
        'https_preload',
        'admin_api_token_digest',
        'ip_filter_admin',
        'ip_filter_admin_enable',
        'ip_filter_custodian',
        'ip_filter_custodian_enable',
        'ip_filter_receiver',
        'ip_filter_receiver_enable',
        'ip_filter_whistleblower',
        'ip_filter_whistleblower_enable',
        'log_level',
        'log_accesses_of_internal_users',
        'two_factor',
        'encryption',
        'escrow',
        'crypto_escrow_pub_key',
        'multisite',
        'adminonly',
        'backup',
        'backup_d',
        'backup_m',
        'backup_w',
        'backup_remote',
        'backup_remote_server',
        'backup_remote_port',
        'backup_remote_username',
        'backup_remote_password'
    ],
    'notification': [
        'smtp_server',
        'smtp_port',
        'smtp_username',
        'smtp_password',
        'smtp_source_email',
        'smtp_security',
        'smtp_authentication',
        'disable_admin_notification_emails',
        'disable_custodian_notification_emails',
        'disable_receiver_notification_emails',
        'tip_expiration_threshold'
    ]
}


ConfigFilters['admin_node'] = list(set(ConfigFilters['node']) - set([
    'id',
    'receipt_salt',
    'acme_accnt_key',
    'tor_onion_key',
    'https_priv_key',
    'https_priv_gen',
    'https_csr',
    'https_cert',
    'https_chain',
    'admin_api_token_digest'
]))


ConfigFilters['admin_notification'] = list(set(ConfigFilters['notification']) - set([
    'smtp_password'
]))


ConfigFilters['public_node'] = list(set(ConfigFilters['admin_node']) - set([
    'id',
    'version',
    'version_db',
    'basic_auth',
    'basic_auth_username',
    'basic_auth_password',
    'crypto_escrow_pub_key',
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
    'header_title_prefix',
    'header_title_homepage',
    'header_title_submissionpage',
    'presentation',
    'description',
    'whistleblowing_question',
    'whistleblowing_button',
    'footer',
    'maximum_filesize',
    'favicon',
    'languages_enabled',
    'default_language',
    'languages_supported',
    'enable_ricochet_panel',
    'ricochet_address'
]


ConfigL10NFilters = {
    'node': [
        'description',
        'presentation',
        'footer',
        'disclaimer_title',
        'disclaimer_text',
        'whistleblowing_question',
        'whistleblowing_button',
        'custom_privacy_badge_text',
        'header_title_prefix',
        'header_title_homepage',
        'header_title_submissionpage',
        'contexts_clarification',
        'signup_tos1_title',
        'signup_tos1_text',
        'signup_tos1_checkbox_label',
        'signup_tos2_title',
        'signup_tos2_text',
        'signup_tos2_checkbox_label'
    ],

    'notification': [
        'activation_mail_template',
        'activation_mail_title',
        'account_activation_mail_template',
        'account_activation_mail_title',
        'admin_anomaly_activities',
        'admin_anomaly_disk_high',
        'admin_anomaly_disk_low',
        'admin_anomaly_mail_template',
        'admin_anomaly_mail_title',
        'admin_pgp_alert_mail_template',
        'admin_pgp_alert_mail_title',
        'admin_signup_alert_mail_template',
        'admin_signup_alert_mail_title',
        'admin_test_mail_template',
        'admin_test_mail_title',
        'comment_mail_template',
        'comment_mail_title',
        'email_validation_mail_template',
        'email_validation_mail_title',
        'export_message_recipient',
        'export_message_whistleblower',
        'export_template',
        'file_mail_template',
        'file_mail_title',
        'https_certificate_expiration_mail_template',
        'https_certificate_expiration_mail_title',
        'https_certificate_renewal_failure_mail_template',
        'https_certificate_renewal_failure_mail_title',
        'identity_access_authorized_mail_template',
        'identity_access_authorized_mail_title',
        'identity_access_denied_mail_template',
        'identity_access_denied_mail_title',
        'identity_access_request_mail_template',
        'identity_access_request_mail_title',
        'identity_provided_mail_template',
        'identity_provided_mail_title',
        'message_mail_template',
        'message_mail_title',
        'password_reset_validation_mail_template',
        'password_reset_validation_mail_title',
        'pgp_alert_mail_template',
        'pgp_alert_mail_title',
        'receiver_notification_limit_reached_mail_template',
        'receiver_notification_limit_reached_mail_title',
        'signup_mail_template',
        'signup_mail_title',
        'software_update_available_mail_template',
        'software_update_available_mail_title',
        'tip_expiration_summary_mail_template',
        'tip_expiration_summary_mail_title',
        'tip_mail_template',
        'tip_mail_title',
        'user_credentials'
    ]
}
