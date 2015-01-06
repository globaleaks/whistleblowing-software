# -*- coding: UTF-8
#
#   notification_sched
#   ******************
#
# Notification implementation, documented along the others asynchronous
# operations, in Architecture and in jobs/README.md

import sys

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.jobs.base import GLJob
from globaleaks.handlers import admin, rtip
from globaleaks.handlers.admin.notification import admin_serialize_notification
from globaleaks.plugins import notification
from globaleaks.plugins.base import Event
from globaleaks.rest import errors
from globaleaks.settings import transact, transact_ro, GLSetting
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

    # settings.notification_plugins contain a list of supported plugin
    # at the moment only 1. so [0] is used.
    # different context/receiver may use different code-plugin, just at the
    # moment they are not implemented, and therefore is a classvariable
    plugin = getattr(notification, GLSetting.notification_plugins[0])()

    def __init__(self):
        self.events = {}
        self.language = GLSetting.defaults.default_language

        # Assigned by the subclass
        self.context_desc = {}
        self.steps_info_desc = {}
        self.trigger = None
        self.do_mail = None

    def import_receiver(self, receiver):

        self.receiver_desc = admin.admin_serialize_receiver(receiver, self.language)

        if self.trigger == 'Message':
            self.template_type = u'encrypted_message' if \
                receiver.gpg_key_status == u'Enabled' else u'plaintext_message'
            if not receiver.message_notification:
                log.debug("Receiver %s has %s notification disabled" %
                          (receiver.user.username, self.trigger))
            return receiver.message_notification
        elif self.trigger == 'Tip':
            self.template_type = u'encrypted_tip' if \
                receiver.gpg_key_status == u'Enabled' else u'plaintext_tip'
            if not receiver.tip_notification:
                log.debug("Receiver %s has %s notification disabled" %
                          (receiver.user.username, self.trigger))
            return receiver.tip_notification
        elif self.trigger == 'Comment':
            self.template_type = u'encrypted_comment' if \
                receiver.gpg_key_status == u'Enabled' else u'plaintext_comment'
            if not receiver.comment_notification:
                log.debug("Receiver %s has %s notification disabled" %
                          (receiver.user.username, self.trigger))
            return receiver.comment_notification
        elif self.trigger == 'File':
            self.template_type = u'encrypted_file' if \
                receiver.gpg_key_status == u'Enabled' else u'plaintext_file'
            if not receiver.file_notification:
                log.debug("Receiver %s has %s notification disabled" %
                          (receiver.user.username, self.trigger))
            return receiver.file_notification
        else:
            raise Exception("self.trigger of unexpected kind ? %s" % self.trigger)

    @transact_ro
    def load_node(self, store):
        """
        called directly by constructor
        notification setting need to contains both template
        and systemsettings.
        """
        self.node_desc = admin.db_admin_serialize_node(store, self.language)
        self.notification_desc = admin_serialize_notification(
            store.find(models.Notification).one(),
            self.language
        )

    def append_event(self, trigger_info, trigger_parent, event_id):

        assert hasattr(self, 'trigger'), "Superclass has not initialized self.trigger"
        event = Event(type=self.template_type, trigger=self.trigger,
                        steps_info=self.steps_info_desc,
                        trigger_info=trigger_info,
                        trigger_parent=trigger_parent,
                        notification_settings=self.notification_desc,
                        node_info=self.node_desc,
                        receiver_info=self.receiver_desc,
                        context_info=self.context_desc,
                        do_mail=self.do_mail,
                        plugin=EventLogger.plugin)

        self.events.update({unicode(event_id): event })

class TipEventLogger(EventLogger):

    def __init__(self):
        EventLogger.__init__(self)
        self.trigger = 'Tip'

    @transact
    def load_tips(self, store):
        # XXX call this shit: from_tips_to_events

        not_notified_tips = store.find(models.ReceiverTip,
                                       models.ReceiverTip.mark == models.ReceiverTip._marker[0]
        )

        if not_notified_tips.count():
            log.debug("Receiver Tips found to be notified: %d" % not_notified_tips.count())

        for receiver_tip in not_notified_tips:

            self.do_mail = self.import_receiver(receiver_tip.receiver)

            tip_desc = serialize_receivertip(receiver_tip)

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
            self.append_event(trigger_info=tip_desc, 
                              trigger_parent=None, 
                              event_id=tip_desc['id'])


# TODO remind that when do_mail is False:
# receiver_tip.mark = models.ReceiverTip._marker[3] # 'disabled'

class MessageEventLogger(EventLogger):

    def __init__(self):
        EventLogger.__init__(self)
        self.trigger = 'Message'

    @transact
    def load_messages(self, store):

        not_notified_messages = store.find(models.Message,
                                           models.Message.mark == models.Message._marker[0]
        )

        if not_notified_messages.count():
            log.debug("Messages found to be notified: %d" % not_notified_messages.count())

        for message in not_notified_messages:

            message_desc = rtip.receiver_serialize_message(message)

            # !? is pretty useless ?
            message.mark = u'notified' # models.Message._marker[1]

            # message.type can be 'receiver' or 'wb' at the moment, we care of the 2nd
            if message.type == u"receiver":
                continue

            # trigger_parent:
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
            self.append_event(trigger_info=message_desc, 
                    trigger_parent=tip_desc, 
                    event_id=message_desc['id'])

