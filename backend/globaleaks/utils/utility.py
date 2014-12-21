# -*- coding: UTF-8
#   utility
#   *******
#
# GlobaLeaks Utility Functions

import cgi
import codecs
import inspect
import logging
import os
import sys
import time
import traceback
from uuid import UUID
from datetime import datetime, timedelta

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.python import log as twlog
from twisted.python import logfile as twlogfile
from twisted.python import util
from twisted.python.failure import Failure

from globaleaks.settings import GLSetting

def uuid4():
    """
    This function returns a secure random uuid4 as
    defined by http://www.ietf.org/rfc/rfc4122.txt

    r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})
    this is the regexp that has to be matched, and if a special
    debug option is enabled here, the UUIDv4 is not randomic
    """
    if len(GLSetting.debug_option_UUID_human) > 1:

        GLSetting.debug_UUID_human_counter += 1
        str_padding = 8 - len(GLSetting.debug_option_UUID_human)
        int_padding = 12 - len("%d" % GLSetting.debug_UUID_human_counter)

        Huuidv4 = "%s%s-0000-0000-0000-%s%d" % (
            GLSetting.debug_option_UUID_human,
            str_padding * "0",
            int_padding * "0",
            GLSetting.debug_UUID_human_counter
        )
        return unicode(Huuidv4)
    else:
        return unicode(UUID(bytes=os.urandom(16), version=4))


def randint(start, end=None):
    if not end:
        end = start
        start = 0
    w = end - start + 1
    return start + int(''.join("%x" % ord(x) for x in os.urandom(w)), 16) % w

def randbits(bits):
    return os.urandom(int(bits/8))

def choice(population):
    size = len(population)
    return population[randint(size-1)]

def shuffle(x):
    for i in reversed(xrange(1, len(x))):
        j = randint(0, i)
        x[i], x[j] = x[j], x[i]
    return x

def deferred_sleep(timeout):
    """
    @param timeout: this sleep is called to slow down bruteforce attacks
    @return:
    """
    def callbackDeferred():
        d.callback(True)

    d = Deferred()
    reactor.callLater(timeout, callbackDeferred)
    return d

def log_encode_html(s):
    """
    This function encodes the following characters
    using HTML encoding: < > & ' " \ / 
    """
    s = cgi.escape(s, True)
    s = s.replace("'", "&#39;")
    s = s.replace("/", "&#47;")
    s = s.replace("\\", "&#92;")
    return s

def log_remove_escapes(s):
    """
    This function removes escape sequence from log strings
    """
    if isinstance(s, unicode):
        return codecs.encode(s, 'unicode_escape')
    else:
        try:
            s = str(s)
            unicodelogmsg = s.decode('utf-8')
        except UnicodeDecodeError:
            return codecs.encode(s, 'string_escape')
        except Exception as e:
            return "Failure in log_remove_escapes %r" % e
        else:
            return codecs.encode(unicodelogmsg, 'unicode_escape')

class GLLogObserver(twlog.FileLogObserver):

    suppressed = 0
    limit_suppressed = 1
    last_exception_msg = ""

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

        if GLLogObserver.suppressed == GLLogObserver.limit_suppressed:
            # This code path flush the status of the broken log, in the case a flood is happen
            # for few moment or in the case something goes wrong when logging below.
            log.info("!! has been suppressed %d log lines due to error flood (last error %s)" %
                     (GLLogObserver.limit_suppressed, GLLogObserver.last_exception_msg) )

            GLLogObserver.suppressed = 0
            GLLogObserver.limit_suppressed += 5
            GLLogObserver.last_exception_msg = ""

        try:
            # in addition to escape sequence removal on logfiles we also quote html chars
            util.untilConcludes(self.write, timeStr + " " + log_encode_html(msgStr))
            util.untilConcludes(self.flush) # Hoorj!
        except Exception as excep:
            GLLogObserver.suppressed += 1
            GLLogObserver.last_exception_msg = str(excep)


class Logger(object):
    """
    Customized LogPublisher
    """
    def _str(self, msg):
        if isinstance(msg, unicode):
            msg = msg.encode('utf-8')

        return log_remove_escapes(msg)

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
        if GLSetting.loglevel and GLSetting.loglevel <= logging.INFO:
            print "[-] %s" % self._str(msg)

    def err(self, msg):
        if GLSetting.loglevel:
            twlog.err("[!] %s" % self._str(msg))

    def debug(self, msg):
        if GLSetting.loglevel and GLSetting.loglevel <= logging.DEBUG:
            print "[D] %s" % self._str(msg)

    def msg(self, msg):
        if GLSetting.loglevel:
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
    if default is None:
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

## time facilities ##

def datetime_null():
    """
    @return: a utc datetime object representing a null date
    """
    return datetime.utcfromtimestamp(0)

def datetime_now():
    """
    @return: a utc datetime object of now and eventually incremented
             of a certain amount of seconds if the Node is running with --XXX option
    """
    now = datetime.utcnow()

    if GLSetting.debug_option_in_the_future:
        now += timedelta(seconds=GLSetting.debug_option_in_the_future)

    return now

def utc_dynamic_date(start_date, seconds=0, minutes=0, hours=0):
    """
    @param start_date: a date stored in a db
    seconds/minutes/hours = the amount of future you want
    @return: a datetime object, as base of the sum
    """
    return start_date + timedelta(seconds=(seconds + (minutes * 60) + (hours * 3600)))

