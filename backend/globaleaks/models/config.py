import json
import os

from storm.locals import Storm, Unicode, Pickle, And

from .groups import GLConfig


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

    def fill_object_dict(self):
        cur = self.store.find(Config, And(Config.var_group == self.group))
        rows = [_ for _ in cur]
        # TODO Assert set equality of rows.var_name and self.group keys
        self.ro = ObjectDict({c.var_name : c.raw_value for c in rows})
        self.w = ObjectDict({c.var_name : c for c in rows})

    def update(self, request):
        # TODO decide if we can trust request sufficiently to use request.keys()
        keys = set(request.keys()) & set(self.w.keys())
        for key in keys:
            # TODO must remove unsettable keys
            getattr(self.w, key).raw_value = request[key]

    def get(self, var_name):
        where = And(Config.var_group == self.group, Config.var_name == unicode(var_name))
        r = self.store.find(Config, where).one()
        if r is None:
            raise ValueError("No such config item: %s:%s" % (self.group, var_name))
        return r


class Config(Storm):
    __storm_table__ = 'config'
    __storm_primary__ = ('var_group', 'var_name')

    type_map = {'str': unicode, 'int': int, 'bool': bool}

    var_group = Unicode()
    var_name = Unicode()
    var_type = Unicode()
    raw_value = Pickle() # TODO use struct pack

    def __init__(self, group, name, var_type, value):
        self.var_group = unicode(group)
        if not var_type in self.type_map:
            raise TypeError('Passed var_type is not in Config type map')
        if var_type == 'str':
            value = unicode(value)
        if not isinstance(value, self.type_map[var_type]):
            raise ValueError('raw_value has the wrong type!')
        else:
            self.raw_value = value
        self.var_name = unicode(name)
        self.var_type = unicode(var_type)


def get_config_group(store, var_group):
    # TODO no check that returned keys are approved.
    grp = store.find(Config, Config.var_group == unicode(var_group))
    return {x.var_name : x.raw_value for x in grp} 
    

def validate_input(raw_json):
    if not isinstance(raw_json, dict):
        raise ValueError
    #if len(raw_json) != 2:
    #    raise ValueError
    for k, val in raw_json.iteritems():
        if not isinstance(val, list): raise ValueError
        for item in val:
          if len(item.keys()) != 3: raise ValueError
    return raw_json


def load_json_config(store):
    for gname, group in GLConfig.iteritems():
        for var_name, item_def in group.iteritems():
            item = Config(gname, var_name, item_def.typ, item_def.val)
            store.add(item)
