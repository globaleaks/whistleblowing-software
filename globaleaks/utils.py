from datetime import datetime, timedelta
import logging

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