def utc_future_date(seconds=0, minutes=0, hours=0):
    """
    @param seconds: get a datetime obj with now+hours
    @param minutes: get a datetime obj with now+minutes
    @param hours: get a datetime obj with now+seconds
    @return: a datetime object
        Eventually is incremented of a certain amount of seconds
        if the Node is running with --XXX option
    """
    now = datetime.utcnow()

    if GLSetting.debug_option_in_the_future:
        now += timedelta(seconds=GLSetting.debug_option_in_the_future)

    return utc_dynamic_date(now, seconds, minutes, hours)

def get_future_epoch(seconds=0):
    """
    @param seconds: optional, the second in
        the future
    @return: seconds since the Epoch
        This future data is eventually incremented of the
        amount of seconds specified in --XXX option
    """
    basic_future = int(time.time()) - time.timezone + seconds

    if GLSetting.debug_option_in_the_future:
        basic_future += GLSetting.debug_option_in_the_future

    return basic_future

def is_expired(check_date, seconds=0, minutes=0, hours=0, day=0):
    """
    @param check_date: a datetime or a timestap
    @param seconds, minutes, hours, day
        the time to live of the element
    @return:
        if now > check_date + (seconds+minutes+hours)
        True is returned, else False

        Eventually is incremented of a certain amount of seconds
        if the Node is running with --XXX option
    """
    if not check_date:
        return False

    total_hours = (day * 24) + hours
    check = check_date + timedelta(seconds=seconds, minutes=minutes, hours=total_hours)
    now = datetime_now()

    if GLSetting.debug_option_in_the_future:
        now += timedelta(seconds=GLSetting.debug_option_in_the_future)

    return now > check

def datetime_to_ISO8601(date):
    """
    conver a datetime in ISO8601 format and UTC timezone
    """
    if date is None:
        date = datetime_null()

    return date.isoformat() + "Z" # Z means that the date is in UTC

def ISO8601_to_datetime(isodate):

    isodate = isodate[:19] # we srip the eventual Z at the end

    try:
        ret = datetime.strptime(isodate, "%Y-%m-%dT%H:%M:%S")
    except ValueError :
        ret = datetime.strptime(isodate, "%Y-%m-%dT%H:%M:%S.%f")
        ret.replace(microsecond=0)
    return ret

def datetime_to_pretty_str(date):
    """
    print a datetime in pretty formatted str format
    """
    if date is None:
        date = datetime_null()

    return date.strftime("%A %d %B %Y %H:%M (UTC)")

def ISO8601_to_pretty_str(isodate):
    """
    convert a ISO8601 in pretty formatted str format
    """
    if isodate is None:
        isodate = datetime_null().isoformat()
 
    date = datetime(year=int(isodate[0:4]),
                    month=int(isodate[5:7]),
                    day=int(isodate[8:10]),
                    hour=int(isodate[11:13]),
                    minute=int(isodate[14:16]),
                    second=int(isodate[17:19]) )

    return datetime_to_pretty_str(date)

def datetime_to_pretty_str_tz(date):
    """
    print a datetime in pretty formatted str format
    """
    if date is None:
        date = datetime_null()

    return date.strftime("%A %d %B %Y %H:%M")

def ISO8601_to_pretty_str_tz(isodate, tz):
    """
    convert a ISO8601 in pretty formatted str format
    """
    if isodate is None:
        isodate = datetime_null().isoformat()

    date = datetime(year=int(isodate[0:4]),
                    month=int(isodate[5:7]),
                    day=int(isodate[8:10]),
                    hour=int(isodate[11:13]),
                    minute=int(isodate[14:16]),
                    second=int(isodate[17:19]) )

    tz_i, tz_d = divmod(tz, 1)
    tz_d, _  = divmod(tz_d * 100, 1)

    date += timedelta(hours=tz_i, minutes=tz_d)

    return datetime_to_pretty_str_tz(date)

def seconds_convert(value, conversion_factor, minv=0, maxv=0):
    """
    @param value:
    @param conversion_factor:
    """
    seconds = value * conversion_factor

    if (seconds / conversion_factor) != value:
        raise Exception("Invalid operation triggered")
    if minv and (seconds < minv * conversion_factor):
        raise Exception("%d < %d" % (seconds, minv * conversion_factor))
    if maxv and (seconds > maxv * conversion_factor):
        raise Exception("%d > %d" % (seconds, maxv * conversion_factor))

    return seconds

def acquire_bool(boolvalue):
    if boolvalue == 'true' or boolvalue == u'true' or boolvalue == True:
        return True

    return False

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

# Dumping utility

def dump_submission_steps(wb_steps):

    dumptext = u"FIELD_MAIL_DUMP_STILL_NEED_TO_BE_IMPLEMENTED"

    return dumptext

def dump_file_list(filelist, files_n):

    info = "%s%s%s\n" % ("Filename",
                             " "*(40-len("Filename")),
                             "Size (Bytes)")

    for i in xrange(files_n):
        info += "%s%s%i\n" % (filelist[i]['name'],
                                " "*(40 - len(filelist[i]['name'])),
                                filelist[i]['size'])

    return info
