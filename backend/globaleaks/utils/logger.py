# -*- coding: UTF-8
#
#   logger
#   ******
#
# Log.admin( alarm_level=[$,$], code=$INT, args={'name':'stuff', 'other':'stuff'} )
#
# adminLog, receiverLog, tipLog are @classmethod, callable by any stuff in the world

import cgi
import codecs
import logging
import os
import sys
import traceback

from twisted.python import log as twlog
from twisted.python import logfile as twlogfile
from twisted.python import util
from twisted.python.failure import Failure
from storm.expr import Desc

from globaleaks.utils.utility import datetime_to_ISO8601, datetime_now
from globaleaks.settings import GLSettings, transact_ro
from globaleaks.utils.utility import log
from globaleaks.models import Log

Login_messages = {
    # Admin
    'LOGIN_1' : [ "admin logged in the system", 0 ],
    'LOGIN_2' : [ "receiver %s logged in the system", 1 ],
    # Used for Receiver
    'LOGIN_3' : [ "you logged in the system", 0 ]
}

Tip_messages = {
    # Admin
    'TIP_0' : [ "submission has been created in context %s", 1],
    'TIP_1' : [ "submission is going to expire and has never been accessed by receiver %s", 1 ],
    'TIP_2' : [ "tip deleted from context %s (%s)", 2],
    # Receiver
    'TIP_20': [ "tip with label: %s deleted ", 1],
    'TIP_21': [ "tip delivered to you, in %s", 1],
    'TIP_22': [ "tip deleted from %s, is never been accessed by you", 1],
}

Security_messages  = {
    # Admin
    'SECURITY_0' : [ "system boot", 0],
    # Receiver
    'SECURITY_20' : [ "someone has put a wrong password in the login interface", 0 ],
}

Network_messages = {
    # Admin
    'MAILFAIL_0' : [ "unable to deliver mail to %s: %s", 2]
}


_LOG_CODE = {}
_LOG_CODE.update(Login_messages)
_LOG_CODE.update(Tip_messages)
_LOG_CODE.update(Security_messages)
_LOG_CODE.update(Network_messages)


def _log_parameter_check(alarm_level, code, args):
    """
    This function is intended to verify that the GlobaLeaks developer
    is not making mistakes. Checks the integrity of the log data

    :param alarm_level: list or keyword between 'normal', 'warning', 'mail'
    :param code: a unique string identifier of the EventHappened
    :param args: list of argument.

    :return: No return, or AssertionError
    """
    acceptable_level = ['normal', 'warning', 'mail']

    if isinstance(alarm_level, list):
        for al in alarm_level:
            assert al in acceptable_level, \
                "%s not in %s" % (al, acceptable_level)
    else:
        assert alarm_level in acceptable_level, \
            "%s not in %s" % (alarm_level, acceptable_level)

    assert code in _LOG_CODE, "Log Code %s is not implemented" % code

    assert isinstance(args, list), "Expected a list as argument, not %s" % type(args)
    assert len(args) == _LOG_CODE[code][1], "Invalid number of arguments, expected %d got %d" % (
        _LOG_CODE[code][1], len(args)
    )


def adminLog(alarm_level, code, args):
    _log_parameter_check(alarm_level, code, args)
    LoggedEvent().create({
        'code' : code,
        'args' : args,
        'level': alarm_level,
    }, subject='admin')

def receiverLog(alarm_level, code, args, user_id):
    _log_parameter_check(alarm_level, code, args)
    LoggedEvent().create({
        'code' : code,
        'args' : args,
        'level': alarm_level
    }, subject='receiver', subject_id=user_id)

def tipLog(alarm_level, code, args, tip_id):
    _log_parameter_check(alarm_level, code, args)
    LoggedEvent().create({
        'code' : code,
        'args' : args,
        'level': alarm_level
    }, subject='itip', subject_id=tip_id)


class LogQueue(object):

    _all_queues = {}

    def __init__(self, subject_uuid):

        if subject_uuid in LogQueue._all_queues:
            # The queue already exists
            pass
        else:
            LogQueue._all_queues.update({
                subject_uuid : {}
            })
        self.subject_uuid = subject_uuid


    @classmethod
    def create_subject_uuid(cls, subject, subject_id):
        """
        Just create the unique key used in the LogQueue._all_queues dictionary,
        in order to keep the log of a specific user/role/tip.
        """
        if subject == 'receiver':
            subject_uuid = unicode("receiver_%s" % subject_id)
        elif subject == 'itip':
            subject_uuid = unicode("itip_%s" % subject_id)
        elif subject == 'admin':
            subject_uuid = unicode("admin")
        else:
            raise Exception("Invalid condition %s" % subject)

        return subject_uuid


    def add(self, log_id, logentry):
        LogQueue._all_queues[ self.subject_uuid ].update(
            {log_id : logentry})


    @classmethod
    def is_present(cls, subject_uuid, id):

        try:
            return id in LogQueue._all_queues[ subject_uuid ]
        except KeyError:
            return False




