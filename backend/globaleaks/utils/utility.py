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
import uuid
from datetime import datetime, timedelta

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.python import log as twlog
from twisted.python import logfile as twlogfile
from twisted.python import util
from twisted.python.failure import Failure

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.settings import GLSettings


def uuid4():
    """
    This function returns a uuid4.

    The function is not intended to be used for security reasons.
    """
    if len(GLSettings.debug_option_UUID_human) > 1:
        return huuid4()
    else:
        return unicode(uuid.uuid4())


def huuid4():
    """
    This function returns an incremental id following uuid4 format.

    http://www.ietf.org/rfc/rfc4122.txt

    The function is intended to be used only for debugging purposes.
    """
    GLSettings.debug_UUID_human_counter += 1

    str_padding = 8 - len(GLSettings.debug_option_UUID_human)
    int_padding = 12 - len("%d" % GLSettings.debug_UUID_human_counter)

    Huuidv4 = "%s%s-0000-0000-0000-%s%d" % (
        GLSettings.debug_option_UUID_human,
        str_padding * "0",
        int_padding * "0",
        GLSettings.debug_UUID_human_counter
    )

    return unicode(Huuidv4)


def sum_dicts(*dicts):
    ret = {}

    for d in dicts:
        for k, v in d.items():
            ret[k] = v

    return dict(ret)


def every_language(default_text):
    ret = {}

    for code in LANGUAGES_SUPPORTED_CODES:
        ret.update({code : default_text})

    return ret


def randint(start, end=None):
    if end is None:
        end = start
        start = 0
    w = end - start + 1
    return start + int(''.join("%x" % ord(x) for x in os.urandom(w)), 16) % w


def randbits(bits):
    return os.urandom(int(bits/8))


def choice(population):
    return population[randint(len(population)-1)]


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
    d = Deferred()

    def callbackDeferred():
        d.callback(True)

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
            unicodelogmsg = str(s).decode('utf-8')
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
        if GLSettings.loglevel and GLSettings.loglevel <= logging.INFO:
            print "[-] %s" % self._str(msg)

    def err(self, msg):
        if GLSettings.loglevel:
            twlog.err("[!] %s" % self._str(msg))

    def debug(self, msg):
        if GLSettings.loglevel and GLSettings.loglevel <= logging.DEBUG:
            print "[D] %s" % self._str(msg)

    def time_debug(self, msg):
        # read the command in settings.py near 'verbosity_dict'
        if GLSettings.loglevel and GLSettings.loglevel <= (logging.DEBUG - 1):
            print "[T] %s" % self._str(msg)

    def msg(self, msg):
        if GLSettings.loglevel:
            twlog.msg("[ ] %s" % self._str(msg))

    def start_logging(self):
        """
        If configured enables logserver
        """
        twlog.startLogging(sys.stdout)
        if GLSettings.logfile:
            name = os.path.basename(GLSettings.logfile)
            directory = os.path.dirname(GLSettings.logfile)

            logfile = twlogfile.LogFile(name, directory,
                                        rotateLength=GLSettings.log_file_size,
                                        maxRotatedFiles=GLSettings.maximum_rotated_log_files)
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

def time_now():
    """
    @return: current timestamp
    """
    now = time.time()

    if GLSettings.debug_option_in_the_future:
        now += timedelta(seconds=GLSettings.debug_option_in_the_future)

    return now


def datetime_null():
    """
    @return: a utc datetime object representing a null date
    """
    return datetime.utcfromtimestamp(0)


def datetime_now():
    """
    @return: a utc datetime object for the current time
    """
    now = datetime.utcnow()

    if GLSettings.debug_option_in_the_future:
        now += timedelta(seconds=GLSettings.debug_option_in_the_future)

    return now


def utc_dynamic_date(start_date, seconds=0, minutes=0, hours=0):
    """
    @param start_date: a date stored in a db
    seconds/minutes/hours = the amount of future you want
    @return: a datetime object, as base of the sum
    """
    return start_date + timedelta(seconds=(seconds + (minutes * 60) + (hours * 3600)))


def utc_past_date(seconds=0, minutes=0, hours=0):
    """
    @return a date in the past with the specified delta
    """
    return utc_dynamic_date(datetime_now()) - timedelta(seconds=(seconds + (minutes * 60) + (hours * 3600)))


def utc_future_date(seconds=0, minutes=0, hours=0):
    """
    @return a date in the future with the specified delta
    """
    return utc_dynamic_date(datetime_now(), seconds, minutes, hours)


def get_future_epoch(seconds=0):
    """
    @param seconds: optional, the second in the future
    @return: seconds since the Epoch
    """
    return int(time_now()) - time.timezone + seconds


def is_expired(check_date, seconds=0, minutes=0, hours=0, day=0):
    """
    @param check_date: a datetime or a timestap
    @param seconds, minutes, hours, day
        the time to live of the element
    @return:
        if now > check_date + (seconds+minutes+hours)
        True is returned, else False
    """
    if not check_date:
        return False

    total_hours = (day * 24) + hours
    check = check_date + timedelta(seconds=seconds, minutes=minutes, hours=total_hours)

    return datetime_now() > check


def datetime_to_ISO8601(date):
    """
    conver a datetime into ISO8601 date
    """
    if date is None:
        date = datetime_null()

    return date.isoformat() + "Z" # Z means that the date is in UTC


def ISO8601_to_datetime(isodate):
    """
    convert an ISO8601 date into a datetime
    """
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


def datetime_to_day_str(date):
    """
    print a datetime in DD/MM/YYYY formatted str
    """
    if date is None:
        date = datetime_null()

    return date.strftime("%d/%m/%Y")


def ISO8601_to_day_str(isodate, tz=0):
    """
    print a ISO8601 in DD/MM/YYYY formatted str
    """
    if isodate is None:
        isodate = datetime_null().isoformat()

    date = datetime(year=int(isodate[0:4]),
                    month=int(isodate[5:7]),
                    day=int(isodate[8:10]),
                    hour=int(isodate[11:13]),
                    minute=int(isodate[14:16]),
                    second=int(isodate[17:19]))

    if tz:
        tz_i, tz_d = divmod(tz, 1)
        tz_d, _  = divmod(tz_d * 100, 1)
        date += timedelta(hours=tz_i, minutes=tz_d)

    return date.strftime("%d/%m/%Y")


def ISO8601_to_pretty_str(isodate, tz=0):
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

    if tz:
        tz_i, tz_d = divmod(tz, 1)
        tz_d, _  = divmod(tz_d * 100, 1)
        date += timedelta(hours=tz_i, minutes=tz_d)
        return date.strftime("%A %d %B %Y %H:%M")

    return datetime_to_pretty_str(date)


def iso_year_start(iso_year):
    """Returns the gregorian calendar date of the first day of the given ISO year"""
    fourth_jan = datetime.strptime('{0}-01-04'.format(iso_year), '%Y-%m-%d')
    delta = timedelta(fourth_jan.isoweekday() - 1)
    return fourth_jan - delta


def iso_to_gregorian(iso_year, iso_week, iso_day):
    """Returns gregorian calendar date for the given ISO year, week and day"""
    year_start = iso_year_start(iso_year)
    return year_start + timedelta(days=iso_day - 1, weeks=iso_week - 1)


def bytes_to_pretty_str(b):
    if b is None:
        b = 0

    if isinstance(b, str):
        b = int(b)

    if b >= 1000000000:
        return "%dGB" % int(b / 1000000000)

    if b >= 1000000:
        return "%dMB" % int(b / 1000000)

    return "%dKB" % int(b / 1000)


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
