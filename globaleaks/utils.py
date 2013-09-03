# -*- coding: UTF-8
#   utils
#   *****
#
# GlobaLeaks Utility Functions

from datetime import datetime, timedelta
import cgi
import inspect
import logging
import re
import os
import sys
import time
import traceback
import cStringIO

from twisted.internet.endpoints import TCP4ClientEndpoint
from twisted.internet import reactor, protocol, error
from twisted.internet.defer import Deferred
from twisted.mail.smtp import ESMTPSenderFactory, SMTPClient
from twisted.internet.ssl import ClientContextFactory
from twisted.protocols import tls
from twisted.python import log as twlog
from twisted.python import logfile as twlogfile
from twisted.python import util
from twisted.python.failure import Failure

from OpenSSL import SSL
from txsocksx.client import SOCKS5ClientEndpoint
from Crypto.Hash import SHA256

from globaleaks.settings import GLSetting
from globaleaks import __version__

def sleep(timeout):
    def callbackDeferred():
        d.callback(True)

    d = Deferred()
    reactor.callLater(timeout, callbackDeferred)
    return d

def sanitize_str(s):
    """
    This function encodes the following characters
    using HTML encoding: < > & ' " \ / 
    """
    s = cgi.escape(s, True)
    s = s.replace("'", "&#x2F;")
    s = s.replace("/", "&#47;")
    s = s.replace("\\", "&#92;")
    return s

class GLLogObserver(twlog.FileLogObserver):

    suppressed = 0
    limit_suppressed = 5

    event_list = []
    skipped = 0
    limit_skipped = 10

    def emit(self, eventDict):

        if 'failure' in eventDict:
            vf = eventDict['failure']
            e_t, e_v, e_tb = vf.type, vf.value, vf.getTracebackObject()
            sys.excepthook(e_t, e_v, e_tb)

        text = twlog.textFromEventDict(eventDict)
        if text is None:
            return

        timeStr = self.formatTime(eventDict['time'])
        fmtDict = {'system': eventDict['system'], 'text': text.replace("\n", "\n\t")}
        msgStr = twlog._safeFormat("[%(system)s] %(text)s\n", fmtDict)

        GLLogObserver.event_list.append(timeStr + " " + sanitize_str(msgStr))
        GLLogObserver.skipped += 1

        if GLLogObserver.suppressed == GLLogObserver.limit_suppressed:
            log.info("!! has been suppressed %d log lines" % GLLogObserver.limit_suppressed)
            GLLogObserver.suppressed = 0

        try:
            if GLLogObserver.skipped == GLLogObserver.limit_skipped:
                for string_logged in GLLogObserver.event_list:
                    util.untilConcludes(self.write, string_logged)

                util.untilConcludes(self.flush)
                GLLogObserver.skipped = 0
                GLLogObserver.event_list = []

            # util.untilConcludes(self.write, timeStr + " " + sanitize_str(msgStr))
            # util.untilConcludes(self.flush) # Hoorj!
        except Exception as excep:
            GLLogObserver.suppressed += 1
            pass


class Logger(object):
    """
    Customized LogPublisher
    """
    def _str(self, msg):
        if isinstance(msg, unicode):
            msg = msg.encode('utf-8')

        return str(msg)

    def exception(self, error):
        """
        Error can either be an error message to print to stdout and to the logfile
        or it can be a twisted.python.failure.Failure instance.
        """
        if isinstance(error, Failure):
            error.printTraceback()
        else:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            traceback.print_exception(exc_type, exc_value, exc_traceback)

    def info(self, msg):
        if GLSetting.loglevel <= logging.INFO:
            print "[-] %s" % self._str(msg)

    def err(self, msg):
        twlog.err("[!] %s" % self._str(msg))

    def debug(self, msg):
        if GLSetting.loglevel <= logging.DEBUG:
            print "[D] %s" % self._str(msg)

    def msg(self, msg):
        twlog.msg("[ ] %s" % self._str(msg))

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
            twlog.addObserver(GLLogObserver(logfile).emit)

log = Logger()

