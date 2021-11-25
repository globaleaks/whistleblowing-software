# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from twisted.internet.defer import inlineCallbacks

from OpenSSL.crypto import load_certificate, FILETYPE_PEM


from globaleaks import models
from globaleaks.handlers.admin.https import db_acme_cert_request, load_tls_dict
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.user import db_get_users
from globaleaks.jobs.job import DailyJob
from globaleaks.orm import transact
from globaleaks.utils import letsencrypt
from globaleaks.utils.log import log
from globaleaks.utils.utility import deferred_sleep


class CertificateCheck(DailyJob):
    interval = 24 * 3600

    # Notify about failing HTTPS renewal starting from a week before
    # expiration. This setting is choosen as the half of the
    # letsencrypt renewal threshold. This particular choice is intended
    # to limit the number of email sent enabling up 7 days of failing
    # retries without sending emails.

    notify_expr_within = 7
    acme_try_renewal = 14

    def certificate_mail_creation(self, session, mail_type, tid, expiration_date):
        for user_desc in db_get_users(session, tid, 'admin'):
            if not user_desc['notification']:
                continue

            lang = user_desc['language']

            template_vars = {
                'type': mail_type,
                'node': db_admin_serialize_node(session, tid, lang),
                'notification': db_get_notification(session, tid, lang),
                'expiration_date': expiration_date,
                'user': user_desc,
            }

            self.state.format_and_send_mail(session, tid, user_desc['mail_address'], template_vars)

    @transact
    def cert_expiration_checks(self, session, tid):
        now = datetime.now()

        priv_fact = models.config.ConfigFactory(session, tid)

        if not priv_fact.get_val('https_enabled'):
            return

        cert = load_certificate(FILETYPE_PEM, priv_fact.get_val('https_cert'))
        expiration_date = letsencrypt.convert_asn1_date(cert.get_notAfter())

        # Acme renewal checks
        if priv_fact.get_val('acme') and now > expiration_date - timedelta(self.acme_try_renewal):
            try:
                db_acme_cert_request(session, tid)
            except Exception as exc:
                log.err('Automatic HTTPS renewal failed: %s', exc, tid=tid)

                # Send an email to the admin cause this requires user intervention
                if now > expiration_date - timedelta(self.notify_expr_within) and \
                   not self.state.tenant_cache[tid].notification.disable_admin_notification_emails:
                    self.certificate_mail_creation(session, 'https_certificate_renewal_failure', tid, expiration_date)

            tls_config = load_tls_dict(session, tid)

            self.state.snimap.unload(tid)
            self.state.snimap.load(tid, tls_config)

        # Regular certificates expiration checks
        elif now > expiration_date - timedelta(self.notify_expr_within):
            log.info('The HTTPS Certificate is expiring on %s', expiration_date, tid=tid)
            if not self.state.tenant_cache[tid].notification.disable_admin_notification_emails:
                self.certificate_mail_creation(session, 'https_certificate_expiration', tid, expiration_date)

    @inlineCallbacks
    def operation(self):
        for tid in self.state.tenant_state.keys():
            yield self.cert_expiration_checks(tid)
            yield deferred_sleep(5)
