# -*- coding: utf-8 -*-
from storm.locals import Unicode, Bool

from globaleaks import LANGUAGES_SUPPORTED_CODES, models

XTIDX = 1

class EnabledLanguage(models.ModelWithTID):
    __storm_table__ = 'enabledlanguage'
    __storm_primary__ = ('tid', 'name')

    name = Unicode()

    def __init__(self, tid=XTIDX, name=None, migrate=False):
        if migrate:
            return

        self.tid = tid
        self.name = unicode(name)

    @classmethod
    def list(cls, store, tid=XTIDX):
        return [name for name in store.find(EnabledLanguage.name, EnabledLanguage.tid==tid)]

    @classmethod
    def add_new_lang(cls, store, tid, lang_code, appdata_dict):
        store.add(cls(tid, lang_code))

        NotificationL10NFactory(store, tid).initialize(lang_code, appdata_dict)
        NodeL10NFactory(store, tid).initialize(lang_code, appdata_dict)

    @classmethod
    def add_all_supported_langs(cls, store, tid, appdata_dict):
        for lang_code in LANGUAGES_SUPPORTED_CODES:
            cls.add_new_lang(store, tid, lang_code, appdata_dict)


class ConfigL10N(models.ModelWithTID):
    __storm_table__ = 'config_l10n'
    __storm_primary__ = ('lang', 'var_group', 'var_name')

    lang = Unicode()
    var_group = Unicode()
    var_name = Unicode()
    value = Unicode()
    customized = Bool(default=False)

    def __init__(self, tid=XTIDX, lang_code=None, group=None, var_name=None, value='', migrate=False):
        if migrate:
            return

        self.tid = tid
        self.lang = unicode(lang_code)
        self.var_group = unicode(group)
        self.var_name = unicode(var_name)
        self.value = unicode(value)

    def set_v(self, value):
        value = unicode(value)
        if self.value != value:
            self.value = value
            self.customized = True


class ConfigL10NFactory(object):
    localized_keys = frozenset()
    unmodifiable_keys = frozenset()

    def __init__(self, store, tid, group):
        self.store = store
        self.tid = tid
        self.group = unicode(group)

    def initialize(self, lang_code, l10n_data_src, keys=None):
        if keys is None:
            keys = self.localized_keys

        for key in keys:
            value = l10n_data_src[key][lang_code] if key in l10n_data_src else ''
            self.store.add(ConfigL10N(self.tid, lang_code, self.group, key, value))

    def retrieve_rows(self, lang_code):
        return [r for r in self.store.find(ConfigL10N, tid=self.tid, lang=lang_code, var_group=self.group)]

    def localized_dict(self, lang_code):
        rows = self.retrieve_rows(lang_code)
        return {c.var_name : c.value for c in rows if c.var_name in self.localized_keys}

    def update(self, request, lang_code):
        c_map = {c.var_name : c for c in self.retrieve_rows(lang_code)}

        for key in self.localized_keys - self.unmodifiable_keys:
            c_map[key].set_v(request[key])

    def update_defaults(self, langs, l10n_data_src, reset=False):
        for lang_code in langs:
            old_keys = []

            for cfg in self.get_all(lang_code):
                old_keys.append(cfg.var_name)
                if cfg.var_name in self.localized_keys:
                    if (not cfg.customized or reset or cfg.var_name in self.unmodifiable_keys) and cfg.var_name in l10n_data_src:
                        cfg.value = l10n_data_src[cfg.var_name][lang_code]
                else:
                    self.store.remove(cfg)

            ConfigL10NFactory.initialize(self, lang_code, l10n_data_src, list(set(self.localized_keys) - set(old_keys)))

    def get_all(self, lang_code):
        return self.store.find(ConfigL10N, lang=lang_code, var_group=self.group)

    def get_val(self, var_name, lang_code):
        return models.db_get(self.store, ConfigL10N, lang=lang_code, var_group=self.group, var_name=var_name).value

    def set_val(self, var_name, lang_code, value):
        cfg = self.store.find(ConfigL10N, lang=lang_code, var_group=self.group, var_name=var_name).one()
        cfg.set_v(value)


class NodeL10NFactory(ConfigL10NFactory):
    localized_keys = frozenset({
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
        'widget_files_title',
    })

    def __init__(self, store, tid=XTIDX, *args, **kwargs):
        ConfigL10NFactory.__init__(self, store, tid, u'node', *args, **kwargs)

    def initialize(self, lang_code, appdata_dict, keys=None):
        ConfigL10NFactory.initialize(self, lang_code, appdata_dict['node'], keys)


class NotificationL10NFactory(ConfigL10NFactory):
    localized_keys = frozenset({
        'admin_anomaly_mail_template',
        'admin_anomaly_mail_title',
        'admin_anomaly_disk_low',
        'admin_anomaly_disk_high',
        'admin_anomaly_activities',
        'admin_pgp_alert_mail_template',
        'admin_pgp_alert_mail_title',
        'admin_test_mail_template',
        'admin_test_mail_title',
        'pgp_alert_mail_template',
        'pgp_alert_mail_title',
        'tip_mail_template',
        'tip_mail_title',
        'file_mail_template',
        'file_mail_title',
        'comment_mail_template',
        'comment_mail_title',
        'message_mail_template',
        'message_mail_title',
        'tip_expiration_summary_mail_template',
        'tip_expiration_summary_mail_title',
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
        'export_message_recipient',
        'https_certificate_expiration_mail_template',
        'https_certificate_expiration_mail_title',
        'software_update_available_mail_template',
        'software_update_available_mail_title',
    })

    # These strings are not exposed in admin the interface for customization
    unmodifiable_keys = frozenset({
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
        'export_message_recipient',
        'admin_anomaly_mail_template',
        'admin_anomaly_mail_title',
        'admin_anomaly_activities',
        'admin_anomaly_disk_high',
        'admin_anomaly_disk_low',
        'admin_test_mail_template',
        'admin_test_mail_title',
        'https_certificate_expiration_mail_template',
        'https_certificate_expiration_mail_title'
    })

    # These strings are modifiable via the admin/notification handler
    modifiable_keys = localized_keys - unmodifiable_keys

    def __init__(self, store, tid=XTIDX, *args, **kwargs):
        ConfigL10NFactory.__init__(self, store, tid, u'notification', *args, **kwargs)

    def initialize(self, lang_code, appdata_dict, keys=None):
        ConfigL10NFactory.initialize(self, lang_code, appdata_dict['templates'], keys)

    def reset_templates(self, l10n_data_src):
        langs = EnabledLanguage.list(self.store, XTIDX)
        self.update_defaults(langs, l10n_data_src, reset=True)


def update_defaults(store, appdata):
    langs = EnabledLanguage.list(store, XTIDX)
    NodeL10NFactory(store).update_defaults(langs, appdata['node'])
    NotificationL10NFactory(store).update_defaults(langs, appdata['templates'])
