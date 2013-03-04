# -*- coding: UTF-8
#
#   notification_sched
#   ******************
#
# Notification implementation, documented along the others asynchronous
# operations, in Architecture and in jobs/README.md

from twisted.internet.defer import inlineCallbacks

from globaleaks.jobs.base import GLJob
from globaleaks.plugins.base import Event
from globaleaks import models
from globaleaks.settings import transact
from globaleaks.utils import log, prettyDateTime
from globaleaks.plugins import notification
from globaleaks import settings
from globaleaks.handlers import admin, tip

from collections import namedtuple

Event = namedtuple('Event',
                   ['type', 'trigger', 'notification_settings',
                    'trigger_info', 'node_info', 'receiver_info', 'context_info'])


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
    def do_tip_notification(self, store, notification_settings):

        # settings.notification_plugins contain a list of supported plugin
        # at the moment only 1. so [0] is used. but different context/receiver
        # may use different code-plugin:
        cplugin = settings.notification_plugins[0]

        plugin = getattr(notification, cplugin)(notification_settings)

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
                            notification_settings=notification_settings,
                            trigger_info=tip_desc,
                            node_info=node_desc,
                            receiver_info=receiver_desc,
                            context_info=context_desc)

            # XXX BUG! All notification is marked as correctly send
            rtip.mark = models.ReceiverTip._marker[1]

            notify = plugin.do_notify(event)

            @notify.addCallback
            def success(result):
                log.debug("OK NOT trackable notification due to Storm/Twisted insanity")
                # log.debug('OK Notification for %s' % rtip.receiver.username )
                # rtip.mark = models.ReceiverTip._marker[1]

            @notify.addErrback
            def error(result):
                log.debug("FAIL NOT trackable notification due to Storm/Twisted insanity")
                # log.debug('FAIL Notification for %s FAIL' % rtip.receiver.username )
                # :( This is triggering a "fail connection is closed from Storm"
                # but this is *needed* to keep track of notification status...!
                # rtip.mark = models.ReceiverTip._marker[2]

            # yield notify
            # -- no more 'yield' because we're a @transact
            # -- no more 'notify' because I don't know

        log.debug("Completed notification of %d receiver tips " % not_notified_tips.count() )


    @transact
    def do_comment_notification(self, store, notification_settings):

        comment_notified_cnt = 0
        cplugin = settings.notification_plugins[0]

        plugin = getattr(notification, cplugin)(notification_settings)

        not_notified_comments = store.find(models.Comment,
            models.Comment.mark == models.Comment._marker[0]
        )

        node_desc = admin.admin_serialize_node(store.find(models.Node).one())

        log.debug("Comments found to be notified: %d" % not_notified_comments.count() )
        for comment in not_notified_comments:

            # Storm mishitrstanding :(
            citid = store.find(models.InternalTip, models.InternalTip.id == comment.internaltip_id).one()

            # for every comment, iter on the associated receiver
            log.debug("Comments receiver: %d" % citid.receivers.count())

            comment_desc = tip.serialize_comment(comment)

            context_desc = admin.admin_serialize_context(citid.context)
            assert context_desc.has_key('name')

            # XXX BUG! All notification is marked as correctly send,
            # This can't be managed by callback, and can't be managed by actual DB design
            comment.mark = models.Comment._marker[1]

            for receiver in citid.receivers:

                receiver_desc = admin.admin_serialize_receiver(receiver)
                assert receiver_desc.has_key('notification_fields')

                if not receiver.notification_fields.has_key('mail_address'):
                    log.debug("Receiver %s lack of email address!" % receiver.name)
                    # this is actually impossible, but a check is never bad
                    continue

                comment_notified_cnt += 1

                event = Event(type=u'comment', trigger='Comment',
                    notification_settings=notification_settings,
                    trigger_info=comment_desc,
                    node_info=node_desc,
                    receiver_info=receiver_desc,
                    context_info=context_desc)

                notify = plugin.do_notify(event)

                @notify.addCallback
                def success(result):
                    log.debug("OK NOT trackable comment notification")

                @notify.addErrback
                def error(result):
                    log.debug("FAIL NOT trackable comment notification")

        if comment_notified_cnt:
            log.debug("Completed comment notification: %d " % comment_notified_cnt)



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
        notification_settings = yield self._get_notification_settings()

        if not notification_settings:
            log.err("Node has not Notification configured, Notification disabled!")
            return

        # Else, checks tip/file/comment/activation link
        log.debug("Node notification configured: entering in notification operations")

        yield self.do_tip_notification(notification_settings)
        yield self.do_comment_notification(notification_settings)

        # self.do_file_notification(notification_settings)

