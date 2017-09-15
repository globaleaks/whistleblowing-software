# -*- coding: utf-8 -*-
from globaleaks import models
from globaleaks.db import db_refresh_memory_variables
from globaleaks.jobs.x509_cert_check_sched import X509CertCheckSchedule
from globaleaks.models.config import PrivateFactory
from globaleaks.orm import transact
from globaleaks.state import State
from globaleaks.tests import helpers
from globaleaks.tests.utils import test_tls
from twisted.internet.defer import inlineCallbacks


class TestX509CertCheckSched(helpers.TestGLWithPopulatedDB):

    @inlineCallbacks
    def setUp(self):
        yield helpers.TestGLWithPopulatedDB.setUp(self)
        yield self._setUp()

    @transact
    def _setUp(self, store):
        valid_setup = test_tls.get_valid_setup()

        prv_fact = PrivateFactory(store, 1)
        prv_fact.set_val(u'https_cert', valid_setup['cert'])
        prv_fact.set_val(u'https_enabled', True)

        db_refresh_memory_variables(store)

    @inlineCallbacks
    def test_cert_check_sched(self):
        yield self.test_model_count(models.Mail, 0)

        yield X509CertCheckSchedule().run()

        yield self.test_model_count(models.Mail, 0)

        X509CertCheckSchedule.notify_expr_within = 15*365
        yield X509CertCheckSchedule().run()

        yield self.test_model_count(models.Mail, 1)

        State.tenant_cache[1].notif.disable_admin_notification_emails = True

        yield X509CertCheckSchedule().run()

        yield self.test_model_count(models.Mail, 1)
