# -*- coding: utf-8 -*-

from storm.expr import And
from storm.locals import Unicode, Storm

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.utils.utility import log


class EnabledLanguage(Storm):
    __storm_table__ = 'enabledlanguage'

    name = Unicode(primary=True)

    def __init__(self, name):
        self.name = unicode(name)

    def __repr__(self):
        return "<EnabledLang: %s>" % self.name

    @classmethod
    def add_new_lang(cls, store, lang_code, appdata):
        store.add(cls(lang_code))

        NotificationL10NFactory(store).create_default(lang_code, appdata)
        NodeL10NFactory(store).create_default(lang_code, appdata)

    @classmethod
    def remove_old_lang(cls, store, lang_code):
        obj = store.find(cls, cls.name == unicode(lang_code)).one()
        store.remove(obj)

    @classmethod
    def get_all_strs(cls, store):
        return [e.name for e in store.find(cls)]

    @classmethod
    def add_all_supported_langs(cls, store, appdata_dict):
        node_l10n = NodeL10NFactory(store)
        notif_l10n = NotificationL10NFactory(store)

        for lang_code in LANGUAGES_SUPPORTED_CODES:
            store.add(cls(lang_code))
            node_l10n.create_default(lang_code, appdata_dict)
            notif_l10n.create_default(lang_code, appdata_dict)


class ConfigL10N(Storm):
    __storm_table__ = 'config_l10n'
    __storm_primary__ = ('lang', 'var_group', 'var_name')

    lang = Unicode()
    var_group = Unicode()
    var_name = Unicode()
    value = Unicode()
    def_val = Unicode()

    def __init__(self, lang_code, group, var_name, value=''):
        self.lang = unicode(lang_code)
        self.var_group = unicode(group)
        self.var_name = unicode(var_name)
        self.value = unicode(value)
        self.def_val = unicode(value)

    def __repr__(self):
      return "<ConfigL10N %s::%s.%s::'%s'>" % (self.lang, self.var_group,
                                               self.var_name, self.value[:5])


class ConfigL10NFactory(object):
    def __init__(self, group, store, lang_code=None):
        self.store = store
        self.group = unicode(group)
        if lang_code is not None:
            self.lang_code = unicode(lang_code)
        #TODO use lazy loading to optimize query performance

    def create_default(self, lang_code, l10n_data_src):
        for key in self.localized_keys:
            if key in l10n_data_src and lang_code in l10n_data_src[key]:
                val = l10n_data_src[key][lang_code]
                entry = ConfigL10N(lang_code, self.group, key, val)
            else:
                entry = ConfigL10N(lang_code, self.group, key)
            self.store.add(entry)

    def retrieve_rows(self, lang_code):
        selector = And(ConfigL10N.var_group == self.group, ConfigL10N.lang == unicode(lang_code))
        return [r for r in self.store.find(ConfigL10N, selector)]

    def localized_dict(self, lang_code):
        rows = self.retrieve_rows(lang_code)
        loc_dict = {c.var_name : c.value for c in rows if c.var_name in self.localized_keys}
        return loc_dict

    def update(self, request, lang_code):
        c_map = {c.var_name : c for c in self.retrieve_rows(lang_code)}

        for key in self.localized_keys:
            c = c_map[key]
            c.value = unicode(request[key])

    def _where_is(self, lang_code, var_name):
        return And(ConfigL10N.lang == unicode(lang_code),
                   ConfigL10N.var_group == self.group,
                   ConfigL10N.var_name == unicode(var_name))

    def get_val(self, lang_code, var_name):
        cfg = self.store.find(ConfigL10N, self._where_is(lang_code, var_name)).one()
        if cfg is None:
            raise errors.ModelNotFound('ConfigL10N:%s.%s' % (self.group, var_name))
        return cfg.value

    def set_val(self, var_name, value):
        if self.lang_code is None:
            raise ValueError('Cannot assign ConfigL10N without a language')

        cfg = self.store.find(ConfigL10N, self._where_is(self.lang_code, var_name)).one()
        cfg.value = value


class NodeL10NFactory(ConfigL10NFactory):
    def __init__(self, store, *args, **kwargs):
        ConfigL10NFactory.__init__(self, 'node', store, *args, **kwargs)

    def create_default(self, lang_code, appdata_dict):
        l10n_data_src = appdata_dict['node']
        ConfigL10NFactory.create_default(self, lang_code, l10n_data_src)

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


class NotificationL10NFactory(ConfigL10NFactory):
    def __init__(self, store, *args, **kwargs):
        ConfigL10NFactory.__init__(self, 'notification', store, *args, **kwargs)

    def create_default(self, lang_code, appdata_dict):
        l10n_data_src = appdata_dict['templates']
        ConfigL10NFactory.create_default(self, lang_code, l10n_data_src)

    def reset_templates(self, appdata):
        l10n_data_src = appdata['templates']
        selector = And(ConfigL10N.var_group == self.group)
        for c in self.store.find(ConfigL10N, selector):
            new_value = ''
            if c.var_name in l10n_data_src:
                new_value = l10n_data_src[c.var_name][c.lang]
            c.value = unicode(new_value)

    localized_keys = frozenset({
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
        'export_message_recipient',
    })
