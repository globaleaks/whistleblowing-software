# -*- coding: utf-8 -*-
from sqlalchemy import not_

from globaleaks import __version__
from globaleaks.models import Config, ConfigL10N, EnabledLanguage
from globaleaks.models.properties import *
from globaleaks.models.config_desc import ConfigDescriptor, ConfigFilters, ConfigL10NFilters
from globaleaks.utils.utility import datetime_null


# List of variables that on creation are set with the value
# they have on the root tenant
inherit_from_root_tenant = [
  'default_questionnaire'
]

def get_default(default):
    if callable(default):
        return default()

    return default


class ConfigFactory(object):
    def __init__(self, session, tid):
        self.session = session
        self.tid = tid

    def get_all(self, group):
        return {c.var_name: c for c in self.session.query(Config).filter(Config.tid == self.tid, Config.var_name.in_(ConfigFilters[group]))}

    def update(self, group, data):
        configs = self.get_all(group)
        for k in configs:
            if k in data:
                configs[k].set_v(data[k])

    def get_cfg(self, var_name):
        return self.session.query(Config).filter(Config.tid == self.tid, Config.var_name == var_name).one()

    def get_val(self, var_name):
        return self.get_cfg(var_name).value

    def set_val(self, var_name, value):
        self.get_cfg(var_name).set_v(value)

    def serialize(self, group):
        configs = self.get_all(group)
        return {k: configs[k].value for k in configs}

    def update_defaults(self):
        actual = set([c[0] for c in self.session.query(Config.var_name).filter(Config.tid == self.tid)])
        allowed = set(ConfigDescriptor.keys())
        extra = list(actual - allowed)

        if extra:
            self.session.query(Config).filter(Config.tid == self.tid, Config.var_name.in_(extra)).delete(synchronize_session='fetch')

        missing = list(allowed - actual)
        for key in missing:
            self.session.add(Config({'tid': self.tid, 'var_name': key, 'value': get_default(ConfigDescriptor[key].default)}))


class ConfigL10NFactory(object):
    def __init__(self, session, tid):
        self.session = session
        self.tid = tid

    def initialize(self, keys, lang, data):
        for key in keys:
            value = data[key][lang] if key in data else ''
            self.session.add(ConfigL10N({'tid': self.tid, 'lang': lang, 'var_name': key, 'value': value}))

    def get_all(self, group, lang):
        return [r for r in self.session.query(ConfigL10N).filter(ConfigL10N.tid == self.tid, ConfigL10N.lang == lang, ConfigL10N.var_name.in_(list(ConfigL10NFilters[group])))]

    def serialize(self, group, lang):
        rows = self.get_all(group, lang)
        return {c.var_name : c.value for c in rows if c.var_name in ConfigL10NFilters[group]}

    def update(self, group, data, lang):
        c_map = {c.var_name : c for c in self.get_all(group, lang)}

        for key in (x for x in ConfigL10NFilters[group] if x in data):
            c_map[key].set_v(data[key])

    def update_defaults(self, group, langs, data, reset=False):
        null = datetime_null()

        for lang in langs:
            old_keys = []

            for cfg in self.get_all(group, lang):
                old_keys.append(cfg.var_name)
                if (cfg.update_date != null or reset) and cfg.var_name in data:
                    cfg.value = data[cfg.var_name][lang]

            ConfigL10NFactory.initialize(self, list(set(ConfigL10NFilters[group]) - set(old_keys)), lang, data)

    def get_val(self, var_name, lang):
        cfg = self.session.query(ConfigL10N.value).filter(ConfigL10N.tid == self.tid, ConfigL10N.lang == lang, ConfigL10N.var_name == var_name).one_or_none()
        if cfg is None:
            return ''

        return cfg.value

    def set_val(self, var_name, lang, value):
        cfg = self.session.query(ConfigL10N).filter(ConfigL10N.tid == self.tid, ConfigL10N.lang == lang, ConfigL10N.var_name == var_name).one()
        cfg.set_v(value)

    def reset(self, group, data):
        langs = EnabledLanguage.list(self.session, self.tid)
        self.update_defaults(group, langs, data, reset=True)


def db_get_config_variable(session, tid, var):
    return ConfigFactory(session, tid).get_val(var)


def db_set_config_variable(session, tid, var, val):
    ConfigFactory(session, tid).set_val(var, val)


def initialize_config(session, tid, mode):
    variables = {}

    # Initialization valid for any tenant
    for name, desc in ConfigDescriptor.items():
        variables[name] = get_default(desc.default)

    if tid != 1:
        # Initialization valid for secondary tenants
        variables['mode'] = mode

        root_tenant_node = ConfigFactory(session, 1).serialize('node')
        for name in inherit_from_root_tenant:
            variables[name] = root_tenant_node[name]

    for name, value in variables.items():
        session.add(Config({'tid': tid, 'var_name': name, 'value': value}))


def add_new_lang(session, tid, lang, appdata_dict):
    session.add(EnabledLanguage(tid, lang))

    ConfigL10NFactory(session, tid).initialize(ConfigL10NFilters['node'], lang, appdata_dict['node'])
    ConfigL10NFactory(session, tid).initialize(ConfigL10NFilters['notification'], lang, appdata_dict['templates'])


def update_defaults(session, tid, appdata):
    ConfigFactory(session, tid).update_defaults()

    langs = EnabledLanguage.list(session, tid)

    session.query(ConfigL10N).filter(ConfigL10N.tid == tid,
                                     not_(ConfigL10N.var_name.in_(list(set(ConfigL10NFilters['node']).union(ConfigL10NFilters['notification']))))).delete(synchronize_session='fetch')

    ConfigL10NFactory(session, tid).update_defaults('node', langs, appdata['node'])
    ConfigL10NFactory(session, tid).update_defaults('notification', langs, appdata['templates'])
