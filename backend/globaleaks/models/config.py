from storm.expr import Not, In
from storm.locals import Bool, Unicode, JSON

from globaleaks import __version__
from globaleaks.models import config_desc, ModelWithTID, Tenant
from globaleaks.models.config_desc import ConfigDescriptor, ConfigFilters
from globaleaks.utils.utility import log


class Config(ModelWithTID):
    __storm_table__ = 'config'
    __storm_primary__ = ('tid', 'var_name')

    cfg_desc = ConfigDescriptor
    var_name = Unicode()
    value = JSON()
    customized = Bool(default=False)


    def __init__(self, tid=1, name=None, value=None, cfg_desc=None, migrate=False):
        """
        :param value:    This input is passed directly into set_v
        :param migrate:  Added to comply with models.Model constructor which is
                         used to copy every field returned by storm from the db
                         from an old_obj to a new one.
        :param cfg_desc: Used to specify where to look for the Config objs descripitor.
                         This is used in mig 34.
        """
        if cfg_desc is not None:
            self.cfg_desc = cfg_desc

        if migrate:
            return

        self.tid = tid
        self.var_name = unicode(name)
        self.set_v(value)

    def set_v(self, val):
        desc = ConfigDescriptor[self.var_name]
        if val is None:
            val = desc._type()

        if isinstance(desc, config_desc.Unicode) and isinstance(val, str):
            val = unicode(val)

        if not isinstance(val, desc._type):
            raise ValueError("Cannot assign %s with %s" % (self, type(val)))

        if desc.validator is not None:
            desc.validator(self, self.var_name, val)

        if self.value is None:
            self.value = {'v': val}

        elif self.value['v'] != val:
            self.customized = True
            self.value = {'v': val}

    def get_v(self):
        return self.value['v']


class ConfigFactory(object):
    """
    This factory depends on the following attributes set by the sub class:
    """
    update_set = frozenset() # keys updated when fact.update(d) is called
    group_desc = dict() # the corresponding dict in ConfigDescriptor

    def __init__(self, store, tid, group, *args, **kwargs):
        self.store = store
        self.tid = tid
        self.group = unicode(group)
        self.res = None

    def _query_group(self):
        self.res = {c.var_name: c for c in self.store.find(Config, Config.tid==self.tid, In(Config.var_name, ConfigFilters[self.group]))}

    def update(self, request):
        self._query_group()
        keys = set(request.keys()) & self.update_set

        for key in keys:
            self.res[key].set_v(request[key])

    def get_cfg(self, var_name):
        return self.store.find(Config, tid=self.tid, var_name=var_name).one()

    def get_val(self, var_name):
        return self.get_cfg(var_name).get_v()

    def set_val(self, var_name, value):
        if self.res is not None and var_name in self.res:
            self.res[var_name].set_v(value)
        else:
            self.get_cfg(var_name).set_v(value)

    def _export_group_dict(self, safe_set):
        self._query_group()
        return {k: self.res[k].get_v() for k in safe_set}

    def db_corresponds(self):
        self._query_group()

        k = set(self.res.keys())
        g = ConfigFilters[self.group]

        return k == g

    def clean_and_add(self):
        self._query_group()

        actual = [name for name in self.store.find(Config.var_name, Config.tid==self.tid)]

        allowed = ConfigDescriptor.keys()

        missing = list(set(allowed) - set(actual))

        for key in missing:
            self.store.add(Config(self.tid, key, ConfigDescriptor[key].default))

        extra = list(set(actual) - set(allowed))

        self.store.find(Config, In(Config.var_name, extra)).remove()

        return len(missing), len(extra)


class NodeFactory(ConfigFactory):
    node_private_fields = frozenset({
        'basic_auth',
        'basic_auth_username',
        'basic_auth_password',
        'default_password',
        'default_timezone',

        'threshold_free_disk_megabytes_high',
        'threshold_free_disk_megabytes_low',
        'threshold_free_disk_percentage_high',
        'threshold_free_disk_percentage_low',

        'anonymize_outgoing_connections',
    })

    admin_node = frozenset(ConfigFilters['node'])

    public_node = admin_node - node_private_fields

    update_set = admin_node
    group_desc = ConfigDescriptor

    def __init__(self, store, tid, *args, **kwargs):
        ConfigFactory.__init__(self, store, tid, 'node', *args, **kwargs)

    def public_export(self):
        return self._export_group_dict(self.public_node)

    def admin_export(self):
        return self._export_group_dict(self.admin_node)


class NotificationFactory(ConfigFactory):
    admin_notification = frozenset(ConfigFilters['notification'])

    update_set = admin_notification
    group_desc = ConfigDescriptor

    def __init__(self, store, tid, *args, **kwargs):
        ConfigFactory.__init__(self, store, tid, 'notification', *args, **kwargs)

    def admin_export(self):
        return self._export_group_dict(self.admin_notification)


class PrivateFactory(ConfigFactory):
    non_mem_vars = {
        'acme_accnt_key',
        'tor_onion_key',
        'https_priv_key',
        'https_priv_gen',
        'https_chain',
        'https_dh_params',
    }

    mem_export_set = frozenset(set(ConfigFilters['private']) - non_mem_vars)

    group_desc = ConfigDescriptor

    def __init__(self, store, tid, *args, **kwargs):
        ConfigFactory.__init__(self, store, tid, 'private', *args, **kwargs)

    def mem_copy_export(self):
        return self._export_group_dict(self.mem_export_set)


factories = [NodeFactory, NotificationFactory, PrivateFactory]


def system_cfg_init(store, tid):
    for var_name, desc in ConfigDescriptor.items():
        if desc.default_factory is not None:
            default = desc.default_factory()
        else:
            default = desc.default

        store.add(Config(tid, var_name, default))


def update_defaults(store, tid):
    store.find(Config, Not(In(Config.var_name, ConfigDescriptor.keys()))).remove()

    for fact_model in factories:
         fact_model(store, tid).clean_and_add()

    # Set the system version to the current aligned cfg
    PrivateFactory(store, tid).set_val(u'version', __version__)


def load_tls_dict(store, tid):
    """
    A quick and dirty function to grab all of the tls config for use in subprocesses
    """
    priv = PrivateFactory(store, tid)
    node = NodeFactory(store, tid)

    return {
        'ssl_key': priv.get_val(u'https_priv_key'),
        'ssl_cert': priv.get_val(u'https_cert'),
        'ssl_intermediate': priv.get_val(u'https_chain'),
        'ssl_dh': priv.get_val(u'https_dh_params'),
        'https_enabled': priv.get_val(u'https_enabled'),
        'hostname': node.get_val(u'hostname'),
    }


def load_tls_dict_list(store):
    return [load_tls_dict(store, tid) for tid in store.find(Tenant.id)]
