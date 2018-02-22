# -*- coding: utf-8

from globaleaks import __version__, DATABASE_VERSION
from globaleaks.utils.security import generateRandomSalt as salt


class Item:
    _type = None

    def __init__(self, *args, **kwargs):
        self.default = kwargs['default']


class Unicode(Item):
    _type = unicode

    def __init__(self, *args, **kwargs):
        if 'default' not in kwargs:
            kwargs['default'] = u''

        Item.__init__(self,  *args, **kwargs)


class Int(Item):
    _type = int


class Bool(Item):
    _type = bool


ConfigDescriptor = {
    u'creation_date': Int(default=0),
    u'receipt_salt': Unicode(default=salt),

    u'version': Unicode(default=unicode(__version__)),
    u'version_db': Int(default=DATABASE_VERSION),
    u'latest_version': Unicode(default=unicode(__version__)),

    u'acme': Bool(default=False),
    u'acme_accnt_key': Unicode(),
    u'acme_accnt_uri': Unicode(),

    u'tor_onion_key': Unicode(), # Limits from txtorcon

    u'https_priv_key': Unicode(),
    u'https_priv_gen': Bool(default=False),
    u'https_csr': Unicode(),
    u'https_cert': Unicode(),
    u'https_chain': Unicode(),
    u'https_dh_params': Unicode(),
    u'https_enabled': Bool(default=False),

    u'admin_api_token_digest': Unicode(),

    u'smtp_server': Unicode(default=u'demo.globaleaks.org'),
    u'smtp_port': Int(default=9267),
    u'smtp_username': Unicode(default=u'hey_you_should_change_me'),
    u'smtp_password': Unicode(default=u'yes_you_really_should_change_me'),
    u'smtp_source_name': Unicode(default=u'GlobaLeaks - CHANGE EMAIL ACCOUNT USED FOR NOTIFICATION'),
    u'smtp_source_email': Unicode(default=u'notification@demo.globaleaks.org'),
    u'smtp_security': Unicode(default=u'TLS'),

    u'disable_admin_notification_emails': Bool(default=False),
    u'disable_custodian_notification_emails': Bool(default=False),
    u'disable_receiver_notification_emails': Bool(default=False),

    u'tip_expiration_threshold': Int(default=72), # Hours
    u'notification_threshold_per_hour': Int(default=20),

    u'enable_admin_exception_notification': Bool(default=True),
    u'enable_developers_exception_notification': Bool(default=True),

    u'name': Unicode(default=u''),

    u'basic_auth': Bool(default=False),
    u'basic_auth_username': Unicode(default=u''),
    u'basic_auth_password': Unicode(default=u''),

    u'hostname': Unicode(default=u''),
    u'onionservice': Unicode(default=u''),
    u'rootdomain': Unicode(default=u''),

    u'tb_download_link': Unicode(default=u'https://www.torproject.org/download/download-easy.html.en'),

    u'default_language': Unicode(default=u'en'),
    u'default_questionnaire': Unicode(default=u'default'),

    u'maximum_filesize': Int(default=30),

    u'https_admin': Bool(default=True),
    u'https_custodian': Bool(default=True),
    u'https_whistleblower': Bool(default=True),
    u'https_receiver': Bool(default=True),
    u'allow_unencrypted': Bool(default=False),
    u'disable_encryption_warnings': Bool(default=False),
    u'allow_iframes_inclusion': Bool(default=False),

    u'can_postpone_expiration': Bool(default=True),
    u'can_delete_submission': Bool(default=True),
    u'can_grant_permissions': Bool(default=False),

    u'allow_indexing': Bool(default=True),

    u'wizard_done': Bool(default=False),

    u'disable_submissions': Bool(default=False),
    u'disable_privacy_badge': Bool(default=False),
    u'disable_security_awareness_badge': Bool(default=False),
    u'disable_security_awareness_questions': Bool(default=False),
    u'disable_key_code_hint': Bool(default=False),
    u'disable_donation_panel': Bool(default=False),

    u'enable_captcha': Bool(default=True),
    u'enable_proof_of_work': Bool(default=True),

    u'enable_signup': Bool(default=False),

    u'enable_experimental_features': Bool(default=False),

    u'simplified_login': Bool(default=False),

    u'enable_custom_privacy_badge': Bool(default=False),

    u'landing_page': Unicode(default=u'homepage'),

    u'show_small_context_cards': Bool(default=False),
    u'show_contexts_in_alphabetical_order': Bool(default=True),

    u'wbtip_timetolive': Int(default=90), # Days

    u'threshold_free_disk_megabytes_high': Int(default=200),
    u'threshold_free_disk_megabytes_low': Int(default=1000),

    u'threshold_free_disk_percentage_high': Int(default=3),
    u'threshold_free_disk_percentage_low': Int(default=10),

    u'context_selector_type': Unicode(default=u'list'),

    u'reachable_via_web': Bool(default=True),
    u'anonymize_outgoing_connections': Bool(default=True)
}

