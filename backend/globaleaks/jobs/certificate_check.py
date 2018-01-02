# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from OpenSSL.crypto import load_certificate, FILETYPE_PEM

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.admin.https import db_acme_cert_issuance
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.user import db_get_admin_users
from globaleaks.jobs.base import LoopingJob
from globaleaks.orm import transact
from globaleaks.utils import letsencrypt
from globaleaks.utils.utility import datetime_to_ISO8601, log
from globaleaks.utils.templating import format_and_send

class CertificateCheck(LoopingJob):
    interval = 3 * 24 * 3600

    notify_expr_within = 15
    acme_try_renewal = 30
    acme_failures = 0
    should_restart_https = False

    def certificate_mail_creation(self, store, tid, expiration_date):
        for user_desc in db_get_admin_users(store, tid):
            lang = user_desc['language']

            template_vars = {
                'type': 'https_certificate_expiration',
                'node': db_admin_serialize_node(store, tid, lang),
                'notification': db_get_notification(store, tid, lang),
                'expiration_date': expiration_date,
                'user': user_desc,
            }

            format_and_send(store, tid, user_desc, template_vars)

    @transact
    def check_tenants_for_cert_expiration(self, store):
        for tid in store.find(models.Tenant.id, models.Tenant.active == True):
            self.cert_expiration_checks(store, tid)

    def cert_expiration_checks(self, store, tid):
        priv_fact = models.config.PrivateFactory(store, tid)

        if not priv_fact.get_val(u'https_enabled'):
            return

        cert = load_certificate(FILETYPE_PEM, priv_fact.get_val(u'https_cert'))
        expiration_date = letsencrypt.convert_asn1_date(cert.get_notAfter())

        # Acme renewal checks
        if priv_fact.get_val(u'acme') and datetime.now() > expiration_date - timedelta(days=self.acme_try_renewal):
            try:
                db_acme_cert_issuance(store, tid)
            except Exception as excep:
                self.acme_failures =+ 1
                log.err('ACME certificate renewal failed with: %s', excep, tid=tid)
                raise

            self.should_restart_https = True
            self.acme_failures = 0

        # Regular certificates expiration checks
        elif datetime.now() > expiration_date - timedelta(days=self.notify_expr_within):
            expiration_date = datetime_to_ISO8601(expiration_date)
            log.info('The HTTPS Certificate is expiring on %s', expiration_date, tid=tid)
            if not self.state.tenant_cache[tid].notification.disable_admin_notification_emails:
                self.certificate_mail_creation(store, tid, expiration_date)

    @inlineCallbacks
    def operation(self):
        yield self.check_tenants_for_cert_expiration()

        if self.should_restart_https:
            self.should_restart_https = False
            yield self.state.process_supervisor.shutdown()
            yield self.state.process_supervisor.maybe_launch_https_workers()
