# -*- coding: utf-8 -*-

from storm.expr import And
from storm.locals import Unicode

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.utils.utility import log

from . import BaseModel, Node, Notification, ConfigL10N


class EnabledLanguage(BaseModel):
    name = Unicode(primary=True)

    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return "<EnabledLang: %s>" % self.name

    @classmethod
    def add_new_lang(cls, store, lang_code, appdata):
        store.add(cls(lang_code))

        Notification_L10N(store).create_default(lang_code, appdata)
        Node_L10N(store).create_default(lang_code, appdata)

    @classmethod
    def remove_old_lang(cls, store, lang_code):
        obj = store.find(cls, cls.name == unicode(lang_code)).one()
        store.remove(obj)

    @classmethod
    def get_all(cls, store):
        return [e for e in store.find(cls)]

    @classmethod
    def add_all_supported_langs(cls, store, appdata_dict):
        node_l10n = Node_L10N(store)
        notif_l10n = Notification_L10N(store)

        for lang_code in LANGUAGES_SUPPORTED_CODES:
            store.add(cls(lang_code))
            node_l10n.create_default(lang_code, appdata_dict)
            notif_l10n.create_default(lang_code, appdata_dict)



class ConfigL10N_Map(object):

    def __init__(self, model, store):
        self.store = store
        self.model = model
        self.group_name = unicode(model.__storm_table__)

    def create_default(self, lang_code, l10n_data_src):
        for key in self.model.localized_keys:
            if key in l10n_data_src and lang_code in l10n_data_src[key]:
                val = l10n_data_src[key][lang_code]
                entry = ConfigL10N(lang_code, self.group_name, key, val)
            else:
                entry = ConfigL10N(lang_code, self.group_name, key)
            self.store.add(entry)

    def retrieve_rows(self, lang):
        selector = And(ConfigL10N.var_group == self.group_name, ConfigL10N.lang == unicode(lang))
        return [r for r in self.store.find(ConfigL10N, selector)]

    def fill_localized_values(self, external_obj, lang):
        rows = self.retrieve_rows(lang)
        loc_dict = {c.var_name : c.value for c in rows}

        for key in self.model.localized_keys:
            if key in loc_dict:
                external_obj[key] = loc_dict[key]
        return external_obj

    def update_model(self, request, lang):
        c_map = {c.var_name : c for c in self.retrieve_rows(lang)}

        for key in self.model.localized_keys:
            c = c_map[key]
            c.value = unicode(request[key])


class Node_L10N(ConfigL10N_Map):

    def __init__(self, store):
        ConfigL10N_Map.__init__(self, Node, store)

    def create_default(self, lang_code, appdata_dict):
        l10n_data_src = appdata_dict['node']
        ConfigL10N_Map.create_default(self, lang_code, l10n_data_src)


class Notification_L10N(ConfigL10N_Map):

    def __init__(self, store):
        ConfigL10N_Map.__init__(self, Notification, store)

    def create_default(self, lang_code, appdata_dict):
        l10n_data_src = appdata_dict['templates']
        ConfigL10N_Map.create_default(self, lang_code, l10n_data_src)

    def reset_templates(self, appdata):
        l10n_data_src = appdata['templates']
        selector = And(ConfigL10N.var_group == self.group_name)
        for cfg_item in self.store.find(ConfigL10N, selector):
            new_value = u''
            if cfg_item.var_name in l10n_data_src:
                new_value = unicode(l10n_data_src[cfg_item.lang])
            cfg_item.value = new_value
