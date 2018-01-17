# -*- coding: utf-8 -*-
from sqlalchemy import Column, not_

from globaleaks import __version__
from globaleaks.models import config_desc, Base, Model, Tenant
from globaleaks.models.properties import *
from globaleaks.models.config_desc import ConfigDescriptor, ConfigFilters


class Config(Model, Base):
    __tablename__ = 'config'
    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), primary_key=True, default=1, nullable=False)
    var_name = Column(String(64), primary_key=True, nullable=False)

    value = Column(JSON, nullable=False)
    customized = Column(Boolean, default=False, nullable=False)

    cfg_desc = ConfigDescriptor

    def __init__(self, tid=1, name=None, value=None, cfg_desc=None, migrate=False):
        """
        :param value:    This input is passed directly into set_v
        :param migrate:  Added to comply with models.Model constructor which is
                         used to copy every field returned by the ORM from the db
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

    def __init__(self, session, tid, group, *args, **kwargs):
        self.session = session
        self.tid = tid
        self.group = unicode(group)
        self.res = None

    def _query_group(self):
        self.res = {c.var_name: c for c in self.session.query(Config).filter(Config.tid == self.tid, Config.var_name.in_(ConfigFilters[self.group]))}

    def update(self, request):
        self._query_group()
        keys = set(request.keys()) & self.update_set

        for key in keys:
            self.res[key].set_v(request[key])

    def get_cfg(self, var_name):
        return self.session.query(Config).filter(Config.tid == self.tid, Config.var_name == var_name).one()

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

    def clean_and_add(self):
        actual = [c[0] for c in self.session.query(Config.var_name).filter(Config.tid == self.tid)]

        allowed = ConfigDescriptor.keys()

        extra = list(set(actual) - set(allowed))

        if extra:
            self.session.query(Config).filter(Config.tid == self.tid, Config.var_name.in_(extra)).delete(synchronize_session='fetch')

        missing = list(set(allowed) - set(actual))
        for key in missing:
            self.session.add(Config(self.tid, key, ConfigDescriptor[key].default))

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

    def __init__(self, session, tid, *args, **kwargs):
        ConfigFactory.__init__(self, session, tid, 'node', *args, **kwargs)

    def public_export(self):
        return self._export_group_dict(self.public_node)

    def admin_export(self):
        return self._export_group_dict(self.admin_node)


class NotificationFactory(ConfigFactory):
    admin_notification = frozenset(ConfigFilters['notification'])

    update_set = admin_notification
    group_desc = ConfigDescriptor

    def __init__(self, session, tid, *args, **kwargs):
        ConfigFactory.__init__(self, session, tid, 'notification', *args, **kwargs)

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

    def __init__(self, session, tid, *args, **kwargs):
        ConfigFactory.__init__(self, session, tid, 'private', *args, **kwargs)


factories = [NodeFactory, NotificationFactory, PrivateFactory]


def system_cfg_init(session, tid):
    for var_name, desc in ConfigDescriptor.items():
        if callable(desc.default):
            default = desc.default()
        else:
            default = desc.default

        session.add(Config(tid, var_name, default))


def update_defaults(session, tid):
    session.query(Config).filter(Config.tid == tid, not_(Config.var_name.in_(ConfigDescriptor.keys()))).delete(synchronize_session='fetch')

    for fact_model in factories:
         fact_model(session, tid).clean_and_add()

    # Set the system version to the current aligned cfg
    PrivateFactory(session, tid).set_val(u'version', __version__)


def load_tls_dict(session, tid):
    """
    A quick and dirty function to grab all of the tls config for use in subprocesses
    """
    priv = PrivateFactory(session, tid)
    node = NodeFactory(session, tid)

    return {
        'ssl_key': priv.get_val(u'https_priv_key'),
        'ssl_cert': priv.get_val(u'https_cert'),
        'ssl_intermediate': priv.get_val(u'https_chain'),
        'ssl_dh': priv.get_val(u'https_dh_params'),
        'https_enabled': priv.get_val(u'https_enabled'),
        'hostname': node.get_val(u'hostname'),
    }


def load_tls_dict_list(session):
    return [load_tls_dict(session, tid[0]) for tid in session.query(Tenant.id)]
