from datetime import datetime, timedelta

from OpenSSL.crypto import load_certificate, FILETYPE_PEM

from globaleaks import models
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.https import db_acme_cert_issuance
from globaleaks.handlers.admin.user import db_get_admin_users
from globaleaks.jobs.base import GLJob
from globaleaks.orm import transact_sync
from globaleaks.security import encrypt_pgp_message
from globaleaks.settings import GLSettings
from globaleaks.utils import lets_enc
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import log


def should_try_acme_renewal(failures):
    # TODO check num failures isn't high
    acme_autorenew = GLSettings.memory_copy.private.acme_autorenew
    https_enabled = GLSettings.memory_copy.private.https_enabled
    if not (https_enabled and acme_autorenew):
        return False
    return True


class X509CertCheckSchedule(GLJob):
    name = "X509 Cert Check"
    interval = 3 * 24 * 3600

    notify_expr_within = 15
    acme_failures = 0
    acme_try_renewal = 30

    def operation(self):
        if should_try_acme_renewal(self.acme_failures):
             self.acme_cert_renewal_checks()
        self.cert_expiration_checks()

    @transact_sync
    def acme_cert_renewal_checks(self, store):

        cert = load_certificate(FILETYPE_PEM, GLSettings.memory_copy.private.https_cert)
        expiration_date = lets_enc.convert_asn1_date(cert.get_notAfter())

        t = timedelta(days=self.acme_try_renewal)
        renewal_window = datetime.now() + t

        if not expiration_date < renewal_window:
            # We will not apply for the renewal of the certificate
            return

        try:
            db_acme_cert_issuance(store, None)
        except Exception as e:
            self.acme_failures =+ 1
            log.err('ACME certificate renewal failed with: %s' % e)
            raise

    @transact_sync
    def cert_expiration_checks(self, store):
        if not GLSettings.memory_copy.private.https_enabled:
            return

        cert = load_certificate(FILETYPE_PEM, GLSettings.memory_copy.private.https_cert)
        expiration_date = lets_enc.convert_asn1_date(cert.get_notAfter())

        t = timedelta(days=self.notify_expr_within)
        expiration_window = datetime.now() + t
        if not expiration_date < expiration_window:
            # The certificate is not going to expire within window.
            return

        # The certificate is going to expire. Mail the administrator
        self.certificate_mail_creation(store, expiration_date)

    def certificate_mail_creation(self, store, expiration_date):
        for user_desc in db_get_admin_users(store):
            lang = user_desc['language']

            template_vars = {
                'type': 'x509_certificate_expiration',
                'expiration_date': expiration_date,
                'node': db_admin_serialize_node(store, lang),
            }
            subject, body = Templating().get_mail_subject_and_body(template_vars)

            # encrypt the notification if the admin has configured the issue.
            pub_key = user_desc['pgp_key_public']
            if len(pub_key) > 0:
                body = encrypt_pgp_message(pub_key, user_desc['pgp_key_fingerprint'], body)

            store.add(models.Mail({
                'address': user_desc['mail_address'],
                'subject': subject,
                'body': body
            }))
