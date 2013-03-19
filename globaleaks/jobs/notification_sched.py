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
from globaleaks.settings import transact, GLSetting
from globaleaks.utils import log, pretty_date_time
from globaleaks.plugins import notification
from globaleaks.handlers import admin, tip

def serialize_receivertip(rtip):
    rtip_dict = {
        'id': unicode(rtip.id),
        'creation_date' : unicode(pretty_date_time(rtip.creation_date)),
        'last_access' : unicode(pretty_date_time(rtip.last_access)),
        'expressed_pertinence' : unicode(rtip.expressed_pertinence),
        'access_counter' : int(rtip.access_counter),
        }
    return rtip_dict

def serialize_internalfile(ifile):
    rfile_dict = {
        'name': unicode(ifile.name),
        'sha2sum': unicode(ifile.sha2sum),
        'content_type': unicode(ifile.content_type),
        'size': unicode(ifile.size),
        'creation_date' : unicode(pretty_date_time(ifile.creation_date)),
    }
    return rfile_dict

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
        cplugin = GLSetting.notification_plugins[0]

        plugin = getattr(notification, cplugin)()

        not_notified_tips = store.find(models.ReceiverTip,
            models.ReceiverTip.mark == models.ReceiverTip._marker[0]
        )

        node_desc = admin.admin_serialize_node(store.find(models.Node).one())

        if not_notified_tips.count():
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

        log.debug("+[Success] Notification Tip reciever %s" % rtip.receiver.username)
        rtip.mark = models.ReceiverTip._marker[1]

    @transact
    def tip_notification_failed(self, store, failure, tip_id):
        """
        This is called when the tip notification has failed.
        """
        rtip = store.find(models.ReceiverTip, models.ReceiverTip.id == tip_id).one()

        if not rtip:
            raise errors.TipGusNotFound

        log.debug("-[Fail] Notification Tip reciever %s" % rtip.receiver.username)
        rtip.mark = models.ReceiverTip._marker[2]

    def do_tip_notification(self, tip_events):
        l = []
        for tip_id, event in tip_events:

            notify = event.plugin.do_notify(event)
            print "pipo"
            #notify.addCallback(self.tip_notification_succeeded, tip_id)
            #notify.addErrback(self.tip_notification_succeeded, tip_id)
            l.append(notify)

        return DeferredList(l)

    @transact
    def create_comment_notification_events(self, store):
        """
        Creates events for performing notification of newly added comments.

        Returns:
            events: a list of tuples containing ((comment_id, receiver_id), an instance of
                :class:`globaleaks.plugins.base.Event`).


        """
        events = []
        cplugin = GLSetting.notification_plugins[0]

        plugin = getattr(notification, cplugin)()

        not_notified_comments = store.find(models.Comment,
            models.Comment.mark == models.Comment._marker[0]
        )

        node_desc = admin.admin_serialize_node(store.find(models.Node).one())

        if not_notified_comments.count():
            log.debug("Comments found to be notified: %d" % not_notified_comments.count() )

        for comment in not_notified_comments:

            if comment.internaltip is None or comment.internaltip.receivers is None:
                log.err("Comment %s has internaltip or receivers broken reference" % comment.id)
                comment.mark = models.Comment._marker[2] # unable to be notified
                continue

            # for every comment, iter on the associated receiver
            log.debug("Comments receiver: %d" % comment.internaltip.receivers.count())

            comment_desc = tip.serialize_comment(comment)

            context_desc = admin.admin_serialize_context(comment.internaltip.context)
            assert context_desc.has_key('name')

            # XXX BUG! All notification is marked as correctly send,
            # This can't be managed by callback, and can't be managed by actual DB design
            comment.mark = models.Comment._marker[1]

            for receiver in comment.internaltip.receivers:

                receiver_desc = admin.admin_serialize_receiver(receiver)
                assert receiver_desc.has_key('notification_fields')

                if not receiver.notification_fields.has_key('mail_address'):
                    log.debug("Receiver %s lack of email address!" % receiver.name)
                    # this is actually impossible, but a check is never bad
                    continue

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
        receiver = store.find(models.Receiver, models.Receiver.id == receiver_id).one()
        if not receiver:
            raise errors.ReceiverGusNotFound
        log.debug("+[Success] Notification of comment reciever %s" % receiver.username)

    @transact
    def comment_notification_failed(self, store, failure, comment_id, receiver_id):
        """
        This is called when the comment notification has failed.
        """
        receiver = store.find(models.Receiver, models.Receiver.id == receiver_id).one()
        if not receiver:
            raise errors.ReceiverGusNotFound
        log.debug("-[Fail] Notification of comment reciever %s" % receiver.username)

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


    @transact
    def create_file_notification_events(self, store):
        """
        Creates events for performing notification of newly added files..

        Returns:
            events: a list of tuples containing ((receiverfile_id, receiver_id), an instance of
                :class:`globaleaks.plugins.base.Event`).

        """
        events = []
        cplugin = GLSetting.notification_plugins[0]

        plugin = getattr(notification, cplugin)()

        not_notified_rfiles = store.find(models.ReceiverFile,
            models.ReceiverTip.mark == models.ReceiverFile._marker[0]
        )

        node_desc = admin.admin_serialize_node(store.find(models.Node).one())

        if not_notified_rfiles.count():
            log.debug("Receiverfiles found to be notified: %d" % not_notified_rfiles.count() )

        for rfile in not_notified_rfiles:

            file_desc = serialize_internalfile(rfile.internalfile)

            context_desc = admin.admin_serialize_context(rfile.internalfile.internaltip.context)
            assert context_desc.has_key('name')

            receiver_desc = admin.admin_serialize_receiver(rfile.receiver)
            assert receiver_desc.has_key('notification_fields')

            if not rfile.receiver.notification_fields.has_key('mail_address'):
                log.debug("Receiver %s lack of email address!" % rfile.receiver.name)
                # this is actually impossible, but a check is never bad
                continue

            event = Event(type=u'file', trigger='File',
                notification_settings=self.notification_settings,
                trigger_info=file_desc,
                node_info=node_desc,
                receiver_info=receiver_desc,
                context_info=context_desc,
                plugin=plugin)

            events.append(((unicode(rfile.id), unicode(rfile.receiver.id)), event))

        return events

    @transact
    def receiverfile_notification_succeeded(self, store, result, receiverfile_id, receiver_id):
        """
        This is called when the Receiver File notification has succeeded
        """
        rfile = store.find(models.ReceiverFile, models.ReceiverFile.id == receiverfile_id).one()
        receiver = store.find(models.Receiver, models.Receiver.id == receiver_id).one()

        if not rfile:
            raise errors.FileGusNotFound

        log.debug("+[Success] Notification of receiverfile %s for reciever %s" % (rfile.internalfile.name, receiver.username))
        rfile.mark = models.ReceiverFile._marker[1] # 'notified'

    @transact
    def receiverfile_notification_failed(self, store, failure, receiverfile_id, receiver_id):
        """
        This is called when the Receiver File notification has failed.
        """
        rfile = store.find(models.ReceiverFile, models.ReceiverFile.id == receiverfile_id).one()
        receiver = store.find(models.Receiver, models.Receiver.id == receiver_id).one()

        if not rfile:
            raise errors.FileGusNotFound
        if not receiver:
            raise errors.ReceiverGusNotFound

        log.debug("-[Fail] Notification of receiverfile %s for reciever %s" % (rfile.internalfile.name, receiver.username))
        rfile.mark = models.ReceiverFile._marker[2] # 'unable to notify'


    def do_receiverfile_notification(self, receiverfile_events):
        l = []
        for receiverfile_receiver_id, event in receiverfile_events:
            receiverfile_id, receiver_id = receiverfile_receiver_id

            notify = event.plugin.do_notify(event)
            notify.addCallback(self.receiverfile_notification_succeeded, receiverfile_id, receiver_id)
            notify.addErrback(self.receiverfile_notification_failed, receiverfile_id, receiver_id)
            l.append(notify)

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
        file_events = yield self.create_file_notification_events()

        d1 = self.do_tip_notification(tip_events)
        d2 = self.do_comment_notification(comment_events)
        d3 = self.do_receiverfile_notification(file_events)

        yield DeferredList([d1, d2, d3], consumeErrors=True)
