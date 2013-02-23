from datetime import datetime, timedelta
import logging

import re
import traceback

from OpenSSL import SSL
from StringIO import StringIO

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.mail.smtp import ESMTPSenderFactory
from twisted.internet.ssl import ClientContextFactory


from twisted.python import log as twlog
from Crypto.Random import random
from Crypto.Hash import SHA256
from twisted.internet import fdesc

from globaleaks import settings


class Publisher(twlog.LogPublisher):
    def info(self, *arg, **kw):
        kw['logLevel'] = logging.INFO
        return self.msg(*arg,**kw)

    def debug(self, *arg, **kw):
        kw['logLevel'] = logging.DEBUG
        return self.msg(*arg, **kw)

    def err(self, *arg, **kw):
        kw['logLevel'] = logging.ERROR
        return twlog.err(*arg, **kw)

    def startLogging(self):
        if settings.logfile:
            logfile_observer = twlog.FileLogObserver(open(settings.logfile, 'w'))
            self.addObserver(logfile_observer.emit)

        logpy_observer = twlog.PythonLoggingObserver('globaleaks')
        logpy_observer.logger.setLevel(settings.loglevel)
        self.addObserver(logpy_observer.emit)

log = Publisher()


## random facilities ##

def random_string(length, type):
    """
    Generates a random string of specified length and type.

    :length: the length of the random string
    :type: needs to be passed as comma separated ranges or values,
           ex. "a-z,A-Z,0-9".
    """
    def parse(type):
        choice_set = ''
        parsed = type.split(',')
        for item in parsed:
            chars = item.split('-')
            if len(chars) > 1:
                for chars in range(ord(chars[0]), ord(chars[1])):
                    choice_set += chr(chars)
            else:
                choice_set += chars[0]
        return choice_set

    choice_set = parse(type)
    res = ''.join(random.choice(choice_set)
                  for x in range(0, length))
    return res

def get_file_checksum(filepath):

    sha = SHA256.new()

    chunk_size = 8192

    with open(filepath, 'rb') as fd:

        fdesc.setNonBlocking(fd.fileno())
        while True:
            chunk = fd.read(chunk_size)
            if len(chunk) == 0:
                break
            sha.update(chunk)

    return sha.hexdigest()

## time facilities ##

def utcFutureDate(seconds=0, minutes=0, hours=0):
    """
    @param seconds: get a datetime obj with now+hours
    @param minutes: get a datetime obj with now+minutes
    @param hours: get a datetime obj with now+seconds
    @return: a datetime object
    """
    delta = (minutes * 60) + (hours * 3600) + seconds
    retTime = datetime.utcnow() + timedelta(seconds=delta)
    return retTime


def prettyDateTime(when):
    """
    @param when: a datetime like the stored DateTime in Storm
    @return: the pretty string
    """
    if when is None or when == 0:
        return "Never"
    else:
        return when.ctime()

def sendmail(authenticationUsername, authenticationSecret, fromAddress, toAddress, messageFile, smtpHost, smtpPort=25):
    """
    Sends an email using SSLv3 over SMTP

    @param authenticationUsername: account username
    @param authenticationSecret: account password
    @param fromAddress: the from address field of the email
    @param toAddress: the to address field of the email
    @param messageFile: the message content
    @param smtpHost: the smtp host
    @param smtpPort: the smtp port
    """
    contextFactory = ClientContextFactory()
    contextFactory.method = SSL.SSLv3_METHOD

    resultDeferred = Deferred()

    senderFactory = ESMTPSenderFactory(
        authenticationUsername,
        authenticationSecret,
        fromAddress,
        toAddress,
        messageFile,
        resultDeferred,
        contextFactory=contextFactory)

    reactor.connectTCP(smtpHost, smtpPort, senderFactory)

    return resultDeferred



def MailException(etype, value, tb):
    """
    Formats traceback and exception data and emails the error

    @param etype: Exception class type
    @param value: Exception string value
    @param tb: Traceback string data
    """
    excType = re.sub("(<(type|class ')|'exceptions.|'>|__main__.)", "", str(etype)).strip()
    tmp = []
    tmp.append("From: %s\n" % ("stackexception@globaleaks.org"))
    tmp.append("To: %s\n" % ("stackexception@lists.globaleaks.org"))
    tmp.append("Subject: GLBackend Exception\n")
    tmp.append("Content-Type: text/plain; charset=ISO-8859-1\n")
    tmp.append("Content-Transfer-Encoding: 8bit\n\n")
    tmp.append("%s %s" % (excType, etype.__doc__))
    for line in traceback.extract_tb(tb):
        tmp.append("\tFile: \"%s\"\n\t\t%s %s: %s\n" % (line[0], line[2], line[1], line[3]))
    while 1:
        if not tb.tb_next: break
        tb = tb.tb_next
    stack = []
    f = tb.tb_frame
    while f:
        stack.append(f)
        f = f.f_back
    stack.reverse()
    tmp.append("\nLocals by frame, innermost last:")
    for frame in stack:
        tmp.append("\nFrame %s in %s at line %s" % (frame.f_code.co_name, frame.f_code.co_filename, frame.f_lineno))
        for key, val in frame.f_locals.items():
            tmp.append("\n\t%20s = " % key)
            try:
                tmp.append(str(val))
            except:
                tmp.append("<ERROR WHILE PRINTING VALUE>")

    message = StringIO(''.join(tmp))

    sendmail("stackexception@globaleaks.org",
             "stackexception99",
             "stackexception@globaleaks.org",
             "stackexception@lists.globaleaks.org",
             message,
             "box549.bluehost.com",
             25)
