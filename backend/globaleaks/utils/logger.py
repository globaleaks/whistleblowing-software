# -*- coding: UTF-8
#
#   logger
#   ******
#
# Log.admin( alarm_level=[$,$], code=$INT, args={'name':'stuff', 'other':'stuff'} )
#
# adminLog, receiverLog, tipLog are @classmethod, callable by any stuff in the world

from twisted.internet.defer import inlineCallbacks
from storm.expr import Desc

from globaleaks.utils.mailutils import MIME_mail_build, sendmail
from globaleaks.utils.utility import datetime_to_ISO8601, datetime_now
from globaleaks.settings import GLSettings, transact_ro, transact
from globaleaks.utils.utility import log
from globaleaks.models import Log

Login_messages = {
    # Admin
    'LOGIN_1' : [ "admin logged in the system", 0 ],
    'LOGIN_2' : [ "receiver %s logged in the system", 1 ],
    # Used for Receiver
    'LOGIN_20' : [ "you logged in the system", 0 ]
}

Tip_messages = {
    # Admin
    'TIP_0' : [ "submission has been created in context %s, %d recipients", 2],
    'TIP_1' : [ "submission delete and has never been accessed by receiver %s", 1],
    'TIP_2' : [ "submission expired and has never been accessed by receiver %s", 1],
    'TIP_3' : [ "tip deleted from context %s", 1],
    'TIP_4' : [ "tip expired from context %s", 1],
    # Receiver
    'TIP_20': [ "tip with label: %s deleted ", 1],
    'TIP_21': [ "tip delivered to you, in %s", 1],
    'TIP_22': [ "tip expired from %s, and never accessed by you", 1],
    'TIP_23': [ "tip deleted from %s (by %s), is never been accessed by you", 2],
    'TIP_24': [ "receiver %s extended expiration date", 1],
}

Security_messages  = {
    # Admin
    'SECURITY_0' : [ "system boot", 0],
    'SECURITY_1' : [ "wrong administrative password attempt password", 0],
    'SECURITY_2' : [ "wrong receiver (username %s) password attempt happened", 1],
    'SECURITY_3' : [ "bruteforce attack detected, invalid login in sequence (%d tries)", 1],
    # Receiver
    'SECURITY_20' : [ "wrong receiver password attempt happened", 0],
}

