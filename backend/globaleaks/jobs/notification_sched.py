# -*- encoding: utf-8 -*-
# Implement the notification of new submissions

import copy

from globaleaks import models
from globaleaks.handlers.admin.context import admin_serialize_context
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.receiver import admin_serialize_receiver
from globaleaks.handlers.rtip import serialize_rtip, serialize_message, serialize_comment
from globaleaks.jobs.base import LoopingJob
from globaleaks.orm import transact, transact_sync
from globaleaks.security import encrypt_message
from globaleaks.settings import GLSettings
from globaleaks.utils.mailutils import sendmail
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import log
from twisted.internet import reactor, threads


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
                cache_obj = db_admin_serialize_node(store, language)
            elif key == 'notification':
                cache_obj = db_get_notification(store, language)

            self.cache[cache_key] = cache_obj

        return self.cache[cache_key]

    def serialize_obj(self, store, key, obj, language):
        obj_id = obj.id

        cache_key = key + '-' + obj_id + '-' + language
        cache_obj = None

        if cache_key not in self.cache:
            if key == 'tip':
                cache_obj = serialize_rtip(store, obj, language)
            elif key == 'context':
                cache_obj = admin_serialize_context(store, obj, language)
            elif key == 'receiver':
                cache_obj = admin_serialize_receiver(store, obj, language)
            elif key == 'message':
                cache_obj = serialize_message(store, obj)
            elif key == 'comment':
                cache_obj = serialize_comment(store, obj)
            elif key == 'file':
                cache_obj = models.serializers.serialize_ifile(store, obj)

            self.cache[cache_key] = cache_obj

        return self.cache[cache_key]

    def process_ReceiverTip(self, store, rtip, data):
        language, context, receiver = store.find((models.User.language, models.Context, models.Receiver),
                                                 models.User.id == models.Receiver.id,
                                                 models.Receiver.id == rtip.receiver_id,
                                                 models.InternalTip.id == rtip.internaltip_id,
                                                 models.Context.id == models.InternalTip.context_id).one()

        data['tip'] = self.serialize_obj(store, 'tip', rtip, language)
        data['context'] = self.serialize_obj(store, 'context', context, language)
        data['receiver'] = self.serialize_obj(store, 'receiver', receiver, language)

        self.process_mail_creation(store, data)

    def process_Message(self, store, message, data):
        # if the message is destinated to the whistleblower no mail should be sent
        if message.type == u"receiver":
            return

        language, context, receiver, rtip = store.find((models.User.language, models.Context, models.Receiver, models.ReceiverTip),
                                                       models.User.id == models.Receiver.id,
                                                       models.Receiver.id == models.ReceiverTip.receiver_id,
                                                       models.ReceiverTip.id == models.Message.receivertip_id,
                                                       models.Context.id == models.InternalTip.context_id,
                                                       models.InternalTip.id == models.ReceiverTip.internaltip_id,
                                                       models.Message.id == message.id).one()

        data['tip'] = self.serialize_obj(store, 'tip', rtip, language)
        data['context'] = self.serialize_obj(store, 'context', context, language)
        data['receiver'] = self.serialize_obj(store, 'receiver', receiver, language)
        data['message'] = self.serialize_obj(store, 'message', message, language)

        self.process_mail_creation(store, data)

    def process_Comment(self, store, comment, data):
        for language, context, receiver, rtip in store.find((models.User.language, models.Context, models.Receiver, models.ReceiverTip),
                                                             models.User.id == models.Receiver.id,
                                                             models.Receiver.id == models.ReceiverTip.receiver_id,
                                                             models.ReceiverTip.internaltip_id == comment.internaltip_id,
                                                             models.Context.id == models.InternalTip.context_id,
                                                             models.InternalTip.id == comment.internaltip_id,
                                                             models.ReceiverTip.internaltip_id == comment.internaltip_id):
            if comment.type == u'receiver' and comment.author_id == rtip.receiver_id:
                continue

            dataX = copy.deepcopy(data)
            dataX['tip'] = self.serialize_obj(store, 'tip', rtip, language)
            dataX['context'] = self.serialize_obj(store, 'context', context, language)
            dataX['receiver'] = self.serialize_obj(store, 'receiver', receiver, language)
            dataX['comment'] = self.serialize_obj(store, 'comment', comment, language)

            self.process_mail_creation(store, dataX)

    def process_ReceiverFile(self, store, rfile, data):
        language, context, receiver, rtip, ifile = store.find((models.User.language, models.Context, models.Receiver, models.ReceiverTip, models.InternalFile),
                                                              models.User.id == models.Receiver.id,
                                                              models.Receiver.id == models.ReceiverTip.receiver_id,
                                                              models.InternalFile.id == rfile.internalfile_id,
                                                              models.InternalTip.id == models.InternalFile.internaltip_id,
                                                              models.ReceiverTip.id == rfile.receivertip_id,
                                                              models.Context.id == models.InternalTip.context_id).one()

        # avoid sending an email for the files that have been loaded during the initial submission
        if ifile.submission:
            return

        data['tip'] = self.serialize_obj(store, 'tip', rtip, language)
        data['context'] = self.serialize_obj(store, 'context', context, language)
        data['receiver'] = self.serialize_obj(store, 'receiver', receiver, language)
        data['file'] = self.serialize_obj(store, 'file', ifile, language)

        self.process_mail_creation(store, data)

    def process_mail_creation(self, store, data):
        receiver_id = data['receiver']['id']

        # Do not spool emails if the receiver has opted out of ntfns for this tip.
        if not data['tip']['enable_notifications']:
          log.debug("Discarding emails for %s due to receiver's preference.", receiver_id)
          return

        # https://github.com/globaleaks/GlobaLeaks/issues/798
        # TODO: the current solution is global and configurable only by the admin
        sent_emails = GLSettings.get_mail_counter(receiver_id)
        if sent_emails >= GLSettings.memory_copy.notif.notification_threshold_per_hour:
            log.debug("Discarding emails for receiver %s due to threshold already exceeded for the current hour",
                      receiver_id)
            return

        GLSettings.increment_mail_counter(receiver_id)
        if sent_emails >= GLSettings.memory_copy.notif.notification_threshold_per_hour:
            log.info("Reached threshold of %d emails with limit of %d for receiver %s",
                     sent_emails,
                     GLSettings.memory_copy.notif.notification_threshold_per_hour,
                     receiver_id)

            # simply changing the type of the notification causes
            # to send the notification_limit_reached
            data['type'] = u'receiver_notification_limit_reached'

        data['notification'] = self.serialize_config(store, 'notification', data['receiver']['language'])
        data['node'] = self.serialize_config(store, 'node', data['receiver']['language'])

        if not data['node']['allow_unencrypted'] and len(data['receiver']['pgp_key_public']) == 0:
            return

        subject, body = Templating().get_mail_subject_and_body(data)

        # If the receiver has encryption enabled encrypt the mail body
        if len(data['receiver']['pgp_key_public']):
            body = encrypt_message(data['receiver']['pgp_key_public'], body)

        store.add(models.Mail({
            'address': data['receiver']['mail_address'],
            'subject': subject,
            'body': body
        }))


    @transact_sync
    def generate(self, store):
        for trigger in ['ReceiverTip', 'Comment', 'Message', 'ReceiverFile']:
            model = trigger_model_map[trigger]

            elements = store.find(model, model.new == True)
            for element in elements:
                element.new = False

                if GLSettings.memory_copy.notif.disable_receiver_notification_emails:
                    continue

                data = {
                    'type': trigger_template_map[trigger]
                }

                getattr(self, 'process_%s' % trigger)(store, element, data)

            count = elements.count()
            if count > 0:
                log.debug("Notification: generated %d notifications of type %s",
                          count, trigger)


@transact
def delete_sent_mail(store, result, mail_id):
    store.find(models.Mail, models.Mail.id == mail_id).remove()


@transact_sync
def get_mails_from_the_pool(store):
    ret = []

    for mail in store.find(models.Mail):
        if mail.processing_attempts > 9:
            store.remove(mail)
            continue

        mail.processing_attempts += 1

        ret.append({
            'id': mail.id,
            'address': mail.address,
            'subject': mail.subject,
            'body': mail.body
        })

    return ret


class NotificationSchedule(LoopingJob):
    name = "Notification"
    interval = 5
    monitor_interval = 3 * 60

    def sendmail(self, mail):
        d = sendmail(mail['address'], mail['subject'], mail['body'])
        d.addCallback(delete_sent_mail, mail['id'])
        return d

    def spool_emails(self):
        mails = get_mails_from_the_pool()
        for mail in mails:
            threads.blockingCallFromThread(reactor, self.sendmail, mail)

    def operation(self):
        MailGenerator().generate()

        self.spool_emails()
