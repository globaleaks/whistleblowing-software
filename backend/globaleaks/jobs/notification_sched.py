# -*- encoding: utf-8 -*-
#
#   notification_sched
#   ******************
#
import copy

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.orm import transact
from globaleaks.handlers.admin.context import admin_serialize_context
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.receiver import admin_serialize_receiver
from globaleaks.handlers.rtip import serialize_rtip, serialize_message, serialize_comment
from globaleaks.handlers.submission import serialize_internalfile
from globaleaks.jobs.base import GLJob
from globaleaks.security import GLBPGP
from globaleaks.settings import GLSettings
from globaleaks.utils.mailutils import sendmail
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import log


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


def serialize_content(store, cache, key, obj, language):
    obj_id = obj.id

    cache_key = key + obj_id + language

    if cache_key not in cache:
        if key == 'tip':
             cache_obj = serialize_rtip(store, obj, language)
        elif key == 'context':
             cache_obj = admin_serialize_context(store, obj, language)
        elif key == 'receiver':
             cache_obj = admin_serialize_receiver(obj, language)
        elif key == 'message':
             cache_obj = serialize_message(obj)
        elif key == 'comment':
             cache_obj = serialize_comment(obj)
        elif key == 'file':
             cache_obj = serialize_internalfile(obj)

        cache[cache_key] = cache_obj

    return copy.deepcopy(cache[cache_key])


class MailGenerator(object):
    def __init__(self):
        self.cache = {}

    def process_ReceiverTip(self, store, rtip, data):
        language = rtip.receiver.user.language

        data['tip'] = serialize_content(store, self.cache, 'tip', rtip, language)
        data['context'] = serialize_content(store, self.cache, 'context', rtip.internaltip.context, language)
        data['receiver'] = serialize_content(store, self.cache, 'receiver', rtip.receiver, language)

        self.process_mail_creation(store, data)


    def process_Message(self, store, message, data):
        # if the message is destinated to the whistleblower no mail should be sent
        if message.type == u"receiver":
            return

        language = message.receivertip.receiver.user.language

        data['tip'] = serialize_content(store, self.cache, 'tip', message.receivertip, language)
        data['context'] = serialize_content(store, self.cache, 'context', message.receivertip.internaltip.context, language)
        data['receiver'] = serialize_content(store, self.cache, 'receiver', message.receivertip.receiver, language)
        data['message'] = serialize_content(store, self.cache, 'message', message, language)

        self.process_mail_creation(store, data)


    def process_Comment(self, store, comment, data):
        for rtip in comment.internaltip.receivertips:
            if comment.type == u'receiver' and comment.author == rtip.receiver.user.name:
                continue

            language = rtip.receiver.user.language

            dataX = copy.deepcopy(data)
            dataX['tip'] = serialize_content(store, self.cache, 'tip', rtip, language)
            dataX['context'] = serialize_content(store, self.cache, 'context', comment.internaltip.context, language)
            dataX['receiver'] = serialize_content(store, self.cache, 'receiver', rtip.receiver, language)
            dataX['comment'] = serialize_content(store, self.cache, 'comment', comment, language)

            self.process_mail_creation(store, dataX)


    def process_ReceiverFile(self, store, rfile, data):
        language = rfile.receiver.user.language

        data['tip'] = serialize_content(store, self.cache, 'tip', rfile.receivertip, language)
        data['context'] = serialize_content(store, self.cache, 'context', rfile.internalfile.internaltip.context, language)
        data['receiver'] = serialize_content(store, self.cache, 'receiver', rfile.receiver, language)
        data['file'] = serialize_content(store, self.cache, 'file', rfile.internalfile, language)

        self.process_mail_creation(store, data)


    def process_mail_creation(self, store, data):
        # https://github.com/globaleaks/GlobaLeaks/issues/798
        # TODO: the current solution is global and configurable only by the admin
        receiver_id = data['receiver']['id']
        sent_emails = GLSettings.get_mail_counter(receiver_id)
        if sent_emails >= GLSettings.memory_copy.notification_threshold_per_hour:
            log.debug("Discarding emails for receiver %s due to threshold already exceeded for the current hour" %
                      receiver_id)
            return

        GLSettings.increment_mail_counter(receiver_id)
        if sent_emails >= GLSettings.memory_copy.notification_threshold_per_hour:
            log.info("Reached threshold of %d emails with limit of %d for receiver %s" % (
                     sent_emails,
                     GLSettings.memory_copy.notification_threshold_per_hour,
                     receiver_id)
            )

            # simply changing the type of the notification causes
            # to send the notification_limit_reached
            data['type'] = u'receiver_notification_limit_reached'

        data['notification'] = db_get_notification(store, data['receiver']['language'])
        data['node'] = db_admin_serialize_node(store, data['receiver']['language'])

        subject, body = Templating().get_mail_subject_and_body(data)

        # If the receiver has encryption enabled encrypt the mail body
        if data['receiver']['pgp_key_status'] == u'enabled':
            gpob = GLBPGP()

            try:
                gpob.load_key(data['receiver']['pgp_key_public'])
                body = gpob.encrypt_message(data['receiver']['pgp_key_fingerprint'], body)
            except Exception as excep:
                log.err("Error in PGP interface object (for %s: %s)! (notification+encryption)" %
                        (data['receiver']['username'], str(excep)))

                return
            finally:
                # the finally statement is always called also if
                # except contains a return or a raise
                gpob.destroy_environment()


        mail = models.Mail({
            'address': data['receiver']['mail_address'],
            'subject': subject,
            'body': body
        })

        store.add(mail)


    @transact
    def process_data(self, store, trigger):
        model = trigger_model_map[trigger]

        elements = store.find(model, model.new == True)
        for element in elements:
            # Mark data as handled as first step;
            # For resiliency reasons it's better to be sure that the
            # state machine move forward, than having starving datas
            # due to possible exceptions in handling
            element.new = False

            if GLSettings.memory_copy.disable_receiver_notification_emails:
                continue 

            data = {
                'type': trigger_template_map[trigger]
            }

            getattr(self, 'process_%s' % trigger)(store, element, data)

        count = elements.count()
        if count > 0:
            log.debug("Notification: generated %d notificatins of type %s" %
                      (count, trigger))


class NotificationSchedule(GLJob):
    name = "Notification"
    monitor_time = 1800

    @transact
    def get_mails_from_the_pool(self, store):
        ret = []

        for mail in store.find(models.Mail):
            ret.append({
                'id': mail.id,
                'address': mail.address,
                'subject': mail.subject,
                'body': mail.body
            })

            mail.processing_attempts += 1
            if mail.processing_attempts > 9:
                store.remove(mail)

        return ret

    @inlineCallbacks
    def operation(self):
        @transact
        def delete_sent_mail(store, mail_id):
            store.find(models.Mail, models.Mail.id == mail_id).remove()

        @inlineCallbacks
        def _success_callback(result, mail_id):
            yield delete_sent_mail(mail_id)

        def _failure_callback(failure, mail_id):
            pass

        mail_generator = MailGenerator()
        for trigger in ['ReceiverTip', 'Comment', 'Message', 'ReceiverFile']:
            yield mail_generator.process_data(trigger)

        mails = yield self.get_mails_from_the_pool()
        for mail in mails:
            sendmail_deferred = sendmail(mail['address'], mail['subject'], mail['body'])
            sendmail_deferred.addCallbacks(_success_callback, _failure_callback,
                                           callbackArgs=(mail['id'],), errbackArgs=(mail['id'],))
            yield sendmail_deferred