Network_messages = {
    # Admin
    'MAILFAIL_0' : [ "unable to deliver mail to %s: %s", 2],
    'MAIL_QUEUE_0' : [ "the queue of logged event that had to be mailed is longer than expected %d", 1],
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
def picklogs(store, subject_uuid, amount, filter_value):
    """
    by subject, pick the last Nth logs, request by paging.
    This may interact with database if required, but hopefully the
    default behavior is to access cache.
    """

    retval = {}
    try:
        memory_avail = LogQueue._all_queues[ subject_uuid ]

        for id, elem in memory_avail.iteritems():

            if filter_value != -1 and filter_value != elem.level:
                continue

            # if is == -1 ('all') or is equal to the request, we keep from memory
            retval.update({ id: elem })

        # Create the query used if the memory supply are not enough
        if filter_value == 1:
            db_query_rl = store.find(Log,
                                     Log.log_level == 1,
                                     Log.subject == unicode(subject_uuid))
        elif filter_value == 0:
            db_query_rl = store.find(Log,
                                     Log.log_level == 0,
                                     Log.subject == unicode(subject_uuid))
        else:
            db_query_rl = store.find(Log,
                                     Log.subject == unicode(subject_uuid))

        # The query is not executed
        if len(retval) < amount:
            db_query_rl.order_by(Desc(Log.id))
            recorded_l = db_query_rl[:(amount - len(retval.keys()))]

            for r in recorded_l:
                entry = LoggedEvent()
                entry.reload(r)
                retval.update({entry.id : entry})

    except KeyError:
        log.debug("Lacking of logs for %s in memory, checking from DB" % subject_uuid)
        pass

    if not subject_uuid in LogQueue._all_queues:
        LogQueue._all_queues.update({subject_uuid : {}})
    else:
        log.debug("From the memory cache, available %d entries for id %s" %
                  ( len(retval.values()), subject_uuid) )

    if filter_value == 1:
        db_query_rl = store.find(Log,
                                 Log.log_level == 1,
                                 Log.subject == unicode(subject_uuid))
    elif filter_value == 0:
        db_query_rl = store.find(Log,
                                 Log.log_level == 0,
                                 Log.subject == unicode(subject_uuid))
    else:
        db_query_rl = store.find(Log,
                                 Log.subject == unicode(subject_uuid))

    db_query_rl.order_by(Desc(Log.id))
    loglist = db_query_rl[:amount]

    for l in loglist:
        entry = LoggedEvent()
        # Reload, also, update the LogQueue
        entry.reload(l)
        retval.update({ entry.id : entry })

    # return only the values, not the IDs.
    # The IDs are just important to ensure uniqueness.
    log.debug("Returning %d entries from picklogs" % len(retval.values()))
    ascending = retval.values()
    ascending.reverse()
    return ascending # now, descending


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
        try:
            return {
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
        except KeyError:
            return {
                'log_code': self.log_code,
                # This "keyerror" switch can be removed when LOG_MSG_CODE are stable,
                # this error happen if in the DB there is something that do not exist
                # anymore. so, **REMIND**, the code can't be changed
                'msg': u'đđ ¿ LOST ¿ ðð',
                'args': self.args,
                'log_date': datetime_to_ISO8601(self.log_date),
                'subject': self.subject,
                'level': self.level,
                'mail': self.mail,
                'mail_sent': self.mail_sent,
                'id': self.id,
                'message': self.log_message
            }


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

        # Update the Queue, because after has to be still full
        LogQueue(self.subject).add(self.id, self)


    def create(self, log_info, subject, subject_id=None):

        if 'mail' in log_info['level']:
            self.mail = True
        else:
            self.mail = False

        self.level = 0
        # if is 'normal' just left the default value, 0

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
        return "Log %d lvl %d\t %s" % (self.id,self.level, self.log_message)



@transact
def mail_in_queue(store):
    """
    Take the events that has to be mailed and are not yet mailed.
    mark them as mailed NOW, this is inappropriate with our current design of
    mail_sent, but this require the creation of a dedicated Class inherit
    from EventLogger (notification_sched.py) and such kind of event require
    a receiver, and Log maybe is not intended for a Receiver, but for an admin.

    So, we need to refactor the EventLogger and generalize it for the Logs
    """
    retval = []
    tobemailed = store.find(Log, Log.mail_sent == False, Log.mail == True)
    for tbm in tobemailed:
        lobj = LoggedEvent()
        lobj.reload(tbm)
        tbm.mail_sent = True
        # This function can be slow if I associate also receiver serialized info,
        # and context info and such, because at the end we have to fill the mail template
        # and the information required to send the email
        log_infos = lobj.serialize_log()
        retval.append(log_infos)

    return retval



Temporarly_template = \
"""

Esteemed %UserName%,

The system of %NodeName% has an information to report you:

%MessageFromLog%

Best regards,
your faithful Log reporting system
"""


class LoggerNotification(object):
    """
    This class has only @staticmethod, can be moved easily, but I was not finding any needs to do
    a normal class/object or to do a list of method in this module.
    """

    @staticmethod
    # @inlineCallbacks
    def log_event_mail_generation(serialized_evnt):
        """
        This function take an event and send a priority email
        """

        admin_email = u'vecna@globaleaks.org'
        admin_language = u'en' # yield _get_admin_user_language()
        keyword = '%MessageFromLog%'
        notification_settings = dict(
            {
                'mail_title_for_user_logs': 'Info: %s' % keyword
            }) # yield get_notification(admin_language)

        message = Temporarly_template # yield _get_message_template()
        message_title = notification_settings['mail_title_for_user_logs']

        where = message.find(keyword)
        assert where != -1, "Invalid template body loaded ?"

        true_message = "%s%s%s" % (
            message[:where],
            serialized_evnt['message'],
            message[where + len(keyword):])

        where = message_title.find(keyword)
        assert where != -1, "Invalid template title loaded ?"

        true_title = "%s%s%s" % (
            message_title[:where],
            serialized_evnt['message'],
            message_title[where + len(keyword):])

        message = MIME_mail_build(GLSettings.memory_copy.notif_source_name,
                                  GLSettings.memory_copy.notif_source_email,
                                  admin_email,
                                  admin_email,
                                  true_title,
                                  true_message)

        # returnValue({
        return dict({
            'admin_email': admin_email,
            'message': message,
        })

    @staticmethod
    @inlineCallbacks
    def send_log_email(admin_email, message):
        yield sendmail(authentication_username=GLSettings.memory_copy.notif_username,
                       authentication_password=GLSettings.memory_copy.notif_password,
                       from_address=GLSettings.memory_copy.notif_username,
                       to_address=admin_email,
                       message_file=message,
                       smtp_host=GLSettings.memory_copy.notif_server,
                       smtp_port=GLSettings.memory_copy.notif_port,
                       security=GLSettings.memory_copy.notif_security,
                       event=None)


