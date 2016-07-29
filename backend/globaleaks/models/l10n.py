# -*- coding: utf-8 -*-

from storm.expr import And 
from storm.locals import Unicode

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.utils.utility import log

from . import BaseModel, Node, Notification, Static_L10N


class EnabledLanguage(BaseModel):
    name = Unicode(primary=True)

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    @classmethod
    def add_new_lang(cls, store, lang_code, app_data):
        store.add(cls(lang_code))

        Notification_L10N(store).create_default(lang_code, app_data)
        Node_L10N(store).create_default(lang_code, app_data)

    @classmethod
    def remove_old_lang(cls, store, lang_code):
        obj = store.find(cls, cls.name == unicode(lang_code)).one()
        store.remove(obj)

    @classmethod
    def get_all(cls, store):
        return [str(e) for e in store.find(cls)]

    @classmethod
    def add_supported_langs(cls, store):
        for lang_code in LANGUAGES_SUPPORTED_CODES:
            store.add(cls(lang_code))


class Static_L10N_Map(object):

    def __init__(self, model, store):
        self.store = store
        self.model = model
        self.model_name = unicode(model.__storm_table__)

    def create_default(self, lang_code, l10n_data_src):
        for key in self.model.localized_keys:
            if key in l10n_data_src and lang_code in l10n_data_src[key]:
                val = l10n_data_src[key][lang_code]
                entry = Static_L10N(lang_code, self.model_name, key, val)
            else:
                entry = Static_L10N(lang_code, self.model_name, key)
            self.store.add(entry)

    def create_defaults(self, appdata_dict):
        for lang_code in EnabledLanguage.get_all(self.store):
            self.create_default(lang_code, appdata_dict)

    def retrieve_rows(self, lang):
        selector = And(Static_L10N.model == self.model_name, Static_L10N.lang == unicode(lang))
        return [r for r in self.store.find(Static_L10N, selector)]

    def fill_localized_values(self, external_obj, lang):
        rows = self.retrieve_rows(lang)
        loc_dict = {stat.var_name : stat.value for stat in rows} 
        
        for key in self.model.localized_keys:
            if key in loc_dict and key in loc_dict:
                external_obj[key] = loc_dict[key]
            else:
                log.debug('key missing: %s'% key)
        return external_obj

    def update_model(self, request, lang):
        stat_map = {stat.var_name : stat for stat in self.retrieve_rows(lang)}

        for key in self.model.localized_keys:
            stat_obj = stat_map[key]
            stat_obj.value = request[key]


class Node_L10N(Static_L10N_Map):

    def __init__(self, store):
        Static_L10N_Map.__init__(self, Node, store)

    def create_default(self, lang_code, appdata_dict):
        l10n_data_src = appdata_dict['node']
        Static_L10N_Map.create_default(self, lang_code, l10n_data_src)
        

class Notification_L10N(Static_L10N_Map):

    def __init__(self, store):
        Static_L10N_Map.__init__(self, Notification, store)

    def create_default(self, lang_code, appdata_dict):
        l10n_data_src = appdata_dict['templates']
        Static_L10N_Map.create_default(self, lang_code, l10n_data_src)

    def reset_templates(self):
        selector = And(Static_L10N.model == self.model_name)
        for stat_objs in self.store.find(Static_L10N, selector):
            stat_objs.value = stat_objs.def_val
