# -*- coding: utf-8 -*-
from sqlalchemy import not_

from six import text_type

from globaleaks import __version__
from globaleaks.models import Config, ConfigL10N, EnabledLanguage
from globaleaks.models.properties import *
from globaleaks.models.config_desc import ConfigDescriptor, ConfigFilters

class ConfigFactory(object):
    """
    This factory depends on the following attributes set by the sub class:
    """
    def __init__(self, session, tid, group, *args, **kwargs):
        self.session = session
        self.tid = tid
        self.group = text_type(group)
        self.res = None
        self.keys = ConfigFilters[group]

    def _query_group(self):
        self.res = {c.var_name: c for c in self.session.query(Config).filter(Config.tid == self.tid, Config.var_name.in_(ConfigFilters[self.group]))}

    def update(self, request):
        self._query_group()

        for key in (key for key in request.keys() if key in self.res):
            self.res[key].set_v(request[key])

    def get_cfg(self, var_name):
        return self.session.query(Config).filter(Config.tid == self.tid, Config.var_name == var_name).one()

    def get_val(self, var_name):
        return self.get_cfg(var_name).get_v()

    def set_val(self, var_name, value):
        if self.res is not None and var_name in self.res:
            self.res[var_name].set_v(value)
        else:
            self.get_cfg(var_name).set_v(value)

    def serialize(self):
        self._query_group()
        return {k: self.res[k].get_v() for k in self.res}

    def clean_and_add(self):
        actual = set([c[0] for c in self.session.query(Config.var_name).filter(Config.tid == self.tid)])
        allowed = set(ConfigDescriptor.keys())
        extra = list(actual - allowed)

        if extra:
            self.session.query(Config).filter(Config.tid == self.tid, Config.var_name.in_(extra)).delete(synchronize_session='fetch')

        missing = list(allowed - actual)
        for key in missing:
            self.session.add(Config(self.tid, key, ConfigDescriptor[key].default))

        return len(missing), len(extra)


class ConfigL10NFactory(object):
    keys = []

    def __init__(self, session, tid):
        self.session = session
        self.tid = tid

    def initialize(self, lang_code, initialization_dict, keys=None):
        if keys is None:
            keys = self.keys

        for key in keys:
            value = initialization_dict[key][lang_code] if key in initialization_dict else ''
            self.session.add(ConfigL10N(self.tid, lang_code, key, value))

    def get_all(self, lang_code):
        return [r for r in self.session.query(ConfigL10N).filter(ConfigL10N.tid == self.tid, ConfigL10N.lang == lang_code, ConfigL10N.var_name.in_(list(self.keys)))]

    def localized_dict(self, lang_code):
        rows = self.get_all(lang_code)
        return {c.var_name : c.value for c in rows if c.var_name in self.keys}

    def update(self, request, lang_code):
        c_map = {c.var_name : c for c in self.get_all(lang_code)}

        for key in self.keys:
            c_map[key].set_v(request[key])

    def update_defaults(self, langs, l10n_data_src, reset=False):
        for lang_code in langs:
            old_keys = []

            for cfg in self.get_all(lang_code):
                old_keys.append(cfg.var_name)
                if (not cfg.customized or reset) and cfg.var_name in l10n_data_src:
                    cfg.value = l10n_data_src[cfg.var_name][lang_code]

            ConfigL10NFactory.initialize(self, lang_code, l10n_data_src, list(set(self.keys) - set(old_keys)))

    def get_val(self, var_name, lang_code):
        cfg = self.session.query(ConfigL10N.value).filter(ConfigL10N.tid == self.tid, ConfigL10N.lang == lang_code, ConfigL10N.var_name == var_name).one_or_none()
        if cfg is None:
            return ''

        return cfg.value

    def set_val(self, var_name, lang_code, value):
        cfg = self.session.query(ConfigL10N).filter(ConfigL10N.tid == self.tid, ConfigL10N.lang == lang_code, ConfigL10N.var_name == var_name).one()
        cfg.set_v(value)


