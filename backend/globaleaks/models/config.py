import json
import os
from datetime import datetime

from storm.locals import Storm, Unicode, And, JSON

from .groups import GLConfig, SafeSets
from .properties import iso_strf_time


class ObjectDict(dict):
    """Makes a dictionary behave like an object."""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)

    def __setattr__(self, name, value):
        self[name] = value


class ConfigFactory(object):
    def __init__(self, group, store):
        self.group = unicode(group)
        self.store = store
        self.res = None

    def _query_group(self):
        if not self.res is None:
            return
        cur = self.store.find(Config, And(Config.var_group == self.group))
        self.res = {c.var_name : c for c in cur}

    def update(self, request):
        self._query_group()
        keys = set(request.keys()) & self._update_set

        for key in keys:
            self.res[key].set_val(request[key])

    def get(self, var_name):
        if self.res is None:
            where = And(Config.var_group == self.group, Config.var_name == unicode(var_name))
            r = self.store.find(Config, where).one()
            if r is None:
                raise ValueError("No such config item: %s:%s" % (self.group, var_name))
            return r
        else:
            return self.res[var_name]

    def get_val(self, var_name):
        return self.get(var_name).get_val()

    def set_val(self, var_name, value):
        if self.res is None or not var_name in self.res:
            raise KeyError("Factory is not initialized with %s" %s)
        else:
            self.res[var_name].set_val(value)

    def _export_group_dict(self, safe_set):
        self._query_group()
        return {k : self.res[k].get_val() for k in safe_set}


class NodeFactory(ConfigFactory):
    _update_set = SafeSets.admin_node

    def __init__(self, store):
        ConfigFactory.__init__(self, 'node', store)

    def public_export(self):
        return self._export_group_dict(SafeSets.public_node)

    def admin_export(self):
        return self._export_group_dict(SafeSets.admin_node)


class NotificationFactory(ConfigFactory):
    _update_set = SafeSets.admin_notification

    def __init__(self, store):
        ConfigFactory.__init__(self, 'notification', store)

    def admin_export(self):
        return self._export_group_dict(SafeSets.admin_notification)


class PrivateFactory(ConfigFactory):
    def __init__(self, store):
        ConfigFactory.__init__(self, 'private', store)

    def mem_copy_export(self):
        keys = frozenset(GLConfig['private'].keys())
        return self._export_group_dict(keys)

class Config(Storm):
    __storm_table__ = 'config'
    __storm_primary__ = ('var_group', 'var_name')

    var_group = Unicode()
    var_name = Unicode()
    value = JSON()

    def _get_v(self):
        return self.value.get('v')

    def set_val(self, val):
        self.find_descriptor()
        if self.desc.validator is not None:
            val = self.desc.validator(self, self.var_name, val)
        if self.desc.__class__.__name__ == 'DateTime' and isinstance(val, datetime):
            val = iso_strf_time(val)
        self.value = {'v': val}

    def find_descriptor(self):
        d = GLConfig.get(self.var_group, {}).get(self.var_name, None)
        if d is None:
            raise ValueError('Descriptor cannot be None')
        self.desc = d

    def get_val(self):
        return self.value['v']

    def __init__(self, group, name, value):
        self.var_group = unicode(group)
        self.var_name = unicode(name)
        self.set_val(value)

    def __repr__(self):
        return "<Config: %s.%s>" % (self.var_group, self.var_name)


def initialize_config(store):
    for gname, group in GLConfig.iteritems():
        for var_name, item_def in group.iteritems():
            item = Config(gname, var_name, item_def.val)
            store.add(item)
