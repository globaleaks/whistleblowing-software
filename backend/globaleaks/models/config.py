# -*- coding: utf-8 -*-
from sqlalchemy import Column, not_

from globaleaks import __version__
from globaleaks.models import config_desc, Base, Model, Tenant
from globaleaks.models.properties import *
from globaleaks.models.config_desc import ConfigDescriptor, ConfigFilters


class Config(Model, Base):
    __tablename__ = 'config'
    tid = Column(Integer, ForeignKey('tenant.id', ondelete='CASCADE'), primary_key=True, default=1, nullable=False)
    var_name = Column(Unicode(64), primary_key=True, nullable=False)

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

        if self.value is not None:
            self.customized = True

        self.value = val

    def get_v(self):
        return self.value


class ConfigFactory(object):
    """
    This factory depends on the following attributes set by the sub class:
    """
    def __init__(self, session, tid, group, *args, **kwargs):
        self.session = session
        self.tid = tid
        self.group = unicode(group)
        self.res = None
        self.keys = ConfigFilters[group]

    def _query_group(self):
        self.res = {c.var_name: c for c in self.session.query(Config).filter(Config.tid == self.tid, Config.var_name.in_(ConfigFilters[self.group]))}

    def update(self, request):
        self._query_group()

        for key in (key for key in request.keys() if key in self.res):
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

    def serialize(self):
        self._query_group()
        return {k: self.res[k].get_v() for k in self.res}

    def clean_and_add(self):
        actual = set([c[0] for c in self.session.query(Config.var_name).filter(Config.tid == self.tid)])
        allowed = set(ConfigDescriptor.keys())
        extra = list(actual - allowed)

        if extra:
            self.session.query(Config).filter(Config.tid == self.tid, Config.var_name.in_(extra)).delete(synchronize_session='fetch')

        missing = list(allowed - actual)
        for key in missing:
            self.session.add(Config(self.tid, key, ConfigDescriptor[key].default))

        return len(missing), len(extra)


def system_cfg_init(session, tid):
    for var_name, desc in ConfigDescriptor.items():
        if callable(desc.default):
            default = desc.default()
        else:
            default = desc.default

        session.add(Config(tid, var_name, default))


def update_defaults(session, tid):
    session.query(Config).filter(Config.tid == tid, not_(Config.var_name.in_(ConfigDescriptor.keys()))).delete(synchronize_session='fetch')

    ConfigFactory(session, tid, 'node').clean_and_add()
    ConfigFactory(session, tid, 'notification').clean_and_add()

    # Set the system version to the current aligned cfg
    ConfigFactory(session, tid, 'node').set_val(u'version', __version__)
