# -*- encoding: utf-8 -*-
#
#   mailflush_sched
#   ***************
#
# Flush the email that has to be sent, is based on EventLog
# database table.


from globaleaks import models
from globaleaks.handlers.admin import db_admin_serialize_node
from globaleaks.jobs.base import GLJob
from globaleaks.rest import errors
from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.utils.utility import log, datetime_to_ISO8601

from globaleaks.models import EventLogs
from globaleaks.handlers.admin.notification import admin_serialize_notification
from globaleaks.plugins import notification
from globaleaks.utils.utility import deferred_sleep

from cyclone.util import ObjectDict as OD
from twisted.internet.defer import inlineCallbacks



class NotificationMail:
    """
    Has to be implement in the appropriate plugin class

            if notification_counter >= GLSetting.notification_limit:
                log.debug("Notification counter has reached the suggested limit: %d (tip)" %
                          notification_counter)
                break

    """

    def __init__(self, plugin_used):
        self.plugin_used = plugin_used

    @inlineCallbacks
    def do_every_notification(self, eventdict):

        notify = self.plugin_used.do_notify(eventdict)

        if notify is None:
            yield deferred_sleep(1.0)
        else:
            notify.addCallback(self.every_notification_succeeded, eventdict['id'])
            notify.addErrback(self.every_notification_failed, eventdict['id'])
            yield notify


    @transact
    def every_notification_succeeded(self, store, event_id):
        print "success", event_id
        pass

    @transact
    def every_notification_failed(self, store, event_id):
        print "fail", event_id
        pass



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

            notify = self.plugin_used.do_notify(event)

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

            notify = self.plugin_used.do_notify(event)

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

            notify = self.plugin_used.do_notify(event)

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

            notify = self.plugin_used.do_notify(event)

            if notify is None:
                continue

            notify.addCallback(self.message_notification_succeeded, message_id)
            notify.addErrback(self.message_notification_failed, message_id)

            # we need to wait on single mail send basis to not be prone to DoS
            # and be forced to open so many outgoing connections.
            yield notify





@transact_ro
def load_complete_events(store):
    """
    _complete_ is explicit because do not serialize, but make an OD() of the description.
    """

    notification_settings = admin_serialize_notification(
        store.find(models.Notification).one(), 'en'
    )

    node_desc = db_admin_serialize_node(store, 'en')

    event_list = []
    storedevnts = store.find(EventLogs)

    for stev in storedevnts:

        eventcomplete = OD()

        # node level information are not stored in the node, but fetch now\
        eventcomplete.notification_settings = notification_settings
        eventcomplete.node_info = node_desc

        # event level information are decoded form DB in the old 'Event'|nametuple format:
        eventcomplete.receiver_info = stev.description['receiver_info']
        eventcomplete.trigger_parent = stev.description['trigger_parent']
        eventcomplete.trigger_info = stev.description['trigger_info']
        eventcomplete.context_info = stev.description['context_info']
        eventcomplete.steps_info = stev.description['steps_info']
        # TODO node

        eventcomplete.type = stev.description['type'] # 'Tip', 'Comment'
        eventcomplete.trigger = stev.event_reference['kind'] # 'plaintext_blah' ...

        event_list.append(eventcomplete)

    return event_list


class MailflushSchedule(GLJob):

    @inlineCallbacks
    def operation(self):


        queue_events = yield load_complete_events()

        plugin = getattr(notification, GLSetting.notification_plugins[0])()
        notifcb = NotificationMail(plugin)


        for qe in queue_events:
            print "I'm flushing"
            print dir(qe)
            deferred_sleep(2)
            notifcb.do_every_notification(qe)
            deferred_sleep(2)


