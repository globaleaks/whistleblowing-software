# -*- coding: UTF-8
#
# mailutils
# *********
#
# GlobaLeaks Utility used to handle Mail, format, exception, etc

import logging
import re
import traceback
import StringIO
from datetime import datetime
from calendar import timegm
from email import utils as mailutils
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.header import Header
from email import Charset

from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet import reactor, protocol, error,  defer
from twisted.mail.smtp import ESMTPSenderFactory, SMTPClient, SMTPClientError, SMTPError
from twisted.internet.ssl import ClientContextFactory
from twisted.protocols import tls
from twisted.python.failure import Failure

from OpenSSL import SSL
from txsocksx.client import SOCKS5ClientEndpoint

from globaleaks import __version__
from globaleaks.utils.utility import log, setDeferredTimeout
from globaleaks.settings import GLSettings
from globaleaks.security import GLBPGP, sha256


def rfc822_date():
    """
    holy stackoverflow:
    http://stackoverflow.com/questions/3453177/convert-python-datetime-to-rfc-2822
    """
    nowdt = datetime.utcnow()
    nowtuple = nowdt.utctimetuple()
    nowtimestamp = timegm(nowtuple)
    return mailutils.formatdate(nowtimestamp)


class GLClientContextFactory(ClientContextFactory):
    # evilaliv3:
    #   this is the same solution I applied to tor2web:
    #     as discussed on https://trac.torproject.org/projects/tor/ticket/11598
    #     there is no way of enabling all TLS methods excluding SSL.
    #     the problem lies in the fact that SSL.TLSv1_METHOD | SSL.TLSv1_1_METHOD | SSL.TLSv1_2_METHOD
    #     is denied by OpenSSL.
    #
    #     The solution implemented is to enable SSL.SSLv23_METHOD then explicitly
    #     use options: SSL_OP_NO_SSLv2 and SSL_OP_NO_SSLv3
    #
    #     This trick make openssl consider valid all TLS methods.

    method = SSL.SSLv23_METHOD

    _contextFactory = SSL.Context

    def getContext(self):
        ctx = self._contextFactory(self.method)
        ctx.set_options(SSL.OP_NO_SSLv2 | SSL.OP_NO_SSLv3)
        return ctx


def sendmail(to_address, subject, body):
    """
    Sends an email using SMTPS/SMTP+TLS and torify the connection

    @param to_address: the to address field of the email
    @param subject: the mail subject
    @param body: the mail body
    @param event: the event description, needed to keep track of failure/success
    """
    try:
        if GLSettings.disable_mail_notification:
            return defer.succeed(None)

        if to_address == "":
            return

        result_deferred = defer.Deferred()

        def errback(reason, *args, **kwargs):
            # TODO: here it should be written a complete debugging of the possible
            #       errors by writing clear log lines in relation to all the stack:
            #       e.g. it should debugged all errors related to: TCP/SOCKS/TLS/SSL/SMTP/SFIGA
            if isinstance(reason, Failure):
                log.err("SMTP connection failed (Exception: %s)" % reason.value)
                log.debug(reason)

            return result_deferred.errback(reason)

        authentication_username=GLSettings.memory_copy.notif_username
        authentication_password=GLSettings.memory_copy.notif_password
        from_address=GLSettings.memory_copy.notif_source_email
        smtp_host=GLSettings.memory_copy.notif_server
        smtp_port=GLSettings.memory_copy.notif_port
        security=GLSettings.memory_copy.notif_security

        message = MIME_mail_build(GLSettings.memory_copy.notif_source_name,
                                  GLSettings.memory_copy.notif_source_email,
                                  to_address,
                                  to_address,
                                  subject,
                                  body)

        log.debug('Sending email to %s using SMTP server [%s:%d] [%s]' %
                  (to_address, smtp_host, smtp_port, security))

        context_factory = GLClientContextFactory()

        esmtp_deferred = defer.Deferred()
        esmtp_deferred.addCallbacks(result_deferred.callback, errback)

        factory = ESMTPSenderFactory(
            authentication_username.encode('utf-8'),
            authentication_password.encode('utf-8'),
            from_address,
            to_address,
            message,
            esmtp_deferred,
            contextFactory=context_factory,
            requireAuthentication=True,
            requireTransportSecurity=(security != 'SSL'),
            retries=0,
            timeout=GLSettings.mail_timeout)

        if security == "SSL":
            factory = tls.TLSMemoryBIOFactory(context_factory, True, factory)

        if GLSettings.testing:
            #  Hooking the test down to here is a trick to be able to test all the above code :)
            return defer.succeed(None)

        if not GLSettings.disable_mail_torification:
            socksProxy = TCP4ClientEndpoint(reactor, GLSettings.socks_host, GLSettings.socks_port, timeout=GLSettings.mail_timeout)
            endpoint = SOCKS5ClientEndpoint(smtp_host.encode('utf-8'), smtp_port, socksProxy)
        else:
            endpoint = TCP4ClientEndpoint(reactor, smtp_host.encode('utf-8'), smtp_port, timeout=GLSettings.mail_timeout)

        d = endpoint.connect(factory)
        d.addErrback(errback)

        setDeferredTimeout(result_deferred, 90)

        return result_deferred

    except Exception as excep:
        # we strongly need to avoid raising exception inside email logic to avoid chained errors
        log.err("Unexpected exception in sendmail: %s" % str(excep))
        return defer.fail()


