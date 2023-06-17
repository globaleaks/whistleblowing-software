# -*- encoding: utf-8 -*-
from globaleaks import __version__, DATABASE_VERSION
from globaleaks.models.config_desc import Unicode, Int, Bool
from globaleaks.utils.crypto import GCE
from globaleaks.utils.utility import datetime_null, iso_strf_time


GLConfig_v_37 = {
    'private': {
        'receipt_salt': Unicode(default=GCE.generate_salt()),
        'smtp_password': Unicode(default='yes_you_really_should_change_me'),

        'version': Unicode(default=Unicode(__version__)),
        'version_db': Int(default=DATABASE_VERSION),

        'https_priv_key': Unicode(),
        'https_priv_gen': Bool(default=False),
        'https_csr': Unicode(),
        'https_cert': Unicode(),
        'https_chain': Unicode(),
        'https_dh_params': Unicode(),
        'https_enabled': Bool(default=False),
    },
    'notification': {
        'server': Unicode(default='demo.globaleaks.org'),
        'port': Int(default=9267),

        'username': Unicode(default='hey_you_should_change_me'),
        # See smtp_password in private for password

        'source_email': Unicode(default='notification@demo.globaleaks.org'),

        'security': Unicode(default='TLS'),
        'disable_admin_notification_emails': Bool(default=False),
        'disable_custodian_notification_emails': Bool(default=False),
        'disable_receiver_notification_emails': Bool(default=False),

        'tip_expiration_threshold': Int(default=72),  # Hours

        'exception_email_address': Unicode(default='globaleaks-stackexception@lists.globaleaks.org'),
        'exception_email_pgp_key_fingerprint': Unicode(default=''),
        'exception_email_pgp_key_public': Unicode(default=''),
        'exception_email_pgp_key_expiration': Unicode(default=iso_strf_time(datetime_null())),
    },
    'node': {
        'name': Unicode(default=''),

        'basic_auth': Bool(default=False),
        'basic_auth_username': Unicode(default=''),
        'basic_auth_password': Unicode(default=''),

        'public_site': Unicode(default=''),
        'hidden_service': Unicode(default=''),
        'tb_download_link': Unicode(default='https://www.torproject.org/download/download'),

        'default_language': Unicode(default='en'),

        # Advanced settings
        'maximum_filesize': Int(default=30),
        'tor2web_admin': Bool(default=True),
        'tor2web_custodian': Bool(default=True),
        'tor2web_whistleblower': Bool(default=False),
        'tor2web_receiver': Bool(default=True),
        'tor2web_unauth': Bool(default=True),
        'allow_unencrypted': Bool(default=True),
        'disable_encryption_warnings': Bool(default=False),
        'allow_iframes_inclusion': Bool(default=False),
        'submission_minimum_delay': Int(default=10),

        # privileges of receivers
        'can_postpone_expiration': Bool(default=False),
        'can_delete_submission': Bool(default=False),
        'can_grant_permissions': Bool(default=False),

        'allow_indexing': Bool(default=True),

        'wizard_done': Bool(default=False),

        'disable_submissions': Bool(default=False),
        'disable_privacy_badge': Bool(default=False),
        'disable_key_code_hint': Bool(default=False),

        'enable_captcha': Bool(default=True),

        'simplified_login': Bool(default=True),

        'enable_custom_privacy_badge': Bool(default=False),

        'landing_page': Unicode(default='homepage'),

        'show_small_context_cards': Bool(default=False),
        'show_contexts_in_alphabetical_order': Bool(default=False),

        'wbtip_timetolive': Int(default=90),  # Days

        'threshold_free_disk_megabytes_high': Int(default=200),
        'threshold_free_disk_megabytes_medium': Int(default=500),
        'threshold_free_disk_megabytes_low': Int(default=1000),

        'threshold_free_disk_percentage_high': Int(default=3),
        'threshold_free_disk_percentage_medium': Int(default=5),
        'threshold_free_disk_percentage_low': Int(default=10),

        'context_selector_type': Unicode(default='list'),
    },
}