@transact_ro
def picklogs(store, subject_uuid, amount):
    """
    by subject, pick the last Nth logs, request by paging.
    This may interact with database if required, but hopefully the
    default behavior is to access cache.
    """

    try:
        subject_dict = LogQueue._all_queues[ subject_uuid ]
        # [last, last-1, last-2]
        x = subject_dict.values()
        # In this way, we are taking the first (the last, in LIFO) logs in queue
        retval = x[:amount] if len(x) > amount else x

        least_id = subject_dict.keys()[-1]

        if len(retval) < amount:
            db_query_rl = store.find(Log, Log.subject == unicode(subject_uuid), Log.id < least_id)
            db_query_rl.order_by(Desc(Log.id))
            recorded_l = db_query_rl[:(amount - len(retval))]

            for r in recorded_l:
                entry = LoggedEvent()
                entry.reload(r)
                retval.append(entry)

    except KeyError:
        LogQueue._all_queues.update({subject_uuid : {}})
        retval = []

        retrieved = store.find(Log, Log.subject == unicode(subject_uuid))
        retrieved.order_by(Desc(Log.id))
        loglist = retrieved[:amount]

        for l in loglist:
            entry = LoggedEvent()
            entry.reload(l)
            retval.append(entry)

    return retval


@transact_ro
def initialize_LoggedEvent(store):

    if not LoggedEvent._incremental_id:
        last_log = store.find(Log)
        last_log.order_by(Desc(Log.id))
        if last_log.count() > 0:
            x = last_log[0]
            LoggedEvent._incremental_id = x.id
        else:
            LoggedEvent._incremental_id = 1

    log.debug("Restarting of Log framework, since ID %d" % LoggedEvent._incremental_id)
    return LoggedEvent._incremental_id



class LoggedEvent(object):
    """
    This is the Logged Event we keep in memory, in order to keep track of the latest
    event, and optimize repeated event printing.
    """
    _incremental_id = 0

    @classmethod
    def get_unique_log_id(cls):

        assert LoggedEvent._incremental_id, "Missing initialization of _incremental_id!"
        LoggedEvent._incremental_id += 1
        return LoggedEvent._incremental_id


    def serialize_log(self):
        log_dict = {
            'log_code': self.log_code,
            'msg': _LOG_CODE[self.log_code][0],
            'args': self.args,
            'log_date': datetime_to_ISO8601(self.log_date),
            'subject': self.subject,
            'level': self.level,
            'mail': self.mail,
            'mail_sent': self.mail_sent,
            'id': self.id,
            'message': self.log_message
        }
        return log_dict

    def match(self, code, args):
        """
        Clean this things, this is just for pdb
        """
        if not self.log_code == code:
            return False

        if not self.args == args:
            return False

        return True

    def __init__(self):

        self.id = 0


    def reload(self, storm_Log_entry):

        self.id = storm_Log_entry.id
        self.log_code = storm_Log_entry.code
        self.args = storm_Log_entry.args
        self.subject = storm_Log_entry.subject
        self.mail = storm_Log_entry.mail
        self.mail_sent = storm_Log_entry.mail_sent
        self.level = storm_Log_entry.log_level
        self.log_date = storm_Log_entry.log_date
        self.log_message = storm_Log_entry.log_message

        LogQueue(self.subject).add(self.id, self)


    def create(self, log_info, subject, subject_id=None):

        if 'mail' in log_info['level']:
            self.mail = True
        else:
            self.mail = False

        self.level = 1
        # if is 'normal' just left the default value, 1

        if 'warning' in log_info['level']:
            self.level = 1

        if 'debug' in log_info['level']:
            self.level = 0

        self.mail_sent = False
        self.id = LoggedEvent.get_unique_log_id()
        self.log_code = log_info['code']
        self.args = log_info['args']
        self.log_date = datetime_now()

        subject_uuid = LogQueue.create_subject_uuid(subject, subject_id)
        self.subject = subject_uuid

        if len(self.args) == 0:
            assert 0 == _LOG_CODE[ self.log_code ][1]
            log_str = _LOG_CODE[ self.log_code][0]
        elif len(self.args) == 1:
            assert 1 == _LOG_CODE[ self.log_code ][1]
            log_str = (_LOG_CODE[ self.log_code][0] % self.args[0] )
        elif len(self.args) == 2:
            assert 2 == _LOG_CODE[ self.log_code ][1]
            log_str = (_LOG_CODE[ self.log_code][0] % (self.args[0], self.args[1])  )
        else:
            raise Exception("!!?")

        log.debug("Log of: [%s]" % log_str)
        self.log_message = unicode(log_str)

        LogQueue(subject_uuid).add(self.id, self)

    def __repr__(self):
        return "Log ID %d" % self.id


########## copied from utility.py to put all the log related function here
########## They has to be updated anyway


def log_encode_html(s):
    """
    This function encodes the following characters
    using HTML encoding: < > & ' " \ /

    This function has been suggested for security reason by an old PT, and
    make senses only if the Log can be influenced by external means. now with the
    new logging structure, only the "arguments" has to be escaped, not all the line in
    the logfile.
    """
    s = cgi.escape(s, True)
    s = s.replace("'", "&#39;")
    s = s.replace("/", "&#47;")
    s = s.replace("\\", "&#92;")
    return s

def log_remove_escapes(s):
    """
    This function removes escape sequence from log strings, read the comment in the function above
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

            ##### log.info("!! has been suppressed %d log lines due to error flood (last error %s)" %
            #####          (GLLogObserver.limit_suppressed, GLLogObserver.last_exception_msg) )

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

