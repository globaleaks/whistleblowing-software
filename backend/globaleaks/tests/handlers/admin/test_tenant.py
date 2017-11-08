# -*- coding: utf-8 -*-"""

from globaleaks.tests import helpers

from twisted.internet.defer import inlineCallbacks
from globaleaks.handlers.admin import tenant
from globaleaks.jobs import onion_service
from globaleaks.state import State

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
        State.onion_service_job = onion_service.OnionService()
        self.test_reactor.pump([1])

    @inlineCallbacks
    def tearDown(self):
        yield State.onion_service_job.stop()
        yield helpers.TestHandlerWithPopulatedDB.tearDown(self)


class TestTenantCollection(TenantTestEnv):
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


class TestTenantInstance(TenantTestEnv):
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
