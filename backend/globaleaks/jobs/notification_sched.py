# -*- encoding: utf-8 -*-
#
#   notification_sched
#   ******************
#
# Notification implementation, documented along the others asynchronous
# operations, in Architecture and in jobs/README.md

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.jobs.base import GLJob
from globaleaks.handlers import admin, rtip
from globaleaks.handlers.submission import db_serialize_questionnaire_answers, \
    db_get_archived_questionnaire_schema
from globaleaks.plugins.base import Event
from globaleaks.settings import transact, GLSettings
from globaleaks.utils.utility import log, datetime_to_ISO8601
from globaleaks.models import EventLogs
from globaleaks.anomaly import Alarm


def serialize_receivertip(store, rtip, language):
    rtip_dict = {
        'id': rtip.id,
        'creation_date': datetime_to_ISO8601(rtip.internaltip.creation_date),
        'last_access': datetime_to_ISO8601(rtip.last_access),
        'access_counter': rtip.access_counter,
        'questionnaire': db_get_archived_questionnaire_schema(store, rtip.internaltip.questionnaire_hash, language),
        'answers': db_serialize_questionnaire_answers(store, rtip.internaltip),
        'context_id': rtip.internaltip.context.id,
        'expiration_date': datetime_to_ISO8601(rtip.internaltip.expiration_date)
    }

    return rtip_dict


def serialize_internalfile(ifile, rfile_id):
    """
    :param ifile: store InternalFile
    :param rfile_id: ReceiverFile.id, to keep track
    """
    rfile_dict = {
        'receiverfile_id': rfile_id,
        'name': ifile.name,
        'content_type': ifile.content_type,
        'size': ifile.size,
        'creation_date': datetime_to_ISO8601(ifile.creation_date),
    }

    return rfile_dict


def db_save_events_on_db(store, event_list):
    for evnt in event_list:
        e = EventLogs()

        e.description = {
            'receiver_info': evnt.receiver_info,
            'context_info': evnt.context_info,
            'tip_info': evnt.tip_info,
            'subevent_info': evnt.subevent_info,
            'type': evnt.type,
        }

        e.event_reference = {
            'kind': evnt.trigger
        }

        e.title = evnt.trigger
        e.receiver_id = evnt.receiver_info['id']
        e.receivertip_id = evnt.tip_info['id']
        e.mail_sent = False

        store.add(e)


class EventLogger(object):
    trigger = '[undefined]'

    def __init__(self):
        self.events = []
        self.language = GLSettings.defaults.language

    def import_receiver(self, receiver):
        self.language = receiver.user.language

        if self.trigger == 'Message':
            self.template_type = u'message'
        elif self.trigger == 'Tip':
            self.template_type = u'tip'
        elif self.trigger == 'Comment':
            self.template_type = u'comment'
        elif self.trigger == 'File':
            self.template_type = u'file'
        elif self.trigger == 'ExpiringTip':
            self.template_type = u'upcoming_tip_expiration'
        else:
            raise Exception("self.trigger of unexpected kind ? %s" % self.trigger)

        receiver_desc = admin.receiver.admin_serialize_receiver(receiver, self.language)

        return (receiver.tip_notification, receiver_desc)

    def process_event(self, store, elem):
        pass

    @transact
    def process_events(self, store):
        """
        :return:
            0  = No event has been processed
           -1  = Threshold reach, emergency mode.
           >0  = Some elements to be notified has been processed
        """

        _elemscount = store.find(self.model, self.model.new == True).count()

        if _elemscount > (GLSettings.jobs_operation_limit * 10):
            # If this situation happen, we are facing a shitload of problem.
            # The reasonable option is that the entire Notification get skipped for this specific Trigger
            # all the events are marked as "new = False" and "chi si è visto si è visto"!
            # plus, the Admin get notified about it with an email.
            log.err("Waves of new %s received, notification suspended completely for all the %d %s (Threshold %d)" %
                     ( self.trigger, _elemscount,
                       self.trigger, (GLSettings.jobs_operation_limit * 10) ))
            store.find(self.model, self.model.new == True).set(new=False)
            return -1

        _elems = store.find(self.model, self.model.new == True)[:GLSettings.jobs_operation_limit]

        if _elemscount > GLSettings.jobs_operation_limit:
            log.info("Notification: Processing %d new event from a Queue of %d: %s(s) to be handled" %
                      (_elems.count(), _elemscount, self.trigger))
        elif _elemscount:
            log.debug("Notification: Processing %d new event: %s(s) to be handled" %
                      (_elems.count(), self.trigger))
        else:
            # No element to be processed
            return 0

        for e in _elems:
            # Mark event as handled as first step;
            # For resiliency reasons it's better to be sure that the
            # state machine move forward, than having starving events
            # due to possible exceptions in handling
            e.new = False
            self.process_event(store, e)

        db_save_events_on_db(store, self.events)
        log.debug("Notification: generated %d notification events of type %s" %
                  (len(self.events), self.trigger))

        return _elems.count()


