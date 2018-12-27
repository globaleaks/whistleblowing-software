# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from OpenSSL.crypto import load_certificate, FILETYPE_PEM

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.admin.https import db_acme_cert_issuance
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.user import db_get_admin_users
from globaleaks.jobs.job import LoopingJob
from globaleaks.orm import transact
from globaleaks.utils import letsencrypt
from globaleaks.utils.utility import datetime_to_ISO8601
from globaleaks.utils.log import log


class CertificateCheck(LoopingJob):
    interval = 24 * 3600

    notify_expr_within = 15
    acme_try_renewal = 15
    should_restart_https = False

    def certificate_mail_creation(self, session, mail_type, tid, expiration_date):
        for user_desc in db_get_admin_users(session, tid):
            lang = user_desc['language']

            template_vars = {
                'type': mail_type,
                'node': db_admin_serialize_node(session, tid, lang),
                'notification': db_get_notification(session, tid, lang),
                'expiration_date': expiration_date,
                'user': user_desc,
            }

            self.state.format_and_send_mail(session, tid, user_desc, template_vars)

    @transact
    def check_tenants_for_cert_expiration(self, session):
        for tenant in session.query(models.Tenant.id).filter(models.Tenant.active == True):
            self.cert_expiration_checks(session, tenant[0])

    def cert_expiration_checks(self, session, tid):
        priv_fact = models.config.ConfigFactory(session, tid, 'node')

        if not priv_fact.get_val(u'https_enabled'):
            return

        cert = load_certificate(FILETYPE_PEM, priv_fact.get_val(u'https_cert'))
        expiration_date = letsencrypt.convert_asn1_date(cert.get_notAfter())
        expiration_date_iso = datetime_to_ISO8601(expiration_date)

        # Acme renewal checks
        if priv_fact.get_val(u'acme') and datetime.now() > expiration_date - timedelta(days=self.acme_try_renewal):
            try:
                db_acme_cert_issuance(session, tid)
            except Exception as exc:
                log.err('Automatic HTTPS renewal failed: %s', exc, tid=tid)

                # Send an email to the admin cause this requires user intervention
                if not self.state.tenant_cache[tid].notification.disable_admin_notification_emails:
                    self.certificate_mail_creation(session, 'https_certificate_renewal_failure', tid, expiration_date_iso)
            else:
                self.should_restart_https = True

        # Regular certificates expiration checks
        elif datetime.now() > expiration_date - timedelta(days=self.notify_expr_within):
            log.info('The HTTPS Certificate is expiring on %s', expiration_date, tid=tid)
            if not self.state.tenant_cache[tid].notification.disable_admin_notification_emails:
                self.certificate_mail_creation(session, 'https_certificate_expiration', tid, expiration_date_iso)

    @inlineCallbacks
    def operation(self):
        yield self.check_tenants_for_cert_expiration()

        if self.should_restart_https:
            self.should_restart_https = False
            yield self.state.process_supervisor.shutdown()
            yield self.state.process_supervisor.maybe_launch_https_workers()
