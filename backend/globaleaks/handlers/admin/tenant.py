# -*- coding: UTF-8
#
#   tenant
#   *****
# Implementation of the Tenant handlers
#
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import Tenant
from globaleaks.orm import transact
from globaleaks.rest import requests


def serialize_tenant(store, tenant):
    return {
        'id': tenant.id,
        'label': tenant.label,
        'active': tenant.active
    }


def db_create(store, desc):
    tenant = Tenant(desc)

    store.add(tenant)

    # required to generate/retrive the id
    store.flush()

    return tenant


@transact
def create(store, desc, *args, **kwargs):
    return serialize_tenant(store, db_create(store, desc, *args, **kwargs))


def db_get_tenant_list(store):
    return [serialize_tenant(store, tenant) for tenant in store.find(Tenant)]


@transact
def get_tenant_list(store):
    return db_get_tenant_list(store)


@transact
def get(store, tid):
    return serialize_tenant(store, Tenant.get(store, id=tid))


@transact
def update(store, tid, request):
    tenant = Tenant.get(store, id=tid)
    Tenant.update(tenant, request)


class TenantCollection(BaseHandler):
    check_roles = 'admin'
    cache_resource = True
    invalidate_cache = True

    def get(self):
        """
        Return the list of registered tenants
        """
        return get_tenant_list()

    def post(self):
        """
        Create a new tenant
        """
        request = self.validate_message(self.request.content.read(), requests.AdminTenantDesc)

        return create(request)


class TenantInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def delete(self, tenant_id):
        """
        Delete the specified tenant.
        """
        return Tenant.delete(id=int(tenant_id))


    def put(self, tenant_id):
        """
        Update the specified tenant.
        """
        request = self.validate_message(self.request.content.read(),
                                        requests.AdminTenantDesc)

        return update(int(tenant_id), request)

    def get(self, tenant_id):
        return get(tid=int(tenant_id))
