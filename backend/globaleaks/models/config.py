from globaleaks import __version__
from globaleaks.utils.utility import log
from storm.expr import And, Not
from storm.locals import Storm, Bool, Unicode, JSON

import config_desc
from .config_desc import GLConfig


class ConfigFactory(object):
    """
    This factory depends on the following attributes set by the sub class:
      update_set    -- keys updated when fact.update(d) is called
      group_desc    -- the corresponding dict in GLConfig
    """

    def __init__(self, group, store, lazy=True, *args, **kwargs):
        self.group = unicode(group)
        self.store = store
        self.res = None
        if not lazy:
            self._query_group()

    def _query_group(self):
        if not self.res is None:
            return
        cur = self.store.find(Config, And(Config.var_group == self.group))
        self.res = {c.var_name : c for c in cur}

    def update(self, request):
        self._query_group()
        keys = set(request.keys()) & self.update_set

        for key in keys:
            self.res[key].set_v(request[key])

    def get_cfg(self, var_name):
        if self.res is None:
            where = And(Config.var_group == self.group, Config.var_name == unicode(var_name))
            r = self.store.find(Config, where).one()
            if r is None:
                raise KeyError("No such config item: %s:%s" % (self.group, var_name))
            return r
        else:
            return self.res[var_name]

    def get_val(self, var_name):
        return self.get_cfg(var_name).get_v()

    def set_val(self, var_name, value):
        if self.res is None:
            self.get_cfg(var_name).set_v(value)
        elif not var_name in self.res:
            raise KeyError("Factory is not initialized with %s" % var_name)
        else:
            self.res[var_name].set_v(value)

    def _export_group_dict(self, safe_set):
        self._query_group()
        return {k : self.res[k].get_v() for k in safe_set}

    def db_corresponds(self):
        self.res = None
        try:
            self._query_group()
        except ValueError:
            return False

        k = set(self.res.keys())
        g = set(self.group_desc)

        if k != g:
            return False

        return True

    def clean_and_add(self):
        cur = self.store.find(Config, Config.var_group == self.group)
        res = {c.var_name : c for c in cur}

        actual = set(self.res.keys())
        allowed = set(self.group_desc)

        missing = allowed - actual

        for key in missing:
            desc = self.group_desc[key]
            c = Config(self.group, key, desc.default)
            log.info("Adding new config %s" % c)
            self.store.add(c)

        extra = actual - allowed

        for key in extra:
            c = res[key]
            log.info("Removing unused config: %s" % c)
            self.store.remove(c)

        return len(missing), len(extra)


class NodeFactory(ConfigFactory):
    node_private_fields = frozenset({
        'basic_auth',
        'basic_auth_username',
        'basic_auth_password',
        'default_password',
        'default_timezone',

        'can_postpone_expiration',
        'can_delete_submission',
        'can_grant_permissions',

        'ahmia',
        'allow_indexing',

        'threshold_free_disk_megabytes_high',
        'threshold_free_disk_megabytes_medium',
        'threshold_free_disk_megabytes_low',
        'threshold_free_disk_percentage_high',
        'threshold_free_disk_percentage_medium',
        'threshold_free_disk_percentage_low'
    })

    admin_node = frozenset(GLConfig['node'].keys())

    public_node = admin_node - node_private_fields

    update_set = admin_node
    group_desc = GLConfig['node']

    def __init__(self, store, *args, **kwargs):
        ConfigFactory.__init__(self, 'node', store, *args, **kwargs)

    def public_export(self):
        return self._export_group_dict(self.public_node)

    def admin_export(self):
        return self._export_group_dict(self.admin_node)


class NotificationFactory(ConfigFactory):
    admin_notification = frozenset(GLConfig['notification'].keys())

    update_set = admin_notification
    group_desc = GLConfig['notification']

    def __init__(self, store, *args, **kwargs):
        ConfigFactory.__init__(self, 'notification', store, *args, **kwargs)

    def admin_export(self):
        return self._export_group_dict(self.admin_notification)


class PrivateFactory(ConfigFactory):
    mem_export_set = frozenset(GLConfig['private'].keys())

    group_desc = GLConfig['private']

    def __init__(self, store, *args, **kwargs):
        ConfigFactory.__init__(self, 'private', store, *args, **kwargs)

    def mem_copy_export(self):
        return self._export_group_dict(self.mem_export_set)


factories = [NodeFactory, NotificationFactory, PrivateFactory]


class Config(Storm):
    __storm_table__ = 'config'
    __storm_primary__ = ('var_group', 'var_name')

    var_group = Unicode()
    var_name = Unicode()
    value = JSON()
    customized = Bool(default=False)

    def __init__(self, group, name, value):
        self.var_group = unicode(group)
        self.var_name = unicode(name)

        self.set_v(value)

    def set_v(self, val):
        self.find_descriptor()
        if val is None:
            val = self.desc._type()
        if isinstance(self.desc, config_desc.Unicode) and isinstance(val, str):
            val = unicode(val)
        if not isinstance(val, self.desc._type):
            raise ValueError("Cannot assign %s with %s" % (self, type(val)))
        if self.desc.validator is not None:
            self.desc.validator(self, self.var_name, val)

        if self.value is not None and self.value['v'] != val:
            self.customized = True

        self.value = {'v': val}

    def find_descriptor(self):
        d = GLConfig.get(self.var_group, {}).get(self.var_name, None)
        if d is None:
            raise ValueError('%s descriptor cannot be None' % self)
        self.desc = d

    def get_v(self):
        return self.value['v']

    def __repr__(self):
        return "<Config: %s.%s>" % (self.var_group, self.var_name)

def system_cfg_init(store):
    for gname, group in GLConfig.iteritems():
        for var_name, cfg_desc in group.iteritems():
            item = Config(gname, var_name, cfg_desc.default)
            store.add(item)

def del_cfg_not_in_groups(store):
    where = And(Not(Config.var_group == u'node'), Not(Config.var_group == u'notification'),
                Not(Config.var_group == u'private'))
    res = store.find(Config, where)
    for c in res:
        log.info("Removing extra Config <%s>" % c)
    store.find(Config, where).remove()

def is_cfg_valid(store):
    for fact_model in factories:
        if not fact_model(store).db_corresponds():
            return False

    s = {r.var_group for r in store.find(Config).group_by(Config.var_group)}
    if s != set(GLConfig.keys()):
        return False

    return True

def update_defaults(store):
    if not is_cfg_valid(store):
        log.info("This update will change system configuration")

        for fact_model in factories:
            factory = fact_model(store, lazy=False)
            factory.clean_and_add()

        del_cfg_not_in_groups(store)

    # Set the system version to the current aligned cfg
    prv = PrivateFactory(store)
    prv.set_val('version', __version__)
