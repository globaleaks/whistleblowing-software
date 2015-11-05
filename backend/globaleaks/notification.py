# -*- coding: UTF-8
# notification.py
# ************

from collections import namedtuple

from twisted.internet.defer import inlineCallbacks, Deferred

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
def mark_event_as_notified(store, event_id):
    """
    """
    evnt = store.find(EventLogs, EventLogs.id == event_id).one()
    if evnt:
        evnt.mail_sent = True
        log.debug("Marked event [%s] as sent" % evnt.title)


class MailNotification(object):
    def get_mail_subject_and_body(self, event):
        def replace_variables(template, event):
            return Templating().format_template(template, event)

        if event.type in [u'tip', u'file', u'comment', u'message', u'tip_expiration', 'receiver_notification_limit_reached']:
            subject = replace_variables(event.notification_settings[event.type + '_mail_title'], event)
            body = replace_variables(event.notification_settings[event.type + '_mail_template'], event)
        else:
            raise NotImplementedError("This event_type (%s) is not supported" % event.type)

        if event.type in [u'tip', u'file', u'comment', u'message', u'tip_expiration']:
            subject = subject

        return subject, body


    def do_notify(self, event):
        if event.type == 'digest':
            body = event.tip_info['body']
            title = event.tip_info['title']
        else:
            body, title = self.get_mail_subject_and_body(event)

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
                return None
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

    @inlineCallbacks
    def do_every_notification(self, eventOD):
        notify = self.do_notify(eventOD)

        if isinstance(notify, Deferred):
            notify.addCallback(self.every_notification_succeeded, eventOD.orm_id)
            notify.addErrback(self.every_notification_failed, eventOD.orm_id)
            yield notify
        else:
            yield self.every_notification_failed(None, eventOD.orm_id)

    @transact
    def every_notification_succeeded(self, store, result, event_id):
        if event_id:
            log.debug("Mail delivered correctly for event %s, [%s]" % (event_id, result))
            yield mark_event_as_notified(event_id)
        else:
            log.debug("Mail (Digest|Anomaly) correctly sent")

    @transact
    def every_notification_failed(self, store, failure, event_id):
        if event_id:
            log.err("Mail delivery failure for event %s (%s)" % (event_id, failure))
            yield mark_event_as_notified(event_id)
        else:
            log.err("Mail (Digest|Anomaly) error")