def MIME_mail_build(src_name, src_mail, dest_name, dest_mail, title, mail_body):
    # Override python's weird assumption that utf-8 text should be encoded with
    # base64, and instead use quoted-printable (for both subject and body).  I
    # can't figure out a way to specify QP (quoted-printable) instead of base64 in
    # a way that doesn't modify global state. :-(
    Charset.add_charset('utf-8', Charset.QP, Charset.QP, 'utf-8')

    # This example is of an email with text and html alternatives.
    multipart = MIMEMultipart('alternative')

    # We need to use Header objects here instead of just assigning the strings in
    # order to get our headers properly encoded (with QP).
    # You may want to avoid this if your headers are already ASCII, just so people
    # can read the raw message without getting a headache.
    multipart['Subject'] = Header(title.encode('utf-8'), 'UTF-8').encode()
    multipart['Date'] = rfc822_date()

    multipart['To'] = Header(dest_name.encode('utf-8'), 'UTF-8').encode() + \
                        " <" + dest_mail + ">"

    multipart['From'] = Header(src_name.encode('utf-8'), 'UTF-8').encode() + \
                        " <" + src_mail + ">"

    multipart['X-Mailer'] = "fnord"

    textpart = MIMEText(mail_body.encode('utf-8'), 'plain', 'UTF-8')
    multipart.attach(textpart)

    return StringIO.StringIO(multipart.as_string())


def mail_exception_handler(etype, value, tback):
    """
    Formats traceback and exception data and emails the error,
    This would be enabled only in the testing phase and testing release,
    not in production release.
    """
    if GLSettings.disable_backend_exception_notification:
        return

    if isinstance(value, GeneratorExit) or \
       isinstance(value, defer.AlreadyCalledError) or \
       isinstance(value, SMTPError) or \
        etype == AssertionError and value.message == "Request closed":
        # we need to bypass email notification for some exception that:
        # 1) raise frequently or lie in a twisted bug;
        # 2) lack of useful stacktraces;
        # 3) can be cause of email storm amplification
        #
        # this kind of exception can be simply logged error logs.
        log.err("exception mail suppressed for exception (%s) [reason: special exception]" % str(etype))
        return

    # collection of the stacktrace info
    exc_type = re.sub("(<(type|class ')|'exceptions.|'>|__main__.)",
                      "", str(etype))
    error_message = "%s %s" % (exc_type.strip(), etype.__doc__)
    traceinfo = '\n'.join(traceback.format_exception(etype, value, tback))

    mail_body = error_message + "\n\n" + traceinfo

    log.err("Unhandled exception raised:")
    log.err(mail_body)

    send_exception_email(mail_body)


def send_exception_email(mail_body, mail_reason="GlobaLeaks Exception"):
    if (GLSettings.exceptions_email_count >= GLSettings.exceptions_email_hourly_limit):
        return

    if isinstance(mail_body, str) or isinstance(mail_body, unicode):
        mail_body = bytes(mail_body)

    if not hasattr(GLSettings.memory_copy, 'notif_source_name') or \
        not hasattr(GLSettings.memory_copy, 'notif_source_email') or \
        not hasattr(GLSettings.memory_copy, 'exception_email_address'):
        log.err("Error: Cannot send mail exception before complete initialization.")
        return

    sha256_hash = sha256(mail_body)

    if sha256_hash in GLSettings.exceptions:
        GLSettings.exceptions[sha256_hash] += 1
        if GLSettings.exceptions[sha256_hash] > 5:
            # if the threshold has been exceeded
            log.err("exception mail suppressed for exception (%s) [reason: threshold exceeded]" % sha256_hash)
            return
    else:
        GLSettings.exceptions[sha256_hash] = 1

    GLSettings.exceptions_email_count += 1

    try:
        mail_subject = "%s %s" % (mail_reason, __version__)
        if GLSettings.devel_mode:
            mail_subject +=  " [%s]" % GLSettings.developer_name

        # If the receiver has encryption enabled (for notification), encrypt the mail body
        if GLSettings.memory_copy.exception_email_pgp_key_status == u'enabled':
            gpob = GLBPGP()
            try:
                gpob.load_key(GLSettings.memory_copy.exception_email_pgp_key_public)
                mail_body = gpob.encrypt_message(GLSettings.memory_copy.exception_email_pgp_key_fingerprint, mail_body)
            except Exception as excep:
                # If exception emails are configured to be subject to encryption an the key
                # expires the only thing to do is to disable the email.
                # TODO: evaluate if notificate an alert in plaintext to the exception email
                #       this could be done simply here replacing the email subject and body.
                log.err("Error while encrypting exception email: %s" % str(excep))
                return None
            finally:
                # the finally statement is always called also if
                # except contains a return or a raise
                gpob.destroy_environment()

        # avoid to wait for the notification to happen  but rely on  background completion
        sendmail(GLSettings.memory_copy.exception_email_address, mail_subject,  mail_body)

    except Exception as excep:
        # we strongly need to avoid raising exception inside email logic to avoid chained errors
        log.err("Unexpected exception in process_mail_exception: %s" % excep)
