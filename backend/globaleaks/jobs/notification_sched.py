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


def serialize_receivertip(receiver_tip):
    rtip_dict = {
        'id': receiver_tip.id,
        'creation_date': datetime_to_ISO8601(receiver_tip.creation_date),
        'last_access': datetime_to_ISO8601(receiver_tip.last_access),
        'access_counter': receiver_tip.access_counter,
        'wb_steps': receiver_tip.internaltip.wb_steps,
        'context_id': receiver_tip.internaltip.context.id,
    }
    return rtip_dict

def serialize_internalfile(ifile, rfile_id):
    """
    :param ifile: store InternalFile
    :param rfile_id: ReceiverFile.id, to keep track
    :return:
    """
    rfile_dict = {
        'receiverfile_id': rfile_id,
        'name': ifile.name,
        'content_type': ifile.content_type,
        'size': ifile.size,
        'creation_date' : datetime_to_ISO8601(ifile.creation_date),
    }
    return rfile_dict

# Note: is used tip.serialize_comment until more information are not
# requested in Comment notification template (like some Tip info)

class EventLogger(object):
    """
    This is the base class, is derived in
    TipEventLogger, CommentEventLogger, MessageEventLogger and FileEventLogger

    The pattern here:
        load_* => use transact
        import_* => receive a storm object, are executed in transact

    FUTURE XXX Note:
        I was thinking to support easily also "Admin" here, but at the moment
        receiver_info is part of the namedtuple 'Event', and change that is quite
        deeper. so at the moment I'm implemented only a receiver support here.

    """

    def __init__(self):
        self.events = []
        self.language = GLSetting.defaults.default_language

        # Assigned by the subclass
        self.context_desc = {}
        self.steps_info_desc = {}
        self.trigger = None

        # this field, do_mail, has to be used as marker, but in fact at the moment
        # is not used in mailflush.
        self.do_mail = None


    def import_receiver(self, receiver):

        self.receiver_desc = admin.admin_serialize_receiver(receiver, self.language)

        if self.trigger == 'Message':
            self.template_type = u'encrypted_message' if \
                receiver.gpg_key_status == u'enabled' else u'plaintext_message'
            return receiver.message_notification
        elif self.trigger == 'Tip':
            self.template_type = u'encrypted_tip' if \
                receiver.gpg_key_status == u'enabled' else u'plaintext_tip'
            return receiver.tip_notification
        elif self.trigger == 'Comment':
            self.template_type = u'encrypted_comment' if \
                receiver.gpg_key_status == u'enabled' else u'plaintext_comment'
            return receiver.comment_notification
        elif self.trigger == 'File':
            self.template_type = u'encrypted_file' if \
                receiver.gpg_key_status == u'enabled' else u'plaintext_file'
            return receiver.file_notification
        else:
            raise Exception("self.trigger of unexpected kind ? %s" % self.trigger)


    def append_event(self, tip_info, subevent_info):
        event = Event(type=self.template_type,
                      trigger=self.trigger,
                      node_info={},
                      steps_info=self.steps_info_desc,
                      tip_info=tip_info,
                      subevent_info=subevent_info,
                      receiver_info=self.receiver_desc,
                      context_info=self.context_desc,
                      do_mail=self.do_mail)

        self.events.append(event )

class TipEventLogger(EventLogger):

    def __init__(self):
        EventLogger.__init__(self)
        self.trigger = 'Tip'

    @transact
    def load_tips(self, store):
        not_notified_tips = store.find(models.ReceiverTip,
                                       models.ReceiverTip.mark == u'not notified')

        if not_notified_tips.count():
            log.debug("Receiver Tips found to be notified: %d" % not_notified_tips.count())

        for receiver_tip in not_notified_tips:

            self.do_mail = self.import_receiver(receiver_tip.receiver)

            tip_desc = serialize_receivertip(receiver_tip)
            receiver_tip.mark = u'notified'

            # this check is to avoid ask continuously the same context:
            if not self.context_desc.has_key('id') or \
                            self.context_desc['id'] != receiver_tip.internaltip.context_id:
                self.context_desc = admin.admin_serialize_context(store,
                                                                  receiver_tip.internaltip.context,
                                                                  self.language)

                self.steps_info_desc = admin.db_get_context_steps(store,
                                                                  self.context_desc['id'],
                                                                  self.language)

            # append the event (use the self.* and the iteration serialization):
            self.append_event(tip_info=tip_desc,
                              subevent_info=None)


class MessageEventLogger(EventLogger):

    def __init__(self):
        EventLogger.__init__(self)
        self.trigger = 'Message'

    @transact
    def load_messages(self, store):

        not_notified_messages = store.find(models.Message,
                                           models.Message.mark == u'not notified')

        if not_notified_messages.count():
            log.debug("Messages found to be notified: %d" % not_notified_messages.count())

        for message in not_notified_messages:

            message_desc = rtip.receiver_serialize_message(message)
            message.mark = u'notified'

            # message.type can be 'receiver' or 'wb' at the moment, we care of the 2nd
            if message.type == u"receiver":
                continue

            tip_desc = serialize_receivertip(message.receivertip)

            self.do_mail = self.import_receiver(message.receivertip.receiver)

            # this check is to avoid ask continuously the same context:
            if not self.context_desc.has_key('id') or \
                            self.context_desc['id'] != message.receivertip.internaltip.context_id:
                self.context_desc = admin.admin_serialize_context(store,
                                                                  message.receivertip.internaltip.context,
                                                                  self.language)
                self.steps_info_desc = admin.db_get_context_steps(store,
                                                                  self.context_desc['id'],
                                                                  self.language)

            # append the event based on the self.* and the iteration serialization:
            self.append_event(tip_info=tip_desc,
                              subevent_info=message_desc)