ConfigFilters = {
    'node': set([
        u'name',
        u'admin_api_token_digest',
        u'basic_auth',
        u'basic_auth_username',
        u'basic_auth_password',
        u'hostname',
        u'onionservice',
        u'rootdomain',
        u'tb_download_link',
        u'default_language',
        u'default_questionnaire',
        u'maximum_filesize',
        u'https_admin',
        u'https_custodian',
        u'https_whistleblower',
        u'https_receiver',
        u'allow_unencrypted',
        u'disable_encryption_warnings',
        u'allow_iframes_inclusion',
        u'can_postpone_expiration',
        u'can_delete_submission',
        u'can_grant_permissions',
        u'allow_indexing',
        u'wizard_done',
        u'disable_submissions',
        u'disable_privacy_badge',
        u'disable_security_awareness_badge',
        u'disable_security_awareness_questions',
        u'disable_key_code_hint',
        u'disable_donation_panel',
        u'enable_signup',
        u'enable_captcha',
        u'enable_proof_of_work',
        u'enable_admin_exception_notification',
        u'enable_developers_exception_notification',
        u'enable_experimental_features',
        u'simplified_login',
        u'enable_custom_privacy_badge',
        u'landing_page',
        u'show_small_context_cards',
        u'show_contexts_in_alphabetical_order',
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
        u'acme_accnt_uri',
        u'tor_onion_key',
        u'https_priv_key',
        u'https_priv_gen',
        u'https_csr',
        u'https_cert',
        u'https_chain',
        u'https_dh_params',
        u'https_enabled',
        u'admin_api_token_digest'
    ]),
    'notification': set([
        u'smtp_server',
        u'smtp_port',
        u'smtp_username',
        u'smtp_password',
        u'smtp_source_name',
        u'smtp_source_email',
        u'smtp_security',
        u'disable_admin_notification_emails',
        u'disable_custodian_notification_emails',
        u'disable_receiver_notification_emails',
        u'tip_expiration_threshold',
        u'notification_threshold_per_hour'
    ])
}


ConfigFilters['admin_node'] = ConfigFilters['node'] - set([
    u'receipt_salt',
    u'acme_accnt_key',
    u'acme_accnt_uri',
    u'tor_onion_key',
    u'https_priv_key',
    u'https_priv_gen',
    u'https_csr',
    u'https_cert',
    u'https_chain',
    u'https_dh_params',
    u'admin_api_token_digest'
])


ConfigFilters['admin_notification'] = ConfigFilters['notification'] - set([
    u'smtp_password'
])


ConfigFilters['public_node'] = ConfigFilters['admin_node'] - set([
    'version',
    'version_db',
    'basic_auth',
    'basic_auth_username',
    'basic_auth_password',
    'default_timezone',
    'threshold_free_disk_megabytes_high',
    'threshold_free_disk_megabytes_low',
    'threshold_free_disk_percentage_high',
    'threshold_free_disk_percentage_low',
    'anonymize_outgoing_connections'
])
