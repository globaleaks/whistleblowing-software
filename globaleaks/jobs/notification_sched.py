# -*- coding: UTF-8
#
#   notification_sched
#   ******************
#
# Notification implementation, documented along the others asynchronous
# operations, in Architecture and in jobs/README.md

from twisted.internet.defer import inlineCallbacks, DeferredList

from globaleaks.rest import errors
from globaleaks.jobs.base import GLJob
from globaleaks.plugins.base import Event
from globaleaks import models
from globaleaks.settings import transact
from globaleaks.utils import log, prettyDateTime
from globaleaks.plugins import notification
from globaleaks import settings
from globaleaks.handlers import admin, tip

def serialize_receivertip(rtip):
    rtip_dict = {
        'id': unicode(rtip.id),
        'creation_date' : unicode(prettyDateTime(rtip.creation_date)),
        'last_access' : unicode(prettyDateTime(rtip.last_access)),
        'expressed_pertinence' : unicode(prettyDateTime(rtip.expressed_pertinence)),
        'access_counter' : int(rtip.access_counter),
        }
    return rtip_dict

# Note: is used tip.serialize_comment until more information are not
# requested in Comment notification template (like some Tip info)

class APSNotification(GLJob):
    notification_settings = None

    @transact
    def _get_notification_settings(self, store):
        """
        notification setting need to contains bot template
        and systemsettings
        """
        from globaleaks.handlers.admin import admin_serialize_notification

        notif = store.find(models.Notification).one()

        if not notif.server:
            return None

        return admin_serialize_notification(notif)


    @transact
    def create_tip_notification_events(self, store):
        """
        This transaction will return all a list of tuples containing the tips
        for which the notification event has not been run.

        Returns:

            events: a list of tuples containing (tip_id, an instance of
                :class:`globaleaks.plugins.base.Event`).

        """
        events = []

        # settings.notification_plugins contain a list of supported plugin
        # at the moment only 1. so [0] is used. but different context/receiver
        # may use different code-plugin:
        cplugin = settings.notification_plugins[0]

        plugin = getattr(notification, cplugin)(self.notification_settings)

        not_notified_tips = store.find(models.ReceiverTip,
            models.ReceiverTip.mark == models.ReceiverTip._marker[0]
        )

        node_desc = admin.admin_serialize_node(store.find(models.Node).one())

        log.debug("Tip found to be notified: %d" % not_notified_tips.count() )
        for rtip in not_notified_tips:

            context_desc = admin.admin_serialize_context(rtip.internaltip.context)
            assert context_desc.has_key('name')

            receiver_desc = admin.admin_serialize_receiver(rtip.receiver)
            assert receiver_desc.has_key('notification_fields')

            tip_desc = serialize_receivertip(rtip)

            if not rtip.receiver.notification_fields.has_key('mail_address'):
                log.debug("Receiver %s lack of email address!" % rtip.receiver.name)
                # this is actually impossible, but a check is never bad
                return

            event = Event(type=u'tip', trigger='Tip',
                            notification_settings=self.notification_settings,
                            trigger_info=tip_desc,
                            node_info=node_desc,
                            receiver_info=receiver_desc,
                            context_info=context_desc,
                            plugin=plugin)
            events.append((unicode(rtip.id), event))

        return events

    @transact
    def tip_notification_succeeded(self, store, result, tip_id):
        """
        This is called when the tip notification has succeeded
        """
        rtip = store.find(models.ReceiverTip, models.ReceiverTip.id == tip_id).one()

        if not rtip:
            raise errors.TipGusNotFound

        log.debug('OK Notification of tip for %s' % rtip.receiver.username )
        rtip.mark = models.ReceiverTip._marker[1]

    @transact
    def tip_notification_failed(self, store, failure, tip_id):
        """
        This is called when the tip notification has failed.
        """
        rtip = store.find(models.ReceiverTip, models.ReceiverTip.id == tip_id).one()

        if not rtip:
            raise errors.TipGusNotFound

        log.debug('FAIL Notification of tip for %s FAIL' % rtip.receiver.username )
        rtip.mark = models.ReceiverTip._marker[2]

    def do_tip_notification(self, tip_events):
        l = []
        for tip_id, event in tip_events:

            notify = event.plugin.do_notify(event)
            notify.addCallback(self.tip_notification_succeeded, tip_id)
            notify.addErrback(self.tip_notification_succeeded, tip_id)
            l.append(notify)

        return DeferredList(l)

        log.debug("Completed notification of %d receiver tips " % not_notified_tips.count() )

    @transact
    def create_comment_notification_events(self, store):
        """
        Creates events for performing notification of newly added comments.

        Returns:
            events: a list of tuples containing ((comment_id, receiver_id), an instance of
                :class:`globaleaks.plugins.base.Event`).


        """
        events = []
        comment_notified_cnt = 0
        cplugin = settings.notification_plugins[0]

        plugin = getattr(notification, cplugin)(self.notification_settings)

        not_notified_comments = store.find(models.Comment,
            models.Comment.mark == models.Comment._marker[0]
        )

        node_desc = admin.admin_serialize_node(store.find(models.Node).one())

        log.debug("Comments found to be notified: %d" % not_notified_comments.count() )
        for comment in not_notified_comments:

            # for every comment, iter on the associated receiver
            log.debug("Comments receiver: %d" % comment.internaltip.receivers.count())

            comment_desc = tip.serialize_comment(comment)

            context_desc = admin.admin_serialize_context(comment.internaltip.context)
            assert context_desc.has_key('name')

            # XXX BUG! All notification is marked as correctly send,
            # This can't be managed by callback, and can't be managed by actual DB design

            for receiver in comment.internaltip.receivers:

                receiver_desc = admin.admin_serialize_receiver(receiver)
                assert receiver_desc.has_key('notification_fields')

                if not receiver.notification_fields.has_key('mail_address'):
                    log.debug("Receiver %s lack of email address!" % receiver.name)
                    # this is actually impossible, but a check is never bad
                    continue

                comment_notified_cnt += 1

                event = Event(type=u'comment', trigger='Comment',
                    notification_settings=self.notification_settings,
                    trigger_info=comment_desc,
                    node_info=node_desc,
                    receiver_info=receiver_desc,
                    context_info=context_desc,
                    plugin=plugin)

                events.append(((unicode(comment.id), unicode(receiver.id)), event))

        return events

    @transact
    def comment_notification_succeeded(self, store, result, comment_id, receiver_id):
        """
        This is called when the comment notification has succeeded
        """
        log.debug("OK Notifification of comment %s for reciever %s" % (comment_id, receiver_id))

    @transact
    def comment_notification_failed(self, store, failure, comment_id, receiver_id):
        """
        This is called when the comment notification has failed.
        """
        log.debug("FAILED Notifification of comment %s for reciever %s" % (comment_id, receiver_id))

    def do_comment_notification(self, comment_events):
        l = []
        for comment_receiver_id, event in comment_events:
            comment_id, receiver_id = comment_receiver_id

            notify = event.plugin.do_notify(event)
            notify.addCallback(self.comment_notification_succeeded, comment_id, receiver_id)
            notify.addErrback(self.comment_notification_failed, comment_id, receiver_id)
            l.append(notify)

        # we place all the notification events inside of a deferred list so
        # that they can all run concurrently
        return DeferredList(l)

    @inlineCallbacks
    def operation(self):
        """
        Goal of this event is to check all the:
            Tips
            Comment
            New files
            System Event

        Only the Models with the 'notification_status' can track which elements has been
        notified or not.
        """

        # Initialize Notification setting system wide
        self.notification_settings = yield self._get_notification_settings()

        if not self.notification_settings:
            log.err("Node has not Notification configured, Notification disabled!")
            return

        # Else, checks tip/file/comment/activation link
        log.debug("Node notification configured: entering in notification operations")

        tip_events = yield self.create_tip_notification_events()
        comment_events = yield self.create_comment_notification_events()

        dl1 = self.do_tip_notification(tip_events)
        dl2 = self.do_comment_notification(comment_events)
        # d3 = self.do_file_notification()
        # yield DeferredList([d1, d2, d3], consumeErrors=True)
        yield DeferredList([d1, d2], consumeErrors=True)