class CommentEventLogger(EventLogger):

    def __init__(self):
        EventLogger.__init__(self)
        self.trigger = 'Comment'

    @transact
    def load_comments(self, store):

        not_notified_comments = store.find(models.Comment,
            models.Comment.mark == models.Comment._marker[0]
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

            # This is useless like the same thing in Message above
            comment.mark = models.Comment._marker[1] # 'notified'

            # for every comment, iterate on the associated receiver(s)
            log.debug("Comments from %s - Receiver(s) %d" % \
                      (comment.author, comment.internaltip.receivers.count()))

            for receiver in comment.internaltip.receivers:

                self.do_mail = self.import_receiver(receiver)

                if comment.type == models.Comment._types[0] and comment.author == receiver.name:
                    log.debug("Receiver is the Author (%s): skipped" % receiver.user.username)
                    continue

                receivertip = store.find(models.ReceiverTip,
                    (models.ReceiverTip.internaltip_id == comment.internaltip_id,
                     models.ReceiverTip.receiver_id == receiver.id)).one()

                rtip_desc = serialize_receivertip(receivertip)

                self.append_event(trigger_info=comment_desc, 
                        trigger_parent=rtip_desc, 
                        event_id=comment_desc['id'])


class FileEventLogger(EventLogger):

    def __init__(self):
        EventLogger.__init__(self)
        self.trigger = 'File'

    @transact
    def load_files(self, store):

        not_notified_rfiles = store.find(models.ReceiverFile,
            models.ReceiverFile.mark == models.ReceiverFile._marker[0]
        )

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
            rtip_desc = serialize_receivertip(rfile.receiver_tip)

            self.do_mail = self.import_receiver(rfile.receiver)

            self.append_event(trigger_info=file_desc, 
                    trigger_parent=rtip_desc,
                    event_id=file_desc['receiverfile_id'])








class NotificationMail:
    """
    Has to be implement in the appropriate plugin class

            if notification_counter >= GLSetting.notification_limit:
                log.debug("Notification counter has reached the suggested limit: %d (tip)" %
                          notification_counter)
                break

    """

    @transact
    def receiverfile_notification_succeeded(self, store, result, receiverfile_id):
        """
        This is called when the Receiver File notification has succeeded
        """
        rfile = store.find(models.ReceiverFile, models.ReceiverFile.id == receiverfile_id).one()

        if not rfile:
            raise errors.FileIdNotFound

        rfile.mark = models.ReceiverFile._marker[1] # 'notified'

        log.debug("Email: +[Success] Notification of receiverfile %s for receiver %s" % (rfile.internalfile.name, rfile.receiver.user.username))

    @transact
    def receiverfile_notification_failed(self, store, failure, receiverfile_id):
        """
        This is called when the Receiver File notification has failed.
        """
        rfile = store.find(models.ReceiverFile, models.ReceiverFile.id == receiverfile_id).one()

        if not rfile:
            raise errors.FileIdNotFound

        rfile.mark = models.ReceiverFile._marker[2] # 'unable to notify'

        log.debug("Email: -[Fail] Notification of receiverfile %s for receiver %s" % (rfile.internalfile.name, rfile.receiver.user.username))

    @inlineCallbacks
    def do_receiverfile_notification(self, receiverfile_events):

        for receiverfile_id, event in receiverfile_events.iteritems():

            notify = event.plugin.do_notify(event)

            if notify is None:
                continue

            notify.addCallback(self.receiverfile_notification_succeeded, receiverfile_id)
            notify.addErrback(self.receiverfile_notification_failed, receiverfile_id)

            # we need to wait on single mail send basis to not be prone to DoS
            # and be forced to open so many outgoing connections.
            yield notify


    @transact_ro
    def comment_notification_succeeded(self, store, result, comment_id):
        """
        This is called when the comment notification has succeeded
        """
        comment = store.find(models.Comment, models.Comment.id == comment_id).one()
        # comment.mark  = ?
        log.debug("Email: +[Success] Notification of comment from %s" % comment.author)

    @transact_ro
    def comment_notification_failed(self, store, failure, comment_id):
        """
        This is called when the comment notification has failed.
        """
        comment = store.find(models.Comment, models.Comment.id == comment_id).one()
        log.debug("Email: -[Fail] Notification of comment from %s" % comment.author)

    @inlineCallbacks
    def do_comment_notification(self, comment_events):

        for comment_id, event in comment_events.iteritems():

            notify = event.plugin.do_notify(event)

            if notify is None:
                continue

            notify.addCallback(self.comment_notification_succeeded, comment_id)
            notify.addErrback(self.comment_notification_failed, comment_id)

            # we need to wait on single mail send basis to not be prone to DoS
            # and be forced to open so many outgoing connections.
            yield notify

    @transact
    def tip_notification_succeeded(self, store, result, tip_id):
        """
        This is called when the tip notification has succeeded
        """
        receiver_tip = store.find(models.ReceiverTip, models.ReceiverTip.id == tip_id).one()

        if not receiver_tip:
            raise errors.TipIdNotFound

        log.debug("Email: +[Success] Notification Tip receiver %s" % receiver_tip.receiver.user.username)
        receiver_tip.mark = models.ReceiverTip._marker[1] # 'notified'

    @transact
    def tip_notification_failed(self, store, failure, tip_id):
        """
        This is called when the tip notification has failed.
        """
        receiver_tip = store.find(models.ReceiverTip, models.ReceiverTip.id == tip_id).one()

        if not receiver_tip:
            raise errors.TipIdNotFound

        log.debug("Email: -[Fail] Notification Tip receiver %s" % receiver_tip.receiver.user.username)
        receiver_tip.mark = models.ReceiverTip._marker[2] # 'unable to notify'

    @inlineCallbacks
    def do_tip_notification(self, tip_events):
        """
        This function fill the table events with new notification, to be display at the
        receive login
        """

        for tip_id, event in tip_events.iteritems():

            # plugin is the email, and the email notification may be disable globally,
            # in this case, is there checked to be skipped
            if GLSetting.notification_temporary_disable:
                log.debug("Email notification of [%s %s] temporarly disable" % event.type, event.receiver_info)
                continue

            notify = event.plugin.do_notify(event)

            if notify is None:
                continue

            notify.addCallback(self.tip_notification_succeeded, tip_id)
            notify.addErrback(self.tip_notification_failed, tip_id)

            # we need to wait on single mail send basis to not be prone to DoS
            # and be forced to open so many outgoing connections.
            yield notify


    @transact_ro
    def message_notification_succeeded(self, store, result, message_id):
        """
        This is called when the message notification has succeeded
        """
        message = models.Message.get(store, message_id)
        log.debug("Email: +[Success] Notification of message for %s" %
                  message.receivertip.receiver.user.username)

    @transact_ro
    def message_notification_failed(self, store, failure, message_id):
        """
        This is called when the message notification has failed.
        """
        message = store.find(models.Message, models.Message.id == message_id).one()
        log.debug("Email: -[Fail] Notification of message receiver %s" %
                  message.receivertip.receiver.user.username)

    @inlineCallbacks
    def do_message_notification(self, message_events):

        for message_id, event in message_events.iteritems():

            notify = event.plugin.do_notify(event)

            if notify is None:
                continue

            notify.addCallback(self.message_notification_succeeded, message_id)
            notify.addErrback(self.message_notification_failed, message_id)

            # we need to wait on single mail send basis to not be prone to DoS
            # and be forced to open so many outgoing connections.
            yield notify


@transact
def save_event_db(store, event_dict):

    for event_id, evnt in event_dict.iteritems():

        e = EventLogs()

        e.description = {
            'received_info': evnt.receiver_info,
            'context_info': evnt.context_info,
            'trigger_parent': evnt.trigger_parent,
            'trigger_info': evnt.trigger_info,
        }
        # this is important to link Event with ReceiverFile|Message|Comment|ReceiverTip
        e.event_reference = {
            'id': event_id,
            'kind': evnt.trigger
        }
        e.title = "Title [%s]" % evnt.trigger
        e.receiver_id = evnt.receiver_info['id']
        e.mail_sent = False

        store.add(e)


class NotificationSchedule(GLJob):
    """
    REMIND:
            # by ticket https://github.com/globaleaks/GlobaLeaks/issues/444
            # send notification of file only if notification of tip is already on send status
            if rfile.receiver_tip.mark == models.ReceiverTip._marker[0]: # 'not notified'
                rfile.mark = models.ReceiverFile._marker[4] # 'skipped'
                log.debug("Skipped notification of %s (for %s) because Tip not yet notified" %
                          (rfile.internalfile.name, rfile.receiver.name))
                store.commit()
                continue
    """

    @inlineCallbacks
    def operation(self):
        # TODO: remove notification_status from Model different of EventLogs

        tips_events = TipEventLogger()
        yield tips_events.load_node()
        yield tips_events.load_tips()
        yield save_event_db(tips_events.events)

        comments_events = CommentEventLogger()
        yield comments_events.load_node()
        yield comments_events.load_comments()
        yield save_event_db(comments_events.events)

        messages_events = MessageEventLogger()
        yield messages_events.load_node()
        yield messages_events.load_messages()
        yield save_event_db(messages_events.events)

        files_events = FileEventLogger()
        yield files_events.load_node()
        yield files_events.load_files()
        yield save_event_db(files_events.events)

        notifcb = NotificationMail()

        # There is no more check in notification_limit now, just flush out:

        try:

            if len(tips_events.events.keys()):
                notifcb.do_tip_notification(tips_events.events)

            if len(comments_events.events.keys()):
                notifcb.do_comment_notification(comments_events.events)

            if len(messages_events.events.keys()):
                notifcb.do_message_notification(messages_events.events)

            if len(files_events.events.keys()):
                notifcb.do_receiverfile_notification(files_events.events)

        except Exception as excep:
            log.err("Error in Mail Notification: %s" % excep)
            log.debug(sys.exc_info())
