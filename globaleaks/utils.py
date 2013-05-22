# -*- coding: UTF-8
#   utils
#   *****
#
# GlobaLeaks Utility Functions

from datetime import datetime, timedelta
import logging
import re
import os
import sys
import time
import traceback

from OpenSSL import SSL
from twisted.internet.endpoints import TCP4ClientEndpoint
from txsocksx.client import SOCKS5ClientEndpoint

from StringIO import StringIO

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.mail.smtp import ESMTPSenderFactory, SMTPClient
from twisted.internet.ssl import ClientContextFactory
from twisted.protocols import tls

from twisted.python import log as twlog
from twisted.python import logfile as twlogfile
from Crypto.Hash import SHA256

from globaleaks.settings import GLSetting
from globaleaks import __version__


class Logger(object):
    """
    Customized LogPublisher
    """
    def _str(self, msg):
        if isinstance(msg, unicode):
            return msg.encode('utf-8')
        return str(msg)

    def info(self, msg):
        if GLSetting.loglevel <= logging.INFO:
            print "[-] %s" % self._str(msg)

    def err(self, msg):
        print "[!] %s" % self._str(msg)

    def debug(self, msg):
        if GLSetting.loglevel <= logging.DEBUG:
            print "[D] %s" % self._str(msg)

    def msg(self, msg):
        print "[ ] %s" % self._str(msg)

    def start_logging(self):
        """
        If configured enables logserver
        """
        twlog.startLogging(sys.stdout)
        if GLSetting.logfile:
            name = os.path.basename(GLSetting.logfile)
            directory = os.path.dirname(GLSetting.logfile)

            logfile = twlogfile.LogFile(name, directory,
                                        rotateLength=GLSetting.log_file_size,
                                        maxRotatedFiles=GLSetting.maximum_rotated_log_files)
            twlog.addObserver(twlog.FileLogObserver(logfile).emit)

log = Logger()

def query_yes_no(question, default="no"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.

    "default" is the presumed answer if the user just hits <Enter>.
              It must be "yes" (the default), "no" or None (meaning
              an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"y":True, "n":False}
    if default == None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = raw_input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'y' or 'n'\n\n")

## Hashing utils

def get_file_checksum(filepath):
    sha = SHA256.new()

    chunk_size = 8192

    with open(filepath, 'rb') as fp:
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
    delta = timedelta(seconds=(seconds + (minutes * 60) + (hours * 3600)))
    return datetime.utcnow() + delta

def datetime_now():
    """
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

def pretty_diff_now(past_date):
    """
    @param past_date: source date in the past of now()
    @return: differences in time up to now(), pretty format
    """
    if not past_date:
        return u"Never"

    now = datetime.utcnow() - timedelta(seconds=time.timezone)
    diff = now - past_date

    diff = int(diff.total_seconds())
    days, hours_carry = divmod(diff, 3600 * 24)
    hours, minutes_carry = divmod(hours_carry, 3600)
    minutes, seconds = divmod(minutes_carry, 60)

    pretty_str = ''
    if seconds:
        pretty_str = "1 second" if seconds == 1 else "%s seconds" % seconds
    if minutes:
        pretty_str = "1 minute" if minutes == 1 else "%s minutes" % minutes
    if hours:
        pretty_str = "1 hour" if hours == 1 else "%s hours" % hours
    if days:
        pretty_str = "1 day" if days == 1 else "%s days" % days

    #return '%sD+%s:%s:%s' % (days, hours, minutes, seconds)
    return pretty_str

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

    def sendError(self, exc):
        if exc.code and exc.resp:
            log.err("STMP Error: %.3d %s" % (exc.code, exc.resp))
        SMTPClient.sendError(self, exc)

    factory.protocol.sendError = sendError

    if security == "SSL":
        factory = tls.TLSMemoryBIOFactory(context_factory, True, factory)

    if GLSetting.tor_socks_enable:
        socksProxy = TCP4ClientEndpoint(reactor, GLSetting.socks_host, GLSetting.socks_port)
        endpoint = SOCKS5ClientEndpoint(smtp_host, smtp_port, socksProxy)
    else:
        endpoint = TCP4ClientEndpoint(reactor, smtp_host, smtp_port)

    d = endpoint.connect(factory)
    d.addErrback(result_deferred.errback)

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
    # this is an hack because inside the Generator, not a great stacktrace is produced
    if(etype == GeneratorExit):
        log.debug("Exception unhandled inside generator")
        return

    mail_exception.mail_counter += 1

    exc_type = re.sub("(<(type|class ')|'exceptions.|'>|__main__.)",
                     "", str(etype))
    tmp = []

    tmp.append("From: %s" % GLSetting.error_reporting_username)
    tmp.append("To: %s" % GLSetting.error_reporting_username)
    tmp.append("Subject: GLBackend Exception %s [%d]" % (__version__, mail_exception.mail_counter) )
    tmp.append("Content-Type: text/plain; charset=ISO-8859-1")
    tmp.append("Content-Transfer-Encoding: 8bit\n")
    tmp.append("Source: %s\n" % " ".join(os.uname()))
    tmp.append("Version: %s\n" % __version__)
    error_message = "%s %s" % (exc_type.strip(), etype.__doc__)
    tmp.append(error_message)

    traceinfo = '\n'.join(traceback.format_exception(etype, value, tback))
    tmp.append(traceinfo)

    info_string = '\n'.join(tmp)
    message = StringIO(info_string)

    log.err(error_message)
    log.err(traceinfo)
    log.debug("Exception Mail (%d):\n%s" % (mail_exception.mail_counter, info_string) )

    sendmail(GLSetting.error_reporting_username,
             GLSetting.error_reporting_password,
             GLSetting.error_reporting_username,
             GLSetting.error_reporting_destmail,
             message,
             GLSetting.error_reporting_server,
             GLSetting.error_reporting_port)

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

    mail_string = request['notification_fields']['mail_address'].lower()
    if not re.match("^([\w-]+\.)*[\w-]+@([\w-]+\.)+[a-z]{2,4}$", mail_string):
        log.debug("Invalid email address format [%s]" % mail_string)
        return False

    return unicode(mail_string)


def acquire_url_address(inputstring, hidden_service=False, http=False):

    accepted = False

    if hidden_service and re.match("^http://[0-9a-z]{16}\.onion$", inputstring):
        accepted |= True

    if http and re.match("^http(s?)://(\w+)\.(.*)$", inputstring):
        accepted |= True

    return accepted