class NodeL10NFactory(ConfigL10NFactory):
    keys = [
        u'description',
        u'presentation',
        u'footer',
        u'disclaimer_title',
        u'disclaimer_text',
        u'whistleblowing_question',
        u'whistleblowing_button',
        u'whistleblowing_receipt_prompt',
        u'custom_privacy_badge_text',
        u'header_title_homepage',
        u'header_title_submissionpage',
        u'header_title_receiptpage',
        u'header_title_tippage',
        u'contexts_clarification'
    ]


class NotificationL10NFactory(ConfigL10NFactory):
    keys = [
        u'admin_anomaly_mail_template',
        u'admin_anomaly_mail_title',
        u'admin_anomaly_disk_low',
        u'admin_anomaly_disk_high',
        u'admin_anomaly_activities',
        u'admin_pgp_alert_mail_template',
        u'admin_pgp_alert_mail_title',
        u'admin_test_mail_template',
        u'admin_test_mail_title',
        u'pgp_alert_mail_template',
        u'pgp_alert_mail_title',
        u'tip_mail_template',
        u'tip_mail_title',
        u'file_mail_template',
        u'file_mail_title',
        u'comment_mail_template',
        u'comment_mail_title',
        u'message_mail_template',
        u'message_mail_title',
        u'tip_expiration_summary_mail_template',
        u'tip_expiration_summary_mail_title',
        u'receiver_notification_limit_reached_mail_template',
        u'receiver_notification_limit_reached_mail_title',
        u'identity_access_authorized_mail_template',
        u'identity_access_authorized_mail_title',
        u'identity_access_denied_mail_template',
        u'identity_access_denied_mail_title',
        u'identity_access_request_mail_template',
        u'identity_access_request_mail_title',
        u'identity_provided_mail_template',
        u'identity_provided_mail_title',
        u'export_template',
        u'export_message_whistleblower',
        u'export_message_recipient',
        u'https_certificate_expiration_mail_template',
        u'https_certificate_expiration_mail_title',
        u'software_update_available_mail_template',
        u'software_update_available_mail_title',
        u'signup_mail_title',
        u'signup_mail_template',
        u'activation_mail_title',
        u'activation_mail_template',
        u'admin_signup_alert_mail_title',
        u'admin_signup_alert_mail_template',
        u'email_validation_mail_title',
        u'email_validation_mail_template'
    ]

    def __init__(self, session, tid, *args, **kwargs):
        ConfigL10NFactory.__init__(self, session, tid, *args, **kwargs)

    def reset_templates(self, l10n_data_src):
        langs = EnabledLanguage.list(self.session, self.tid)
        self.update_defaults(langs, l10n_data_src, reset=True)


def update_defaults(session, tid, appdata):
    session.query(Config).filter(Config.tid == tid, not_(Config.var_name.in_(ConfigDescriptor.keys()))).delete(synchronize_session='fetch')

    ConfigFactory(session, tid, 'node').clean_and_add()
    ConfigFactory(session, tid, 'notification').clean_and_add()

    # Set the system version to the current aligned cfg
    ConfigFactory(session, tid, 'node').set_val(u'version', __version__)

    langs = EnabledLanguage.list(session, tid)

    session.query(ConfigL10N).filter(ConfigL10N.tid == tid,
                                            not_(ConfigL10N.var_name.in_(NodeL10NFactory.keys + NotificationL10NFactory.keys))).delete(synchronize_session='fetch')

    NodeL10NFactory(session, tid).update_defaults(langs, appdata['node'])
    NotificationL10NFactory(session, tid).update_defaults(langs, appdata['templates'])


def add_new_lang(session, tid, lang_code, appdata_dict):
    session.add(EnabledLanguage(tid, lang_code))

    NodeL10NFactory(session, tid).initialize(lang_code, appdata_dict['node'])
    NotificationL10NFactory(session, tid).initialize(lang_code, appdata_dict['templates'])


def system_cfg_init(session, tid):
    for var_name, desc in ConfigDescriptor.items():
        if callable(desc.default):
            default = desc.default()
        else:
            default = desc.default

        session.add(Config(tid, var_name, default))
