# -*- coding: utf-8 -*-"""
from twisted.internet.defer import inlineCallbacks
from globaleaks.handlers.admin import tenant
from globaleaks.tests import helpers

def get_dummy_tenant_desc():
    return {
        'label': 'tenant-xxx',
        'active': True
    }

class TestTenantCollection(helpers.TestHandlerWithPopulatedDB):
    _handler = tenant.TenantCollection

    @inlineCallbacks
    def test_get(self):
        for i in range(3):
            yield tenant.create(get_dummy_tenant_desc())

        handler = self.request(role='admin')
        response = yield handler.get()

        self.assertEqual(len(response), 4)

    @inlineCallbacks
    def test_post(self):
        handler = self.request(get_dummy_tenant_desc(), role='admin')
        yield handler.post()


class TestTenantInstance(helpers.TestHandlerWithPopulatedDB):
    _handler = tenant.TenantInstance

    @inlineCallbacks
    def test_get(self):
        t = yield tenant.create(get_dummy_tenant_desc())

        handler = self.request(role='admin')
        yield handler.get(t['id'])

    @inlineCallbacks
    def test_put(self):
        t = yield tenant.create(get_dummy_tenant_desc())

        handler = self.request(t, role='admin')
        yield handler.put(t['id'])

    @inlineCallbacks
    def test_delete(self):
        t = yield tenant.create(get_dummy_tenant_desc())

        handler = self.request(role='admin')
        yield handler.delete(t['id'])
