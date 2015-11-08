# -*- coding: UTF-8
# notification.py
# ************

from collections import namedtuple

from twisted.internet.defer import inlineCallbacks, fail

from globaleaks.orm import transact
from globaleaks.models import EventLogs
from globaleaks.utils.utility import log
from globaleaks.utils.mailutils import sendmail, MIME_mail_build
from globaleaks.utils.templating import Templating
from globaleaks.security import GLBPGP
from globaleaks.settings import GLSettings


Event = namedtuple('Event',
                   ['type', 'trigger', 'tip_info', 'node_info',
                    'receiver_info', 'context_info',
                    'subevent_info', 'do_mail'])


@transact
def update_event_notification_status(store, event_id, mail_sent):
    attempts_limit = GLSettings.mail_attempts_limit
    event = store.find(EventLogs, EventLogs.id == event_id).one()
    if event:
        event.mail_attempts += 1
        if mail_sent:
            event.mail_sent = True
            log.debug("SUCCESS:: Marked as notified event %s of type [%s]" % (event.id, event.title))
        elif event.mail_attempts >= attempts_limit:
            event.mail_sent = True
            log.debug("FAILURE: Notification for event %s of type %s reached limit of #%d attempts without success" % \
                       (event.id, event.title, attempts_limit))
        else:
            log.debug("FAILURE: Notification for event %s of type %s (attempt #%d)" % \
                       (event.id, event.title, event.mail_attempts))


class MailNotification(object):
    def get_mail_subject_and_body(self, event):
        def replace_variables(template, event):
            return Templating().format_template(template, event)

        if event.type in [u'tip', u'file', u'comment', u'message', u'tip_expiration', 'receiver_notification_limit_reached']:
            subject_template = event.notification_settings[event.type + '_mail_title']
            body_template = event.notification_settings[event.type + '_mail_template']
        else:
            raise NotImplementedError("This event_type (%s) is not supported" % event.type)

        if event.type in [u'tip', u'file', u'comment', u'message', u'tip_expiration']:
            subject_template = "%TipNum%%TipLabel%" + subject_template

        subject = replace_variables(subject_template, event)
        body = replace_variables(body_template, event)

        return subject, body

    @staticmethod
    def mail_flush(from_address, to_address, message_file, event):
        """
        This function just wrap the sendmail call, using the system memory variables.
        """
        log.debug('Email: connecting to [%s:%d] to notify %s using [%s]' %
                  (GLSettings.memory_copy.notif_server,
                   GLSettings.memory_copy.notif_port,
                   to_address[0], GLSettings.memory_copy.notif_security))

        return sendmail(authentication_username=GLSettings.memory_copy.notif_username,
                        authentication_password=GLSettings.memory_copy.notif_password,
                        from_address=from_address,
                        to_address=to_address,
                        message_file=message_file,
                        smtp_host=GLSettings.memory_copy.notif_server,
                        smtp_port=GLSettings.memory_copy.notif_port,
                        security=GLSettings.memory_copy.notif_security,
                        event=event)

    def do_notify(self, event):
        if event.type == 'digest':
            body = event.tip_info['body']
            title = event.tip_info['title']
        else:
            title, body = self.get_mail_subject_and_body(event)

        # If the receiver has encryption enabled (for notification), encrypt the mail body
        if event.receiver_info['pgp_key_status'] == u'enabled':
            gpob = GLBPGP()
            try:
                gpob.load_key(event.receiver_info['pgp_key_public'])
                body = gpob.encrypt_message(event.receiver_info['pgp_key_fingerprint'], body)
            except Exception as excep:
                log.err("Error in PGP interface object (for %s: %s)! (notification+encryption)" %
                        (event.receiver_info['username'], str(excep)))

                # On this condition (PGP enabled but key invalid) the only
                # thing to do is to return None;
                # It will be duty of the PGP check schedule will disable the key
                # and advise the user and the admin about that action.
                return fail(None)
            finally:
                # the finally statement is always called also if
                # except contains a return or a raise
                gpob.destroy_environment()

        receiver_mail = event.receiver_info['mail_address']

        message = MIME_mail_build(GLSettings.memory_copy.notif_source_name,
                                  GLSettings.memory_copy.notif_source_email,
                                  event.receiver_info['name'],
                                  receiver_mail,
                                  title,
                                  body)

        return self.mail_flush(event.notification_settings['source_email'],
                               [receiver_mail], message, event)

    @inlineCallbacks
    def do_every_notification(self, eventOD):
        notify = self.do_notify(eventOD)
        notify.addCallbacks(self.every_notification_succeeded, self.every_notification_failed,
                            callbackArgs=(eventOD.orm_id,), errbackArgs=(eventOD.orm_id,))
        yield notify

    @inlineCallbacks
    def every_notification_succeeded(self, result, event_id):
        if event_id:
            log.debug("Mail delivered correctly for event %s" % (event_id))
            yield update_event_notification_status(event_id, True)
        else:
            log.debug("Mail (Digest|Anomaly) correctly sent")

    @inlineCallbacks
    def every_notification_failed(self, failure, event_id):
        if event_id:
            log.err("Mail delivery failure for event %s" % (event_id))
            yield update_event_notification_status(event_id, False)
        else:
            log.err("Mail (Digest|Anomaly) error")
