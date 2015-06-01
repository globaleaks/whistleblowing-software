# -*- coding: UTF-8
#
# Notification
# ************
#
# This is in fact Mail Notification Plugin, that supports the simplest Mail notification
# operations.
# When new Notification/Delivery will starts to exists, this code would come back to be
# one of the various plugins (used by default, but still an optional adoptions)

from globaleaks.utils.utility import log
from globaleaks.utils.mailutils import sendmail, MIME_mail_build
from globaleaks.utils.templating import Templating
from globaleaks.plugins.base import Notification
from globaleaks.security import GLBPGP
from globaleaks.settings import GLSetting


class MailNotification(Notification):
    plugin_name = u'Mail'
    plugin_type = u'notification'
    plugin_description = u"Mail notification, with encryption supports"

    # This declaration is not more used, because hardcoded
    # admin_fields = {'server' : 'text', 'port': 'int', 'password' : 'text', 'username':'text', 'ssl' : 'bool' }
    # receiver_fields = {'mail_address' : 'text'}
    # But at the first presence of a different notification plugin, need to be resumed and
    # integrated in the validation messages.

    def validate_admin_opt(self, pushed_ao):
        fields = ['server', 'port', 'username', 'password']
        if all(field in pushed_ao for field in fields):
            return True
        else:
            return False

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        log.debug("[%s] receiver_fields %s (with admin %s)" % ( self.__class__.__name__, receiver_fields, admin_fields))
        return True


    def get_mail_body_and_title(self, event):
        # This function, that probably can be optimized with some kind of pattern
        # return body and title computed for the event + template + keywords compute
        if event.type == u'tip':
            body = Templating().format_template(
                event.notification_settings['tip_mail_template'], event)
            title = Templating().format_template(
                event.notification_settings['tip_mail_title'], event)
        elif event.type == u'file':
            body = Templating().format_template(
                event.notification_settings['file_mail_template'], event)
            title = Templating().format_template(
                event.notification_settings['file_mail_title'], event)
        elif event.type == u'comment':
            body = Templating().format_template(
                event.notification_settings['comment_mail_template'], event)
            title = Templating().format_template(
                event.notification_settings['comment_mail_title'], event)
        elif event.type == u'message':
            body = Templating().format_template(
                event.notification_settings['message_mail_template'], event)
            title = Templating().format_template(
                event.notification_settings['message_mail_title'], event)
        elif event.type == u'upcoming_tip_expiration':
            body = Templating().format_template(
                event.notification_settings['tip_expiration_template'], event)
            title = Templating().format_template(
                event.notification_settings['tip_expiration_mail_title'], event)
        elif event.type == u'receiver_threshold_reached_mail_template':
            body = Templating().format_template(
                event.notification_settings['receiver_threshold_reached_mail_template'], event)
            title = Templating().format_template(
                event.notification_settings['receiver_threshold_reached_mail_title'], event)
        else:
            raise NotImplementedError("This event_type (%s) is not supported" % event.type)

        return body, title


    def do_notify(self, event):

        if event.type == 'digest':
            body = event.tip_info['body']
            title = event.tip_info['title']
        else:
            body, title = self.get_mail_body_and_title(event)

        if not self.validate_admin_opt(event.notification_settings):
            log.err('Invalid Mail Settings, no mail can be deliver')
            return None

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

        message = MIME_mail_build(GLSetting.memory_copy.notif_source_name,
                                  GLSetting.memory_copy.notif_source_email,
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
                  (GLSetting.memory_copy.notif_server,
                   GLSetting.memory_copy.notif_port,
                   to_address[0], GLSetting.memory_copy.notif_security))

        return sendmail(authentication_username=GLSetting.memory_copy.notif_username,
                        authentication_password=GLSetting.memory_copy.notif_password,
                        from_address=from_address,
                        to_address=to_address,
                        message_file=message_file,
                        smtp_host=GLSetting.memory_copy.notif_server,
                        smtp_port=GLSetting.memory_copy.notif_port,
                        security=GLSetting.memory_copy.notif_security,
                        event=event)

