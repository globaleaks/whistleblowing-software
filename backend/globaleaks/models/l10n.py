# -*- coding: utf-8 -*-

from storm.expr import And 
from storm.locals import Unicode

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.utils.utility import log

from . import BaseModel, Node, Notification, Static_L10N


def app_supported_langs():
    return iter(LANGUAGES_SUPPORTED_CODES)


class EnabledLanguage(BaseModel):
    name = Unicode(primary=True)

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return self.name

    @classmethod
    def get_all(cls, store):
        return [str(e) for e in store.find(cls)]

    @classmethod
    def create_defaults(cls, store):
        store.add(cls("en"))
        store.add(cls("it"))

class Static_L10N_Map(object):

    def __init__(self, model, store):
        self.store = store
        self.model = model
        self.model_name = unicode(model.__storm_table__)

    def create_defaults(self, app_data):
        for key in self.model.localized_keys:
            for lang in EnabledLanguage.get_all(self.store):
                if key in app_data:
                    lang_dict = app_data[key]
                    val = lang_dict[lang]
                    entry = Static_L10N(self.model_name, lang, key, val)
                else:
                    entry = Static_L10N(self.model_name, lang, key)
                self.store.add(entry)
                
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

class Notification_L10N(Static_L10N_Map):

    def __init__(self, store):
        Static_L10N_Map.__init__(self, Notification, store)

    def reset_templates(self):
        selector = And(Static_L10N.model == self.model_name)
        for stat_objs in self.store.find(Static_L10N, selector):
            stat_objs.value = stat_objs.def_val
