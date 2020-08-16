# -*- coding: utf-8 -*-
# Implementation of the Tenant handlers
from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.models.config import ConfigFactory
from globaleaks.orm import transact


def serialize_site(session, tid):
    """
    Transaction serializing the tenant descriptor

    :param session: An ORM session
    :param tenant:  The tenant model
    :return: A serialization of the provided model
    """
    ret = ConfigFactory(session, tid).serialize('tenant')

    ret['id'] = tid

    if ret['mode'] != 'default':
        root_tenant = ConfigFactory(session, 1).serialize('tenant')
        if ret['subdomain'] and root_tenant.domain:
            ret['hostname'] = ret['subdomain'] + '.' + root_tenant.domain
        else:
            ret['hostname'] = ''


        if ret['subdomain'] and root_tenant.onionservice:
            ret['onionservice'] = ret['subdomain'] + '.' + root_tenant.onionservice
        else:
            ret['onionservice'] = ''

    return ret


@transact
def get_site_list(session):
    """
    Transaction return the list of the active tenants

    :param session: A ORM session
    :return: The list of active tenants
    """
    return [serialize_site(session, tid[0]) for tid in session.query(models.Config.tid).filter(models.Config.var_name == 'active', models.Config.value == True)]


class SiteCollection(BaseHandler):
    """
    Handler responsible of publishing the list of available tenants
    """
    check_roles = 'none'
    root_tenant_only = True

    def get(self):
        """
        Return the list of registered tenants
        """
        if 1 not in self.state.tenant_cache or not self.state.tenant_cache[1].multisite_login:
            return []

        return get_site_list()
