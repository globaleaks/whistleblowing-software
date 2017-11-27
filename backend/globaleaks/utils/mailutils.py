# -*- coding: utf-8
#
# mailutils
# *********
#
# GlobaLeaks Utility used to handle Mail, format, exception, etc

import StringIO
import re
import sys
import traceback
from email import utils, Charset  # pylint: disable=no-name-in-module
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from txsocksx.client import SOCKS5ClientEndpoint

from twisted.internet import reactor, defer
from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.mail.smtp import ESMTPSenderFactory, SMTPError
from twisted.protocols import tls
from twisted.python.failure import Failure

from globaleaks import __version__
from globaleaks.utils.tls import TLSClientContextFactory
from globaleaks.utils.utility import log


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
    multipart['Date'] = utils.formatdate()
    multipart['To'] = Header(dest_name.encode('utf-8'), 'UTF-8').encode() + " <" + dest_mail + ">"
    multipart['From'] = Header(src_name.encode('utf-8'), 'UTF-8').encode() + " <" + src_mail + ">"
    multipart['X-Mailer'] = "fnord"

    multipart.attach(MIMEText(mail_body.encode('utf-8'), 'plain', 'UTF-8'))

    return StringIO.StringIO(multipart.as_string())


def sendmail(tid, username, password, smtp_host, smtp_port, security, from_name, from_address, to_address, subject, body, anonymize=True, socks_host='127.0.0.1', socks_port=9050):
    """
    Send an email using SMTPS/SMTP+TLS and maybe torify the connection.

    @param to_address: the 'To:' field of the email
    @param subject: the mail subject
    @param body: the mail body

    @return: a {Deferred} that returns a success {bool} if the message was passed
             to the server.
    """
    try:
        timeout = 30

        message = MIME_mail_build(from_name,
                                  from_address,
                                  to_address,
                                  to_address,
                                  subject,
                                  body)

        log.debug('Sending email to %s using SMTP server [%s:%d] [%s]',
                  to_address,
                  smtp_host,
                  smtp_port,
                  security,
                  tid=tid)

        context_factory = TLSClientContextFactory()

        smtp_deferred = defer.Deferred()

        factory = ESMTPSenderFactory(
            username.encode('utf-8'),
            password.encode('utf-8'),
            from_address,
            to_address,
            message,
            smtp_deferred,
            contextFactory=context_factory,
            requireAuthentication=True,
            requireTransportSecurity=(security != 'SSL'),
            retries=0,
            timeout=timeout)

        if security == "SSL":
            factory = tls.TLSMemoryBIOFactory(context_factory, True, factory)

        if anonymize:
            socksProxy = TCP4ClientEndpoint(reactor, socks_host, socks_port, timeout=timeout)
            endpoint = SOCKS5ClientEndpoint(smtp_host.encode('utf-8'), smtp_port, socksProxy)
        else:
            endpoint = TCP4ClientEndpoint(reactor, smtp_host.encode('utf-8'), smtp_port, timeout=timeout)

        conn_deferred = endpoint.connect(factory)

        final = defer.DeferredList([conn_deferred, smtp_deferred], fireOnOneErrback=True, consumeErrors=True)

        def failure_cb(failure):
            """
            @param failure {Failure {twisted.internet.FirstError {Failure}}}
            """
            log.err("SMTP connection failed (Exception: %s)", failure.value.subFailure.valued, tid=tid)
            log.debug(failure)
            return False

        def success_cb(results):
            """
            @param results {list of (success, return_val) tuples}
            """
            return True

        final.addCallback(success_cb)
        final.addErrback(failure_cb)

        return final

    except Exception as excep:
        # avoids raising an exception inside email logic to avoid chained errors
        log.err("Unexpected exception in sendmail:", str(excep), tid=tid)
        return defer.succeed(False)


def mail_exception_handler(etype, value, tback):
    """
    Formats traceback and exception data and emails the error,
    This would be enabled only in the testing phase and testing release,
    not in production release.
    """
    if isinstance(value, (GeneratorExit,
                          defer.AlreadyCalledError,
                          SMTPError)) or \
        (etype == AssertionError and value.message == "Request closed"):
        # we need to bypass email notification for some exception that:
        # 1) raise frequently or lie in a twisted bug;
        # 2) lack of useful stacktraces;
        # 3) can be cause of email storm amplification
        #
        # this kind of exception can be simply logged error logs.
        log.err("exception mail suppressed for exception (%s) [reason: special exception]", str(etype))
        return

    # collection of the stacktrace info
    exc_type = re.sub("(<(type|class ')|'exceptions.|'>|__main__.)",
                      "", str(etype))
    error_message = "%s %s" % (exc_type.strip(), etype.__doc__)
    traceinfo = '\n'.join(traceback.format_exception(etype, value, tback))

    mail_body = error_message + "\n\n" + traceinfo

    log.err("Unhandled exception raised:")
    log.err(mail_body)

    from globaleaks.state import State
    State.schedule_exception_email(mail_body)


def extract_exception_traceback_and_schedule_email(e):
    if isinstance(e, Failure):
        mail_exception_handler(e.type, e.value, e.getTracebackObject())
    else:
        mail_exception_handler(*sys.exc_info())
