# -*- coding: UTF-8

from globaleaks.models.validators import shorttext_v, longtext_v, \
       shortlocal_v, longlocal_v, shorturl_v, longurl_v, natnum_v
from globaleaks import __version__, DATABASE_VERSION, LANGUAGES_SUPPORTED_CODES
from globaleaks.utils.utility import datetime_null
from globaleaks.security import generateRandomSalt as salt
from globaleaks.models.properties import iso_strf_time


class Item():
    def __init__(self, *args, **kwargs):
        if 'default' in kwargs:
            self.val = kwargs['default']
        else:
            raise KeyError('No default set! %s, %s' % (args, kwargs))

        self.validator = kwargs.get('validator', None)


class Unicode(Item):
    _type = unicode


class Int(Item):
    _type = int


class Bool(Item):
    _type = bool


GLConfig = {
    'private': {
        'receipt_salt': Unicode(validator=shorttext_v, default=salt()),
        'smtp_password': Unicode(validator=shorttext_v, default=u'yes_you_really_should_change_me'),
    },
    'notification': {
        'server': Unicode(validator=shorttext_v, default=u'demo.globaleaks.org'),
        'port': Int(default=9267),

        'username': Unicode(validator=shorttext_v, default=u'hey_you_should_change_me'),
        # See smtp_password in private for password

        'source_name': Unicode(validator=shorttext_v, default=u'GlobaLeaks - CHANGE EMAIL ACCOUNT USED FOR NOTIFICATION'),
        'source_email': Unicode(validator=shorttext_v, default=u'notification@demo.globaleaks.org'),

        'security': Unicode(validator=shorttext_v, default=u'TLS'),
        'disable_admin_notification_emails': Bool(default=False),
        'disable_custodian_notification_emails': Bool(default=False),
        'disable_receiver_notification_emails': Bool(default=False),
        'send_email_for_every_event': Bool(default=True), # TODO remove me, I am unused

        'tip_expiration_threshold': Int(validator=natnum_v, default=72),
        'notification_threshold_per_hour': Int(validator=natnum_v, default=20),
        'notification_suspension_time': Int(validator=natnum_v, default=(2 * 3600)), #TODO remove unused

        'exception_email_address': Unicode(validator=shorttext_v, default=u'globaleaks-stackexception@lists.globaleaks.org'),
        'exception_email_pgp_key_fingerprint': Unicode(default=u''),
        'exception_email_pgp_key_public': Unicode(default=u''),
        'exception_email_pgp_key_expiration': Unicode(default=iso_strf_time(datetime_null())), #TODO remove unused
    },
    'node': {
        'version': Unicode(default=unicode(__version__)),
        'version_db': Unicode(default=unicode(DATABASE_VERSION)),
        'name': Unicode(validator=shorttext_v, default=u''),

        'basic_auth': Bool(default=False),
        'basic_auth_username': Unicode(default=u''),
        'basic_auth_password': Unicode(default=u''),

        'public_site': Unicode(validator=shorttext_v, default=u''),
        'hidden_service': Unicode(validator=shorttext_v, default=u''),
        'tb_download_link': Unicode(validator=shorttext_v, default=u'https://www.torproject.org/download/download'),

        'default_language': Unicode(validator=shorttext_v, default=u'en'),
        'default_password': Unicode(validator=longtext_v, default=u'globaleaks'),

        # Advanced settings
        'maximum_namesize': Int(validator=natnum_v, default=128),
        'maximum_textsize': Int(validator=natnum_v, default=4096),
        'maximum_filesize': Int(validator=natnum_v, default=30),
        'tor2web_admin': Bool(default=True),
        'tor2web_custodian': Bool(default=True),
        'tor2web_whistleblower': Bool(default=False),
        'tor2web_receiver': Bool(default=True),
        'tor2web_unauth': Bool(default=True),
        'allow_unencrypted': Bool(default=True),
        'disable_encryption_warnings': Bool(default=False),
        'allow_iframes_inclusion': Bool(default=False),
        'submission_minimum_delay': Int(validator=natnum_v, default=10),
        'submission_maximum_ttl': Int(validator=natnum_v, default=10800),

        # privileges of receivers
        'can_postpone_expiration': Bool(default=False),
        'can_delete_submission': Bool(default=False),
        'can_grant_permissions': Bool(default=False),

        'ahmia': Bool(default=False),
        'allow_indexing': Bool(default=False),

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

        'simplified_login': Bool(default=True),

        'enable_custom_privacy_badge': Bool(default=False),

        'landing_page': Unicode(default=u'homepage'),

        'show_small_context_cards': Bool(default=False),
        'show_contexts_in_alphabetical_order': Bool(default=False),

        'wbtip_timetolive': Int(validator=natnum_v, default=90),

        'threshold_free_disk_megabytes_high': Int(validator=natnum_v, default=200),
        'threshold_free_disk_megabytes_medium': Int(validator=natnum_v, default=500),
        'threshold_free_disk_megabytes_low': Int(validator=natnum_v, default=1000),

        'threshold_free_disk_percentage_high': Int(default=3),
        'threshold_free_disk_percentage_medium': Int(default=5),
        'threshold_free_disk_percentage_low': Int(default=10),

        'context_selector_type': Unicode(validator=shorttext_v, default=u'list'),
    },
}
