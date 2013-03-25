# -*- coding: UTF-8
#   config
#   ******
#
# GlobaLeaks Utility Functions

from datetime import datetime, timedelta
import logging
import re
import os
import time
import traceback

from OpenSSL import SSL
from twisted.internet.endpoints import TCP4ClientEndpoint
from txsocksx.client import SOCKS5ClientEndpoint
from txsocksx.ssl import SSLWrapClientEndpoint

from StringIO import StringIO

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.mail.smtp import ESMTPSenderFactory
from twisted.internet.ssl import ClientContextFactory
from twisted.protocols import tls

from twisted.python import log as twlog
from Crypto.Hash import SHA256
from twisted.internet import fdesc

from globaleaks.settings import GLSetting


class Publisher(twlog.LogPublisher):
    """
    Customized LogPublisher
    """
    def info(self, *arg, **kw):
        kw['logLevel'] = logging.INFO
        return self.msg(*arg, **kw)

    def debug(self, *arg, **kw):
        kw['logLevel'] = logging.DEBUG
        return self.msg(*arg, **kw)

    def err(self, *arg, **kw):
        kw['logLevel'] = logging.ERROR
        return twlog.err(*arg, **kw)

    def start_logging(self):
        """
        If configured enables logserver
        """
        if GLSetting.logfile:
            logfile_observer = twlog.FileLogObserver(open(GLSetting.logfile,
                                                     'w'))
            self.addObserver(logfile_observer.emit)

        logpy_observer = twlog.PythonLoggingObserver('globaleaks')
        logpy_observer.logger.setLevel(GLSetting.loglevel)
        self.addObserver(logpy_observer.emit)

log = Publisher()


## Hashing utils

def get_file_checksum(filepath):

    sha = SHA256.new()

    chunk_size = 8192

    with open(filepath, 'rb') as fp:

        fdesc.setNonBlocking(fp.fileno())
        while True:
            chunk = fp.read(chunk_size)
            if len(chunk) == 0:
                break
            sha.update(chunk)

    return sha.hexdigest()

## time facilities ##

def utc_future_date(seconds=0, minutes=0, hours=0):
    """
    @param seconds: get a datetime obj with now+hours
    @param minutes: get a datetime obj with now+minutes
    @param hours: get a datetime obj with now+seconds
    @return: a datetime object
    """
    delta = seconds + (minutes * 60) + (hours * 3600)
    delta = timedelta(seconds=delta) - timedelta(seconds=time.timezone)
    return datetime.utcnow() + delta


def datetime_now():
    """
    @param: a random key used to cache a certain datetime
    @return: a datetime object of now, coherent with the timezone
    """
    now = datetime.utcnow() - timedelta(seconds=time.timezone)
    return now


def is_expired(old_date, seconds=0, minutes=0, hours=0, day=0):
    """
    @param old_date: the datetime stored in the databased

    @param seconds, minutes, hours, day
        the expire time of the element

    @return:
        if the amount requeste by those four param has been reached
        is returned True, else is returned False
    """
    if not old_date:
        return False

    total_hours = (day * 24) + hours
    check = old_date
    check += timedelta(seconds=seconds, minutes=minutes, hours=total_hours)
    now = datetime.utcnow() - timedelta(seconds=time.timezone)

    return now > check


def pretty_date_time(when):
    """
    @param when: a datetime
    @return: the date in ISO 8601, or 'Never' if not set
    """
    if when is None:
        return u'Never'
    else:
        return when.isoformat()

## Mail utilities ##

