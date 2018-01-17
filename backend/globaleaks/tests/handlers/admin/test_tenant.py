# -*- coding: utf-8 -*-"""
from twisted.internet.defer import inlineCallbacks

from globaleaks.db import refresh_memory_variables
from globaleaks.models import config
from globaleaks.handlers.admin import tenant
from globaleaks.state import State
from globaleaks.orm import transact

from globaleaks.tests import helpers

def get_dummy_tenant_desc():
    return {
        'label': 'tenant-xxx',
        'active': True,
        'subdomain': 'www.news',
    }


class TenantTestEnv(helpers.TestHandlerWithPopulatedDB):
    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        State.onion_service_job = False


@transact
def get_salt(session, tid):
    return config.PrivateFactory(session, tid).get_val(u'receipt_salt')

class TestTenantCollection(TenantTestEnv):
    _handler = tenant.TenantCollection

    @inlineCallbacks
    def test_get(self):
        n = 3

        for i in range(n):
            yield tenant.create(get_dummy_tenant_desc())

        handler = self.request(role='admin')
        response = yield handler.get()

        self.assertEqual(len(response), self.population_of_tenants + n)

    @inlineCallbacks
    def test_post(self):
        first = yield get_salt(1)

        handler = self.request(get_dummy_tenant_desc(), role='admin')
        r = yield handler.post()

        second = yield get_salt(r['id'])

        handler = self.request(get_dummy_tenant_desc(), role='admin')
        r = yield handler.post()

        third = yield get_salt(r['id'])

        # Checks that the salt is actually modified from create to another
        self.assertNotEqual(first, second)
        self.assertNotEqual(second, third)


class TestTenantInstance(TenantTestEnv):
    _handler = tenant.TenantInstance

    @inlineCallbacks
    def setUp(self):
        yield TenantTestEnv.setUp(self)
        t = yield tenant.create(get_dummy_tenant_desc())
        self.handler = self.request(t, role='admin')
        yield refresh_memory_variables([4])

    def test_get(self):
        return self.handler.get(4)

    def test_put(self):
        return self.handler.put(4)

    def test_delete(self):
        return self.handler.delete(4)
