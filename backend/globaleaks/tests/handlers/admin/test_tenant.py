# -*- coding: utf-8 -*-"""
from twisted.internet.defer import inlineCallbacks

from globaleaks.db import refresh_memory_variables
from globaleaks.handlers.admin import tenant
from globaleaks.models import config
from globaleaks.orm import transact_wrap
from globaleaks.tests import helpers


def get_dummy_tenant_desc():
    return {
        'label': 'tenant-xxx',
        'active': True,
        'mode': 'default',
        'subdomain': 'subdomain',
    }


class TestTenantCollection(helpers.TestHandlerWithPopulatedDB):
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
        r = {}
        for i in range(0, 3):
            handler = self.request(get_dummy_tenant_desc(), role='admin')
            t = yield handler.post()
            r[i] = yield transact_wrap(config.db_get_config_variable, t['id'], 'receipt_salt')

        # Checks that the salt is actually modified from create to another
        self.assertNotEqual(r[0], r[1])
        self.assertNotEqual(r[1], r[2])
        self.assertNotEqual(r[2], r[0])


class TestTenantInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = tenant.TenantInstance

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestHandlerWithPopulatedDB.setUp(self)
        t = yield tenant.create(get_dummy_tenant_desc())
        self.handler = self.request(t, role='admin')
        yield refresh_memory_variables([4])

    def test_get(self):
        return self.handler.get(4)

    def test_put(self):
        return self.handler.put(4)

    def test_delete(self):
        return self.handler.delete(4)
