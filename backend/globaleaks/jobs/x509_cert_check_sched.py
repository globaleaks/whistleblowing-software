from datetime import datetime, timedelta

from OpenSSL.crypto import load_certificate, FILETYPE_PEM
from globaleaks import models
from globaleaks.handlers.admin.https import db_acme_cert_issuance
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.user import db_get_admin_users
from globaleaks.jobs.base import LoopingJob
from globaleaks.orm import transact_sync
from globaleaks.security import encrypt_message
from globaleaks.settings import GLSettings
from globaleaks.utils import letsencrypt
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import log


def should_try_acme_renewal(num_failures):
    acme = GLSettings.memory_copy.private.acme
    https_enabled = GLSettings.memory_copy.private.https_enabled

    if https_enabled and acme and num_failures < 30:
        return True

    return False


class X509CertCheckSchedule(LoopingJob):
    name = "X509 Cert Check"
    interval = 3 * 24 * 3600

    notify_expr_within = 15
    acme_try_renewal = 30

    acme_failures = 0

    def operation(self):
        if should_try_acme_renewal(self.acme_failures):
            self.acme_cert_renewal_checks()

        self.cert_expiration_checks()

    @transact_sync
    def acme_cert_renewal_checks(self, store):
        cert = load_certificate(FILETYPE_PEM, GLSettings.memory_copy.private.https_cert)
        expiration_date = letsencrypt.convert_asn1_date(cert.get_notAfter())

        t = timedelta(days=self.acme_try_renewal)
        renewal_window = datetime.now() + t

        if not expiration_date < renewal_window:
            # We will not apply for the renewal of the certificate
            return

        try:
            db_acme_cert_issuance(store)
        except Exception as excep:
            self.acme_failures =+ 1
            log.err('ACME certificate renewal failed with: %s', excep)
            raise
        try:
            yield GLSettings.appstate.process_supervisor.shutdown()
            yield GLSettings.appstate.process_supervisor.maybe_launch_https_workers()
        except Exception as excep:
            self.acme_failures =+ 1
            log.err('Restart of HTTPS workers failed with: %s', excep)
            raise

    @transact_sync
    def cert_expiration_checks(self, store):
        if not GLSettings.memory_copy.private.https_enabled:
            return

        cert = load_certificate(FILETYPE_PEM, GLSettings.memory_copy.private.https_cert)
        expiration_date = letsencrypt.convert_asn1_date(cert.get_notAfter())

        t = timedelta(days=self.notify_expr_within)
        expiration_window = datetime.now() + t
        if not expiration_date < expiration_window:
            log.debug('The HTTPS certificate is not going to expire within target window.')
            return

        if GLSettings.memory_copy.notif.disable_admin_notification_emails:
            log.info('Certificate expiring on %s, admin notif email suppressed', expiration_date)
        else:
            self.certificate_mail_creation(store, expiration_date)

    def certificate_mail_creation(self, store, expiration_date):
        for user_desc in db_get_admin_users(store):
            lang = user_desc['language']

            template_vars = {
                'type': 'https_certificate_expiration',
                'expiration_date': expiration_date,
                'node': db_admin_serialize_node(store, lang),
                'notification': db_get_notification(store, lang)
            }

            subject, body = Templating().get_mail_subject_and_body(template_vars)

            # encrypt the notification if the admin has configured the issue.
            if user_desc['pgp_key_public']:
                body = encrypt_message(user_desc['pgp_key_public'], body)

            store.add(models.Mail({
                'address': user_desc['mail_address'],
                'subject': subject,
                'body': body
            }))
