# -*- coding: utf-8 -*-
# Implement the notification of new submissions
import copy

from storm.expr import In

from twisted.internet import defer, reactor, threads

from globaleaks import models
from globaleaks.handlers.admin.context import admin_serialize_context
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.rtip import serialize_rtip, serialize_message, serialize_comment
from globaleaks.handlers.user import user_serialize_user
from globaleaks.jobs.base import NetLoopingJob
from globaleaks.orm import transact, transact_sync
from globaleaks.security import encrypt_message
from globaleaks.state import State
from globaleaks.utils.mailutils import sendmail
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import log


XTIDX = 1


trigger_template_map = {
    'ReceiverTip': u'tip',
    'Message': u'message',
    'Comment': u'comment',
    'ReceiverFile': u'file'
}


trigger_model_map = {
    'ReceiverTip': models.ReceiverTip,
    'Message': models.Message,
    'Comment': models.Comment,
    'ReceiverFile': models.ReceiverFile
}


class MailGenerator(object):
    def __init__(self):
        self.cache = {}

    def serialize_config(self, store, key, language):
        cache_key = key + '-' + language
        cache_obj = None

        if cache_key not in self.cache:
            if key == 'node':
                cache_obj = db_admin_serialize_node(store, XTIDX, language)
            elif key == 'notification':
                cache_obj = db_get_notification(store, language)

            self.cache[cache_key] = cache_obj

        return self.cache[cache_key]

    def serialize_obj(self, store, key, obj, language):
        obj_id = obj.id

        cache_key = key + '-' + obj_id + '-' + language
        cache_obj = None

        if cache_key not in self.cache:
            if key == 'user':
                cache_obj = user_serialize_user(store, obj, language)
            elif key == 'context':
                cache_obj = admin_serialize_context(store, obj, language)
            elif key == 'tip':
                itip = store.find(models.InternalTip, id=obj.internaltip_id).one()
                cache_obj = serialize_rtip(store, obj, itip, language)
            elif key == 'message':
                cache_obj = serialize_message(store, obj)
            elif key == 'comment':
                cache_obj = serialize_comment(store, obj)
            elif key == 'file':
                cache_obj = models.serializers.serialize_ifile(store, obj)

            self.cache[cache_key] = cache_obj

        return self.cache[cache_key]

    def process_ReceiverTip(self, store, rtip, data):
        user, context = store.find((models.User, models.Context),
                                   models.User.id == rtip.receiver_id,
                                   models.InternalTip.id == rtip.internaltip_id,
                                   models.Context.id == models.InternalTip.context_id).one()

        data['user'] = self.serialize_obj(store, 'user', user, user.language)
        data['tip'] = self.serialize_obj(store, 'tip', rtip, user.language)
        data['context'] = self.serialize_obj(store, 'context', context, user.language)

        self.process_mail_creation(store, data)

    def process_Message(self, store, message, data):
        # if the message is destinated to the whistleblower no mail should be sent
        if message.type == u"receiver":
            return

        user, context, rtip = store.find((models.User, models.Context, models.ReceiverTip),
                                         models.User.id == models.ReceiverTip.receiver_id,
                                         models.ReceiverTip.id == models.Message.receivertip_id,
                                         models.Context.id == models.InternalTip.context_id,
                                         models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                         models.Message.id == message.id).one()

        data['user'] = self.serialize_obj(store, 'user', user, user.language)
        data['tip'] = self.serialize_obj(store, 'tip', rtip, user.language)
        data['context'] = self.serialize_obj(store, 'context', context, user.language)
        data['message'] = self.serialize_obj(store, 'message', message, user.language)

        self.process_mail_creation(store, data)

    def process_Comment(self, store, comment, data):
        for user, context, rtip in store.find((models.User, models.Context, models.ReceiverTip),
                                              models.User.id == models.ReceiverTip.receiver_id,
                                              models.ReceiverTip.internaltip_id == comment.internaltip_id,
                                              models.Context.id == models.InternalTip.context_id,
                                              models.InternalTip.id == comment.internaltip_id,
                                              models.ReceiverTip.internaltip_id == comment.internaltip_id):

            # avoid to send emails to the receiver that written the comment
            if comment.author_id == rtip.receiver_id:
                continue

            dataX = copy.deepcopy(data)
            dataX['user'] = self.serialize_obj(store, 'user', user, user.language)
            dataX['tip'] = self.serialize_obj(store, 'tip', rtip, user.language)
            dataX['context'] = self.serialize_obj(store, 'context', context, user.language)
            dataX['comment'] = self.serialize_obj(store, 'comment', comment, user.language)

            self.process_mail_creation(store, dataX)

    def process_ReceiverFile(self, store, rfile, data):
        user, context, rtip, ifile = store.find((models.User, models.Context, models.ReceiverTip, models.InternalFile),
                                                models.User.id == models.ReceiverTip.receiver_id,
                                                models.InternalFile.id == rfile.internalfile_id,
                                                models.InternalTip.id == models.InternalFile.internaltip_id,
                                                models.ReceiverTip.id == rfile.receivertip_id,
                                                models.Context.id == models.InternalTip.context_id).one()

        # avoid sending an email for the files that have been loaded during the initial submission
        if ifile.submission:
            return

        data['user'] = self.serialize_obj(store, 'user', user, user.language)
        data['tip'] = self.serialize_obj(store, 'tip', rtip, user.language)
        data['user'] = self.serialize_obj(store, 'user', user, user.language)
        data['context'] = self.serialize_obj(store, 'context', context, user.language)
        data['file'] = self.serialize_obj(store, 'file', ifile, user.language)

        self.process_mail_creation(store, data)

    def process_mail_creation(self, store, data):
        user_id = data['user']['id']

        # Do not spool emails if the receiver has opted out of ntfns for this tip.
        if not data['tip']['enable_notifications']:
            log.debug("Discarding emails for %s due to receiver's preference.", user_id)
            return

        # https://github.com/globaleaks/GlobaLeaks/issues/798
        # TODO: the current solution is global and configurable only by the admin
        sent_emails = State.get_mail_counter(user_id)
        if sent_emails >= State.tenant_cache[1].notif.notification_threshold_per_hour:
            log.debug("Discarding emails for receiver %s due to threshold already exceeded for the current hour",
                      user_id)
            return

        State.increment_mail_counter(user_id)
        if sent_emails >= State.tenant_cache[1].notif.notification_threshold_per_hour:
            log.info("Reached threshold of %d emails with limit of %d for receiver %s",
                     sent_emails,
                     State.tenant_cache[1].notif.notification_threshold_per_hour,
                     user_id)

            # simply changing the type of the notification causes
            # to send the notification_limit_reached
            data['type'] = u'receiver_notification_limit_reached'

        data['notification'] = self.serialize_config(store, 'notification', data['user']['language'])
        data['node'] = self.serialize_config(store, 'node', data['user']['language'])

        if not data['node']['allow_unencrypted'] and len(data['user']['pgp_key_public']) == 0:
            return

        subject, body = Templating().get_mail_subject_and_body(data)

        # If the receiver has encryption enabled encrypt the mail body
        if data['user']['pgp_key_public']:
            body = encrypt_message(data['user']['pgp_key_public'], body)

        store.add(models.Mail({
            'address': data['user']['mail_address'],
            'subject': subject,
            'body': body
        }))


    @transact_sync
    def generate(self, store):
        for trigger in ['ReceiverTip', 'Comment', 'Message', 'ReceiverFile']:
            model = trigger_model_map[trigger]

            if State.tenant_cache[1].notif.disable_receiver_notification_emails:
                store.find(model, new=True).set(new=False)
                continue

            elements = store.find(model, new=True)
            for element in elements:
                element.new = False

                data = {
                    'type': trigger_template_map[trigger]
                }

                getattr(self, 'process_%s' % trigger)(store, element, data)

            count = elements.count()
            if count > 0:
                log.debug("Notification: generated %d notifications of type %s",
                          count, trigger)


@transact_sync
def delete_sent_mails(store, mail_ids):
    store.find(models.Mail, In(models.Mail.id, mail_ids)).remove()


@transact_sync
def get_mails_from_the_pool(store):
    ret = []

    store.find(models.Mail, models.Mail.processing_attempts > 9).remove()

    for mail in store.find(models.Mail):
        mail.processing_attempts += 1

        ret.append({
            'id': mail.id,
            'address': mail.address,
            'subject': mail.subject,
            'body': mail.body
        })

    return ret


class NotificationSchedule(NetLoopingJob):
    name = "Notification"
    interval = 5
    monitor_interval = 3 * 60
    mails_to_delete = []

    @defer.inlineCallbacks
    def sendmail(self, mail):
        success = yield sendmail(mail['address'], mail['subject'], mail['body'])
        if success:
            self.mails_to_delete.append(mail['id'])

    def spool_emails(self):
        for mail in get_mails_from_the_pool():
            threads.blockingCallFromThread(reactor, self.sendmail, mail)

        delete_sent_mails(self.mails_to_delete)

    def operation(self):
        del self.mails_to_delete[:]

        MailGenerator().generate()

        return self.spool_emails()