def query_yes_no(question, default="no"):
    """
    Ask a yes/no question via raw_input() and return their answer.

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
    total_len = 0

    with open(filepath, 'rb') as fp:
        while True:
            chunk = fp.read(chunk_size)
            if len(chunk) == 0:
                break
            total_len += len(chunk)
            sha.update(chunk)

    if not total_len:
        log.debug("checksum of %s computed, but the file is empty" % filepath)

    return ( sha.hexdigest(), total_len )

## time facilities ##

def utc_dynamic_date(start_date, seconds=0, minutes=0, hours=0):
    """
    @param start_date: a date stored in a db
    seconds/minutes/hours = the amount of future you want
    @return: a datetime object, as base of the sum
    """
    delta = timedelta(seconds=(seconds + (minutes * 60) + (hours * 3600)))
    return start_date + delta

def utc_future_date(seconds=0, minutes=0, hours=0):
    """
    @param seconds: get a datetime obj with now+hours
    @param minutes: get a datetime obj with now+minutes
    @param hours: get a datetime obj with now+seconds
    @return: a datetime object
    """
    delta = timedelta(seconds=(seconds + (minutes * 60) + (hours * 3600)))
    return datetime.utcnow() + delta

def datetime_null():
    """
    @return: a datetime object representing a null date
    """
    return datetime.fromtimestamp(0)

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

def very_pretty_date_time(isowhen):
    """
    print date used in email templating plugin/notification.py
    """
    x = datetime(year=int(isowhen[0:4]),
                 month=int(isowhen[5:7]),
                 day=int(isowhen[8:10]),
                 hour=int(isowhen[11:13]),
                 minute=int(isowhen[14:16]),
                 second=int(isowhen[17:19]) )

    return x.strftime("%H:%M, %A %d %B %Y")

def seconds_convert(value, conversion_factor, min=0, max=0):
    """
    @param value:
    @param conversion_factor:
    """
    seconds = value * conversion_factor

    if (seconds / conversion_factor) != value:
        raise Exception("Invalid operation triggered")
    if min and (seconds < min * conversion_factor):
        raise Exception("%d < %d" % (seconds, min * conversion_factor))
    if max and (seconds > max * conversion_factor):
        raise Exception("%d > %d" % (seconds, max * conversion_factor))

    return seconds

def iso2dateobj(str) :
    try:
        ret = datetime.strptime(str, "%Y-%m-%dT%H:%M:%S")
    except ValueError :
        ret = datetime.strptime(str, "%Y-%m-%dT%H:%M:%S.%f")
        ret.replace(microsecond=0)
    return ret

## Mail utilities ##

def sendmail(authentication_username, authentication_password, from_address,
             to_address, message_file, smtp_host, smtp_port, security, event=None):
    """
    Sends an email using SSLv3 over SMTP

    @param authentication_username: account username
    @param authentication_secret: account password
    @param from_address: the from address field of the email
    @param to_address: the to address field of the email
    @param message_file: the message content,
        string and unicode are converted in StringIO
    @param smtp_host: the smtp host
    @param smtp_port: the smtp port
    @param event: the event description, needed to keep track of failure/success
    """

    result_deferred = Deferred()

    def printError(reason, event):
        if isinstance(reason, Failure):
            reason = reason.type

        # XXX is catch a wrong TCP port, but not wrong SSL protocol, here
        if event:
            log.err("** failed notification within event %s" % event.type)
        # TODO Enhance with retry
        # TODO specify a ticket - make event an Obj instead of a namedtuple
        # TODO It's defined in plugin/base.py

        log.err("Failed to contact %s:%d (Sock Error %s)" %
                (smtp_host, smtp_port, reason))
        log.err(reason)

    def handle_error(reason, *args, **kwargs):
        printError(reason, event)
        return result_deferred.errback(reason)

    context_factory = ClientContextFactory()
    context_factory.method = SSL.SSLv3_METHOD

    if security != "SSL":
        requireTransportSecurity = True
    else:
        requireTransportSecurity = False

    esmtp_deferred = Deferred()
    esmtp_deferred.addErrback(handle_error, event)
    esmtp_deferred.addCallback(result_deferred.callback)

    if isinstance(message_file, cStringIO.InputType):
       pass
    elif isinstance(message_file, unicode) or isinstance(message_file, str):
        message_file = cStringIO.StringIO(str(message_file))
    else:
        log.err("Invalid usage of 'sendmail' function")
        raise AssertionError("message wrong type: %s" % type(message_file))

    factory = ESMTPSenderFactory(
        authentication_username,
        authentication_password,
        from_address,
        to_address,
        message_file,
        esmtp_deferred,
        contextFactory=context_factory,
        requireAuthentication=(authentication_username and authentication_password),
        requireTransportSecurity=requireTransportSecurity)

    def protocolConnectionLost(self, reason=protocol.connectionDone):
        """We are no longer connected"""
        if isinstance(reason, Failure):
            if not isinstance(reason.value, error.ConnectionDone):
                log.err("Failed to contact %s:%d (ConnectionLost Error %s)"
                        % (smtp_host, smtp_port, reason.type))
                log.err(reason)

        self.setTimeout(None)
        self.mailFile = None

    def sendError(self, exc):
        if exc.code and exc.resp:
            log.err("Failed to contact %s:%d (STMP Error: %.3d %s)"
                    % (smtp_host, smtp_port, exc.code, exc.resp))
        SMTPClient.sendError(self, exc)

    factory.protocol.sendError = sendError
    factory.protocol.connectionLost = protocolConnectionLost

    if security == "SSL":
        factory = tls.TLSMemoryBIOFactory(context_factory, True, factory)

    if GLSetting.tor_socks_enable:
        socksProxy = TCP4ClientEndpoint(reactor, GLSetting.socks_host, GLSetting.socks_port)
        endpoint = SOCKS5ClientEndpoint(smtp_host, smtp_port, socksProxy)
    else:
        endpoint = TCP4ClientEndpoint(reactor, smtp_host, smtp_port)

    d = endpoint.connect(factory)
    d.addErrback(handle_error, event)

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
        log.err("Exception unhandled inside generator")
        return

    mail_exception.mail_counter += 1

    exc_type = re.sub("(<(type|class ')|'exceptions.|'>|__main__.)",
                     "", str(etype))
    tmp = []

    tmp.append("From: \"%s\" <%s>" % (GLSetting.memory_copy.notif_source_name,
                                    GLSetting.memory_copy.notif_source_email) )
    tmp.append("To: %s" % GLSetting.memory_copy.exception_email)
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

    #if mail_exception.mail_counter > 30:
    #    log.debug("Exception not reported because exception counter > 30 (%d)" % mail_exception.mail_counter)
    #    log.debug("Anyway, that's your stacktrace: \n%s" % info_string )
    #    return # suppress every notification over the 30th

    if type(info_string) == unicode:
        info_string = info_string.encode(encoding='utf-8', errors='ignore')

    message = cStringIO.StringIO(info_string)

    log.err(error_message)
    log.err(traceinfo)
    log.debug("Exception Mail (%d):\n%s" % (mail_exception.mail_counter, info_string) )

    sendmail(authentication_username=GLSetting.memory_copy.notif_username,
             authentication_password=GLSetting.memory_copy.notif_password,
             from_address=GLSetting.memory_copy.notif_username,
             to_address=GLSetting.memory_copy.exception_email,
             message_file=message,
             smtp_host=GLSetting.memory_copy.notif_server,
             smtp_port=GLSetting.memory_copy.notif_port,
             security=GLSetting.memory_copy.notif_security)

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
        log.err("Invalid email address format [%s]" % mail_string)
        return False

    return unicode(mail_string)


def acquire_url_address(inputstring, hidden_service=False, http=False):

    accepted = False

    if hidden_service and re.match("^http://[0-9a-z]{16}\.onion$", inputstring):
        accepted |= True

    if http and re.match("^http(s?)://(\w+)\.(.*)$", inputstring):
        accepted |= True

    return accepted


def acquire_bool(boolvalue):

    if boolvalue == 'true' or boolvalue == u'true' or boolvalue == True:
        return True
    if boolvalue == 'false' or boolvalue == u'false' or boolvalue == False or boolvalue == None:
        return False

    raise AssertionError("BaseHandler validator is not working")

def l10n(var, language):
    if not var:
        return u''
    if language in var:
        return var[language]
    elif GLSetting.memory_copy.default_language in var:
        return var[GLSetting.memory_copy.default_language]
    elif len(var):
        return var.values()[0]
    else:
        return u''

def naturalize_fields(fields_blob):
    """
    @param fields_blob: the context fields
    @return: a dict of fields not related to the language.

    This function return the first fields blob available, between the
    various localized fields in context.fields.

    just return the first argument, because has been already validated
    by validate_and_fix_fields function in admin.py
    """
    assert isinstance(fields_blob, dict)
    assert len(set(fields_blob)) > 0

    naturalized_f = None
    for lang, fields in fields_blob.iteritems():
        if fields and not naturalized_f:
            naturalized_f = fields

    return naturalized_f


def caller_name(skip=2):
    """Get a name of a caller in the format module.class.method
    
       `skip` specifies how many levels of stack to skip while getting caller
       name. skip=1 means "who calls me", skip=2 "who calls my caller" etc.
       
       An empty string is returned if skipped levels exceed stack height
    """
    stack = inspect.stack()
    start = 0 + skip
    if len(stack) < start + 1:
      return ''
    parentframe = stack[start][0]    
    
    name = []
    module = inspect.getmodule(parentframe)
    # `modname` can be None when frame is executed directly in console
    # TODO(techtonik): consider using __main__
    if module:
        name.append(module.__name__)
    # detect classname
    if 'self' in parentframe.f_locals:
        # I don't know any way to detect call from the object method
        # XXX: there seems to be no way to detect static method call - it will
        #      be just a function call
        name.append(parentframe.f_locals['self'].__class__.__name__)
    codename = parentframe.f_code.co_name
    if codename != '<module>':  # top level usually
        name.append( codename ) # function or a method
    del parentframe
    return ".".join(name)