class TipEventLogger(EventLogger):
    trigger = 'Tip'
    model = models.ReceiverTip

    def process_event(self, store, rtip):
        tip_desc = serialize_receivertip(store, rtip, self.language)

        context_desc = admin.context.admin_serialize_context(store,
                                                             rtip.internaltip.context,
                                                             self.language)

        do_mail, receiver_desc = self.import_receiver(rtip.receiver)

        self.events.append(Event(type=self.template_type,
                                 trigger=self.trigger,
                                 node_info={},
                                 receiver_info=receiver_desc,
                                 context_info=context_desc,
                                 tip_info=tip_desc,
                                 subevent_info={},
                                 do_mail=do_mail))


class MessageEventLogger(EventLogger):
    trigger = 'Message'
    model = models.Message

    def process_event(self, store, message):
        message_desc = rtip.serialize_message(message)

        # message.type can be 'receiver' or 'wb' at the moment, we care of the latter
        if message.type == u"receiver":
            return

        tip_desc = serialize_receivertip(store, message.receivertip, self.language)

        context_desc = admin.context.admin_serialize_context(store,
                                                             message.receivertip.internaltip.context,
                                                             self.language)

        do_mail, receiver_desc = self.import_receiver(message.receivertip.receiver)

        self.events.append(Event(type=self.template_type,
                                 trigger=self.trigger,
                                 node_info={},
                                 receiver_info=receiver_desc,
                                 context_info=context_desc,
                                 tip_info=tip_desc,
                                 subevent_info=message_desc,
                                 do_mail=do_mail))


class CommentEventLogger(EventLogger):
    trigger = 'Comment'
    model = models.Comment

    def process_event(self, store, comment):
        comment_desc = rtip.serialize_comment(comment)

        context_desc = admin.context.admin_serialize_context(store,
                                                             comment.internaltip.context,
                                                             self.language)

        # for every comment, iterate on the associated receiver(s)
        log.debug("Comments from %s - Receiver(s) %d" % \
                  (comment.author, comment.internaltip.receivers.count()))

        for receiver in comment.internaltip.receivers:
            if comment.type == u'receiver' and comment.author == receiver.user.name:
                log.debug("Receiver is the Author (%s): skipped" % receiver.user.username)
                return

            receivertip = store.find(models.ReceiverTip,
                                     (models.ReceiverTip.internaltip_id == comment.internaltip_id,
                                      models.ReceiverTip.receiver_id == receiver.id)).one()

            tip_desc = serialize_receivertip(store, receivertip, self.language)

            do_mail, receiver_desc = self.import_receiver(receiver)

            self.events.append(Event(type=self.template_type,
                                     trigger=self.trigger,
                                     node_info={},
                                     receiver_info=receiver_desc,
                                     context_info=context_desc,
                                     tip_info=tip_desc,
                                     subevent_info=comment_desc,
                                     do_mail=do_mail))


class FileEventLogger(EventLogger):
    trigger = 'File'
    model = models.ReceiverFile

    def process_event(self, store, rfile):
        context_desc = admin.context.admin_serialize_context(store,
                                                             rfile.internalfile.internaltip.context,
                                                             self.language)

        tip_desc = serialize_receivertip(store, rfile.receivertip, self.language)
        file_desc = serialize_internalfile(rfile.internalfile, rfile.id)
        do_mail, receiver_desc = self.import_receiver(rfile.receiver)

        self.events.append(Event(type=self.template_type,
                                 trigger=self.trigger,
                                 node_info={},
                                 receiver_info=receiver_desc,
                                 context_info=context_desc,
                                 tip_info=tip_desc,
                                 subevent_info=file_desc,
                                 do_mail=do_mail))


class NotificationSchedule(GLJob):
    name = "Notification"

    @inlineCallbacks
    def operation(self):
        tip_mngd = yield TipEventLogger().process_events()
        if tip_mngd == -1:
            Alarm.stress_levels['notification'].append('Tip')

        comment_mngd = yield CommentEventLogger().process_events()
        if comment_mngd == -1:
            Alarm.stress_levels['notification'].append('Comment')

        messages_mngd = yield MessageEventLogger().process_events()
        if messages_mngd == -1:
            Alarm.stress_levels['notification'].append('Message')

        file_mngs = yield FileEventLogger().process_events()
        if file_mngs == -1:
            Alarm.stress_levels['notification'].append('File')