class CommentEventLogger(EventLogger):

    def __init__(self):
        EventLogger.__init__(self)
        self.trigger = 'Comment'

    @transact
    def load_comments(self, store):

        not_notified_comments = store.find(models.Comment,
            models.Comment.mark == u'not notified'
        )

        if not_notified_comments.count():
            log.debug("Comments found to be notified: %d" %
                      not_notified_comments.count())

        for comment in not_notified_comments:

            if not self.context_desc.has_key('id') or \
                            self.context_desc['id'] != comment.internaltip.context_id:
                self.context_desc = admin.admin_serialize_context(store,
                                                                  comment.internaltip.context,
                                                                  self.language)

                self.steps_info_desc = admin.db_get_context_steps(store,
                                                                  self.context_desc['id'],
                                                                  self.language)

            comment_desc = rtip.receiver_serialize_comment(comment)
            comment.mark = u'notified'

            # for every comment, iterate on the associated receiver(s)
            log.debug("Comments from %s - Receiver(s) %d" % \
                      (comment.author, comment.internaltip.receivers.count()))

            for receiver in comment.internaltip.receivers:

                self.do_mail = self.import_receiver(receiver)

                if comment.type == u'receiver' and comment.author == receiver.name:
                    log.debug("Receiver is the Author (%s): skipped" % receiver.user.username)
                    continue

                receivertip = store.find(models.ReceiverTip,
                    (models.ReceiverTip.internaltip_id == comment.internaltip_id,
                     models.ReceiverTip.receiver_id == receiver.id)).one()

                tip_desc = serialize_receivertip(receivertip)

                self.append_event(tip_info=tip_desc,
                                  subevent_info=comment_desc)


class FileEventLogger(EventLogger):

    def __init__(self):
        EventLogger.__init__(self)
        self.trigger = 'File'

    @transact
    def load_files(self, store):

        not_notified_rfiles = store.find(models.ReceiverFile,
            models.ReceiverFile.mark == u'not notified')

        if not_notified_rfiles.count():
            log.debug("new [Files✖Receiver] found to be notified: %d" % not_notified_rfiles.count())

        for rfile in not_notified_rfiles:

            if not self.context_desc.has_key('id') or \
                            self.context_desc['id'] != rfile.internalfile.internaltip.context_id:
                self.context_desc = admin.admin_serialize_context(store,
                                                                  rfile.internalfile.internaltip.context,
                                                                  self.language)

                self.steps_info_desc = admin.db_get_context_steps(store,
                                                                  self.context_desc['id'],
                                                                  self.language)

            file_desc = serialize_internalfile(rfile.internalfile, rfile.id)
            tip_desc = serialize_receivertip(rfile.receiver_tip)
            rfile.mark = u'notified'

            self.do_mail = self.import_receiver(rfile.receiver)

            self.append_event(tip_info=tip_desc,
                              subevent_info=file_desc)



@transact
def save_event_db(store, event_dict):

    for evnt in event_dict:

        e = EventLogs()

        e.description = {
            'receiver_info': evnt.receiver_info,
            'context_info': evnt.context_info,
            'tip_info': evnt.tip_info,
            'subevent_info': evnt.subevent_info,
            'steps_info': evnt.steps_info,
            'type': evnt.type,
        }
        # this is important to associate Event with ReceiverFile|Message|Comment|ReceiverTip
        e.event_reference = {
            'kind': evnt.trigger
        }
        # why is a JSON ? now is
        e.title = evnt.trigger
        e.receiver_id = evnt.receiver_info['id']
        e.receivertip_id = evnt.tip_info['id']
        e.mail_sent = False

        store.add(e)


class NotificationSchedule(GLJob):
    @inlineCallbacks
    def operation(self):
        # TODO: remove notification_status from Model different of EventLogs

        tips_events = TipEventLogger()
        yield tips_events.load_tips()
        yield save_event_db(tips_events.events)

        comments_events = CommentEventLogger()
        yield comments_events.load_comments()
        yield save_event_db(comments_events.events)

        messages_events = MessageEventLogger()
        yield messages_events.load_messages()
        yield save_event_db(messages_events.events)

        files_events = FileEventLogger()
        yield files_events.load_files()
        yield save_event_db(files_events.events)

        if any([len(files_events.events), len(messages_events.events),
                len(comments_events.events), len(tips_events.events)]):
            log.debug("Notification: generated Events: %d tips, %d comments, %d messages, %d files" % (
                len(tips_events.events), len(comments_events.events),
                len(messages_events.events), len(files_events.events) ) )