def sendmail(authentication_username, authentication_password, from_address,
             to_address, message_file, smtp_host, smtp_port=25, security="SSL"):
    """
    Sends an email using SSLv3 over SMTP

    @param authentication_username: account username
    @param authentication_secret: account password
    @param from_address: the from address field of the email
    @param to_address: the to address field of the email
    @param message_file: the message content
    @param smtp_host: the smtp host
    @param smtp_port: the smtp port
    """

    result_deferred = Deferred()

    context_factory = ClientContextFactory()
    context_factory.method = SSL.SSLv3_METHOD

    if security != "SSL":
        requireTransportSecurity = True
    else:
        requireTransportSecurity = False

    factory = ESMTPSenderFactory(
        authentication_username,
        authentication_password,
        from_address,
        to_address,
        message_file,
        result_deferred,
        contextFactory=context_factory,
        requireAuthentication=(authentication_username and authentication_password),
        requireTransportSecurity=requireTransportSecurity)

    if security == "SSL":
        factory = tls.TLSMemoryBIOFactory(context_factory, True, factory)

    socksProxy = TCP4ClientEndpoint(reactor, "127.0.0.1", 9050)
    endpoint = SOCKS5ClientEndpoint(smtp_host, smtp_port, socksProxy)
    endpoint.connect(factory)

    return result_deferred


def mail_exception(etype, value, tback):
    """
    Formats traceback and exception data and emails the error,
    This would be enabled only in the testing phase and testing release,
    not in production release.

    @param etype: Exception class type
    @param value: Exception string value
    @param tback: Traceback string data
    """
    mail_exception.mail_counter += 1

    exc_type = re.sub("(<(type|class ')|'exceptions.|'>|__main__.)",
                     "", str(etype))
    tmp = []

    tmp.append("From: %s\n" % ("stackexception@globaleaks.org"))
    tmp.append("To: %s\n" % ("stackexception@lists.globaleaks.org"))
    tmp.append("Subject: GLBackend Exception [%d]\n" % mail_exception.mail_counter)
    tmp.append("Content-Type: text/plain; charset=ISO-8859-1\n")
    tmp.append("Content-Transfer-Encoding: 8bit\n\n")
    tmp.append("Source: %s" % " ".join(os.uname()))
    tmp.append("%s %s" % (exc_type.strip(), etype.__doc__))
    for line in traceback.extract_tb(tback):
        tmp.append("\tFile: \"%s\"\n\t\t%s %s: %s\n"
                   % (line[0], line[2], line[1], line[3]))
    while True:
        if not tback.tb_next:
            break
        tback = tback.tb_next
    stack = []
    f = tback.tb_frame
    while f:
        stack.append(f)
        f = f.f_back
    stack.reverse()
    tmp.append("\nLocals by frame, innermost last:")
    for frame in stack:
        tmp.append("\nFrame %s in %s at line %s" % (frame.f_code.co_name,
                                                    frame.f_code.co_filename,
                                                    frame.f_lineno))
        for key, val in frame.f_locals.items():
            tmp.append("\n\t%20s = " % key)
            try:
                tmp.append(str(val))
            except Exception, e:
                tmp.append("<ERROR WHILE PRINTING VALUE> %s" % e)

    message = StringIO(''.join(tmp))

    log.debug("Exception Mail (%d):\n%s" % (mail_exception.mail_counter, ''.join(tmp)) )

    sendmail("stackexception@globaleaks.org",
             "stackexception99",
             "stackexception@globaleaks.org",
             "stackexception@lists.globaleaks.org",
             message,
             "box549.bluehost.com",
             25)

mail_exception.mail_counter = 0

def acquire_mail_address(request):
    """
    Extracts email address from request

    @param request: expect a receiver request (notification_fields key, with
        mail_address key inside)
    @return: False if is invalid or missing the email address, and the
        lowercase mail address if is valid
    """

    if 'notification_fields' not in request:
        return False

    if 'mail_address' not in request['notification_fields']:
        return False

    mail_string = str(request['notification_fields']['mail_address']).lower()
    if not re.match("^([\w-]+\.)*[\w-]+@([\w-]+\.)+[a-z]{2,4}$", mail_string):
        log.debug("Invalid email address format [%s]" % mail_string)
        return False

    return unicode(mail_string)


def acquire_url_address(inputstring, hidden_service=False, http=False):

    accepted = False

    if hidden_service and re.match("^[0-9a-z]{16}\.onion$", inputstring):
        accepted |= True

    if http and re.match("^http(s?)://(\w+)\.(.*)$", inputstring):
        accepted |= True

    return accepted
