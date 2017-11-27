# -*- coding: utf-8 -*-"""
from twisted.internet.defer import inlineCallbacks

from globaleaks.models import config
from globaleaks.handlers.admin import tenant
from globaleaks.jobs import onion_service
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
def get_salt(store, tid):
    return config.PrivateFactory(store, tid).get_val(u'receipt_salt')

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
