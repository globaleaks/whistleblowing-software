# -*- coding: utf-8

from globaleaks import __version__, DATABASE_VERSION
from globaleaks.models.validators import shorttext_v, longtext_v, \
    natnum_v, range_v
from globaleaks.security import generateRandomSalt as salt


class Item:
    _type = None

    def __init__(self, *args, **kwargs):
        self.default = kwargs['default']
        self.validator = kwargs.get('validator', None)

    def __repr__(self):
        return '<Item({})>'.format(self._type.__name__)


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


GLConfig = {
    'private': {
        'label': Unicode(validator=shorttext_v, default=u''),
        'active': Bool(default=True),
        'creation_date': Int(default=0),
        'receipt_salt': Unicode(validator=shorttext_v, default=salt()), # is always customized
        'smtp_password': Unicode(validator=shorttext_v, default=u'yes_you_really_should_change_me'),

        'version': Unicode(default=unicode(__version__)),
        'version_db': Int(default=DATABASE_VERSION),
        'latest_version': Unicode(default=unicode(__version__)),

        'acme': Bool(default=False),
        'acme_accnt_key': Unicode(),
        'acme_accnt_uri': Unicode(),

        'tor_onion_key': Unicode(validator=longtext_v), # Limits from txtorcon

        'https_priv_key': Unicode(),
        'https_priv_gen': Bool(default=False),
        'https_csr': Unicode(),
        'https_cert': Unicode(),
        'https_chain': Unicode(),
        'https_dh_params': Unicode(),
        'https_enabled': Bool(default=False),

        'admin_api_token_digest': Unicode(),
    },
    'notification': {
        'server': Unicode(validator=shorttext_v, default=u'demo.globaleaks.org'),
        'port': Int(validator=natnum_v, default=9267),

        'username': Unicode(validator=shorttext_v, default=u'hey_you_should_change_me'),
        # See smtp_password in private for password

        'source_name': Unicode(validator=shorttext_v, default=u'GlobaLeaks - CHANGE EMAIL ACCOUNT USED FOR NOTIFICATION'),
        'source_email': Unicode(validator=shorttext_v, default=u'notification@demo.globaleaks.org'),

        'security': Unicode(validator=shorttext_v, default=u'TLS'),
        'disable_admin_notification_emails': Bool(default=False),
        'disable_custodian_notification_emails': Bool(default=False),
        'disable_receiver_notification_emails': Bool(default=False),

        'tip_expiration_threshold': Int(validator=natnum_v, default=72), # Hours
        'notification_threshold_per_hour': Int(validator=natnum_v, default=20),

        'enable_admin_exception_notification': Bool(default=True),
        'enable_developers_exception_notification': Bool(default=True)
    },
    'node': {
        'name': Unicode(validator=shorttext_v, default=u''),

        'basic_auth': Bool(default=False),
        'basic_auth_username': Unicode(default=u''),
        'basic_auth_password': Unicode(default=u''),

        'hostname': Unicode(validator=shorttext_v, default=u''),
        'onionservice': Unicode(validator=shorttext_v, default=u''),

        'tb_download_link': Unicode(validator=shorttext_v, default=u'https://www.torproject.org/download/download-easy.html.en'),

        'default_language': Unicode(validator=shorttext_v, default=u'en'),
        'default_password': Unicode(validator=longtext_v, default=u'globaleaks'),
        'default_questionnaire': Unicode(validator=shorttext_v, default=u'default'),

        # Advanced settings
        'maximum_namesize': Int(validator=natnum_v, default=128),
        'maximum_textsize': Int(validator=natnum_v, default=4096),
        'maximum_filesize': Int(validator=natnum_v, default=30),
        'tor2web_admin': Bool(default=True),
        'tor2web_custodian': Bool(default=True),
        'tor2web_whistleblower': Bool(default=True),
        'tor2web_receiver': Bool(default=True),
        'allow_unencrypted': Bool(default=True),
        'disable_encryption_warnings': Bool(default=False),
        'allow_iframes_inclusion': Bool(default=False),

        # privileges of receivers
        'can_postpone_expiration': Bool(default=False),
        'can_delete_submission': Bool(default=False),
        'can_grant_permissions': Bool(default=False),

        'allow_indexing': Bool(default=True),

        'wizard_done': Bool(default=False),

        'disable_submissions': Bool(default=False),
        'disable_privacy_badge': Bool(default=False),
        'disable_security_awareness_badge': Bool(default=False),
        'disable_security_awareness_questions': Bool(default=False),
        'disable_key_code_hint': Bool(default=False),
        'disable_donation_panel': Bool(default=False),

        'enable_captcha': Bool(default=True),
        'enable_proof_of_work': Bool(default=True),

        'enable_experimental_features': Bool(default=False),

        'simplified_login': Bool(default=False),

        'enable_custom_privacy_badge': Bool(default=False),

        'landing_page': Unicode(default=u'homepage'),

        'show_small_context_cards': Bool(default=False),
        'show_contexts_in_alphabetical_order': Bool(default=True),

        'wbtip_timetolive': Int(validator=range_v(5, 365*2), default=90), # Days

        'threshold_free_disk_megabytes_high': Int(validator=natnum_v, default=200),
        'threshold_free_disk_megabytes_low': Int(validator=natnum_v, default=1000),

        'threshold_free_disk_percentage_high': Int(default=3),
        'threshold_free_disk_percentage_low': Int(default=10),

        'context_selector_type': Unicode(validator=shorttext_v, default=u'list'),

        'reachable_via_web': Bool(default=True),
        'anonymize_outgoing_connections': Bool(default=True),
    },
}
