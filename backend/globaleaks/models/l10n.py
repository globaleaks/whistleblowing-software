# -*- coding: utf-8 -*-
from storm.expr import In, Not
from storm.locals import Unicode, Bool

from globaleaks import LANGUAGES_SUPPORTED_CODES, models


class EnabledLanguage(models.ModelWithTID):
    __storm_table__ = 'enabledlanguage'
    __storm_primary__ = ('tid', 'name')

    name = Unicode()

    def __init__(self, tid=1, name=None, migrate=False):
        if migrate:
            return

        self.tid = tid
        self.name = unicode(name)

    @classmethod
    def list(cls, store, tid):
        return [name for name in store.find(EnabledLanguage.name, EnabledLanguage.tid==tid)]

    @classmethod
    def tid_list(cls, store, tid_list):
        return [(lang.tid, lang.name) for lang in store.find(EnabledLanguage, In(EnabledLanguage.tid, tid_list)).order_by('tid', 'name')]

    @classmethod
    def add_new_lang(cls, store, tid, lang_code, appdata_dict):
        store.add(cls(tid, lang_code))

        NodeL10NFactory(store, tid).initialize(lang_code, appdata_dict['node'])
        NotificationL10NFactory(store, tid).initialize(lang_code, appdata_dict['templates'])

    @classmethod
    def add_all_supported_langs(cls, store, tid, appdata_dict):
        for lang_code in LANGUAGES_SUPPORTED_CODES:
            cls.add_new_lang(store, tid, lang_code, appdata_dict)


class ConfigL10N(models.ModelWithTID):
    __storm_table__ = 'config_l10n'
    __storm_primary__ = ('tid', 'lang', 'var_name')

    lang = Unicode()
    var_name = Unicode()
    value = Unicode()
    customized = Bool(default=False)

    def __init__(self, tid=1, lang_code=None, var_name=None, value='', migrate=False):
        if migrate:
            return

        self.tid = tid
        self.lang = unicode(lang_code)
        self.var_name = unicode(var_name)
        self.value = unicode(value)

    def set_v(self, value):
        value = unicode(value)
        if self.value != value:
            self.value = value
            self.customized = True


class ConfigL10NFactory(object):
    keys = []
    unmodifiable_keys = []
    modifiable_keys = []

    def __init__(self, store, tid):
        self.store = store
        self.tid = tid

    def initialize(self, lang_code, initialization_dict, keys=None):
        if keys is None:
            keys = self.keys

        for key in keys:
            value = initialization_dict[key][lang_code] if key in initialization_dict else ''
            self.store.add(ConfigL10N(self.tid, lang_code, key, value))

    def get_all(self, lang_code):
        return [r for r in self.store.find(ConfigL10N, ConfigL10N.tid==self.tid, ConfigL10N.lang==lang_code, In(ConfigL10N.var_name, list(self.keys)))]

    def localized_dict(self, lang_code):
        rows = self.get_all(lang_code)
        return {c.var_name : c.value for c in rows if c.var_name in self.keys}

    def update(self, request, lang_code):
        c_map = {c.var_name : c for c in self.get_all(lang_code)}

        for key in self.modifiable_keys:
            c_map[key].set_v(request[key])

    def update_defaults(self, langs, l10n_data_src, reset=False):
        for lang_code in langs:
            old_keys = []

            for cfg in self.get_all(lang_code):
                old_keys.append(cfg.var_name)
                if (not cfg.customized or reset or cfg.var_name in self.unmodifiable_keys) and cfg.var_name in l10n_data_src:
                    cfg.value = l10n_data_src[cfg.var_name][lang_code]

            ConfigL10NFactory.initialize(self, lang_code, l10n_data_src, list(set(self.keys) - set(old_keys)))

    def get_val(self, var_name, lang_code):
        return models.db_get(self.store, ConfigL10N, tid=self.tid, lang=lang_code, var_name=var_name).value

    def set_val(self, var_name, lang_code, value):
        cfg = self.store.find(ConfigL10N, tid=self.tid, lang=lang_code, var_name=var_name).one()
        cfg.set_v(value)


class NodeL10NFactory(ConfigL10NFactory):
    keys = [
        u'description',
        u'presentation',
        u'footer',
        u'security_awareness_title',
        u'security_awareness_text',
        u'whistleblowing_question',
        u'whistleblowing_button',
        u'whistleblowing_receipt_prompt',
        u'custom_privacy_badge_tor',
        u'custom_privacy_badge_none',
        u'header_title_homepage',
        u'header_title_submissionpage',
        u'header_title_receiptpage',
        u'header_title_tippage',
        u'contexts_clarification',
        u'widget_comments_title',
        u'widget_messages_title',
        u'widget_files_title',
    ]

    modifiable_keys = keys


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
    ]

    # These strings are not exposed in admin the interface for customization
    unmodifiable_keys = [
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
        u'admin_anomaly_mail_template',
        u'admin_anomaly_mail_title',
        u'admin_anomaly_activities',
        u'admin_anomaly_disk_high',
        u'admin_anomaly_disk_low',
        u'admin_test_mail_template',
        u'admin_test_mail_title',
        u'https_certificate_expiration_mail_template',
        u'https_certificate_expiration_mail_title'
    ]

    modifiable_keys = [item for item in keys if item not in unmodifiable_keys]

    def __init__(self, store, tid, *args, **kwargs):
        ConfigL10NFactory.__init__(self, store, tid, *args, **kwargs)

    def reset_templates(self, l10n_data_src):
        langs = EnabledLanguage.list(self.store, self.tid)
        self.update_defaults(langs, l10n_data_src, reset=True)


def update_defaults(store, tid, appdata):
    langs = EnabledLanguage.list(store, tid)

    store.find(ConfigL10N,
               tid==tid,
               Not(In(ConfigL10N.var_name, NodeL10NFactory.keys + \
               NotificationL10NFactory.keys))).remove()

    NodeL10NFactory(store, tid).update_defaults(langs, appdata['node'])
    NotificationL10NFactory(store, tid).update_defaults(langs, appdata['templates'])
