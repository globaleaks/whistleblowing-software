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
from globaleaks.plugins.base import Event
from globaleaks.settings import transact, GLSetting
from globaleaks.utils.utility import log, datetime_to_ISO8601
from globaleaks.models import EventLogs


def serialize_receivertip(receivertip):
    rtip_dict = {
        'id': receivertip.id,
        'creation_date': datetime_to_ISO8601(receivertip.creation_date),
        'last_access': datetime_to_ISO8601(receivertip.last_access),
        'access_counter': receivertip.access_counter,
        'wb_steps': receivertip.internaltip.wb_steps,
        'context_id': receivertip.internaltip.context.id,
        'expiration_date': datetime_to_ISO8601(receivertip.internaltip.expiration_date),
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
            'steps_info': evnt.steps_info,
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


@transact
def save_events_on_db(store, event_list):
    return db_save_events_on_db(store, event_list)


class EventLogger(object):
    trigger = '[undefined]'

    def __init__(self):
        self.events = []
        self.language = GLSetting.defaults.language

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

        receiver_desc = admin.admin_serialize_receiver(receiver, self.language)

        return (receiver.tip_notification, receiver_desc)

    def process_event(self, store, elem):
        pass

    @transact
    def process_events(self, store):
        _elems = store.find(self.model, self.model.new == True)

        if not _elems.count():
            return

        log.debug("Notification: found %d %s(s) to be handled" %
                  (_elems.count(), self.trigger))

        for e in _elems:
            # Mark event as handled as first step;
            # For resiliency reasons it's better to be sure that the
            # state machine move forward, than having starving events
            # due to possible exceptions in handling
            e.new = False
            self.process_event(store, e)

        if len(self.events):
            db_save_events_on_db(store, self.events)
            log.debug("Notification: generated %d notification events of type %s" %
                      (len(self.events), self.trigger))


class TipEventLogger(EventLogger):
    trigger = 'Tip'
    model = models.ReceiverTip

    def process_event(self, store, rtip):
        tip_desc = serialize_receivertip(rtip)

        context_desc = admin.admin_serialize_context(store,
                                                     rtip.internaltip.context,
                                                     self.language)

        steps_desc = admin.db_get_context_steps(store,
                                                context_desc['id'],
                                                    self.language)

        do_mail, receiver_desc = self.import_receiver(rtip.receiver)

        self.events.append(Event(type=self.template_type,
                                 trigger=self.trigger,
                                 node_info={},
                                 receiver_info=receiver_desc,
                                 context_info=context_desc,
                                 steps_info=steps_desc,
                                 tip_info=tip_desc,
                                 subevent_info={},
                                 do_mail=do_mail))


class MessageEventLogger(EventLogger):
    trigger = 'Message'
    model = models.Message

    def process_event(self, store, message):
        message_desc = rtip.receiver_serialize_message(message)

        # message.type can be 'receiver' or 'wb' at the moment, we care of the latter
        if message.type == u"receiver":
            return

        tip_desc = serialize_receivertip(message.receivertip)

        context_desc = admin.admin_serialize_context(store,
                                                     message.receivertip.internaltip.context,
                                                     self.language)

        steps_desc = admin.db_get_context_steps(store,
                                                context_desc['id'],
                                                self.language)

        do_mail, receiver_desc = self.import_receiver(message.receivertip.receiver)

        self.events.append(Event(type=self.template_type,
                                 trigger=self.trigger,
                                 node_info={},
                                 receiver_info=receiver_desc,
                                 context_info=context_desc,
                                 steps_info=steps_desc,
                                 tip_info=tip_desc,
                                 subevent_info=message_desc,
                                 do_mail=do_mail))


class CommentEventLogger(EventLogger):
    trigger = 'Comment'
    model = models.Comment

    def process_event(self, store, comment):
        comment_desc = rtip.receiver_serialize_comment(comment)

        context_desc = admin.admin_serialize_context(store,
                                                     comment.internaltip.context,
                                                     self.language)

        steps_desc = admin.db_get_context_steps(store,
                                                context_desc['id'],
                                                self.language)

        # for every comment, iterate on the associated receiver(s)
        log.debug("Comments from %s - Receiver(s) %d" % \
                  (comment.author, comment.internaltip.receivers.count()))

        for receiver in comment.internaltip.receivers:
            if comment.type == u'receiver' and comment.author == receiver.name:
                log.debug("Receiver is the Author (%s): skipped" % receiver.user.username)
                return

            receivertip = store.find(models.ReceiverTip,
                                     (models.ReceiverTip.internaltip_id == comment.internaltip_id,
                                      models.ReceiverTip.receiver_id == receiver.id)).one()

            tip_desc = serialize_receivertip(receivertip)

            do_mail, receiver_desc = self.import_receiver(receiver)

            self.events.append(Event(type=self.template_type,
                                     trigger=self.trigger,
                                     node_info={},
                                     receiver_info=receiver_desc,
                                     context_info=context_desc,
                                     steps_info=steps_desc,
                                     tip_info=tip_desc,
                                     subevent_info=comment_desc,
                                     do_mail=do_mail))


class FileEventLogger(EventLogger):
    trigger = 'File'
    model = models.ReceiverFile

    def process_event(self, store, rfile):
        context_desc = admin.admin_serialize_context(store,
                                                     rfile.internalfile.internaltip.context,
                                                     self.language)

        steps_desc = admin.db_get_context_steps(store,
                                                context_desc['id'],
                                                self.language)

        tip_desc = serialize_receivertip(rfile.receivertip)
        file_desc = serialize_internalfile(rfile.internalfile, rfile.id)
        do_mail, receiver_desc = self.import_receiver(rfile.receiver)

        self.events.append(Event(type=self.template_type,
                                 trigger=self.trigger,
                                 node_info={},
                                 receiver_info=receiver_desc,
                                 context_info=context_desc,
                                 steps_info=steps_desc,
                                 tip_info=tip_desc,
                                 subevent_info=file_desc,
                                 do_mail=do_mail))


class NotificationSchedule(GLJob):
    @inlineCallbacks
    def operation(self):
        yield TipEventLogger().process_events()
        yield CommentEventLogger().process_events()
        yield MessageEventLogger().process_events()
        yield FileEventLogger().process_events()
