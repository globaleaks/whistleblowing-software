#
# Notification
# ************
#
# This is in fact Mail Notification Plugin, that supports the simplest Mail notification
# operations.
# When new Notification/Delivery will starts to exists, this code would come back to be
# one of the various plugins (used by default, but still an optional adoptions)

from globaleaks.utils.utility import log, very_pretty_date_time
from globaleaks.utils.mailutils import sendmail, collapse_mail_content, rfc822_date
from globaleaks.plugins.base import Notification
from globaleaks.security import GLBGPG
from globaleaks.models import Receiver
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

    def validate_admin_opt(self, pushed_af):
        fields = ['server', 'port', 'username', 'password']
        if all(field in pushed_af for field in fields):
            return True
        else:
            log.info('invalid mail settings for admin')
            return False

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        log.debug("[%s] receiver_fields %s (with admin %s)" % ( self.__class__.__name__, receiver_fields, admin_fields))
        return True


    def _iterkeywords(self, template, keywords):
        if isinstance(template, dict):
            partial_template = template[GLSetting.memory_copy.default_language]
        else:
            partial_template = template
            # this is wrong!

        for key, var in keywords.iteritems():
            partial_template = partial_template.replace(key, var)

        return partial_template


    # XXX shall be moved in notification_sched ? with the event selection ?
    # ---> yes!
    def format_template(self, template, event_dicts):
        """
        TODO use http://docs.python.org/2/library/email
        """

        node_desc = event_dicts.node_info
        assert node_desc.has_key('name')
        receiver_desc = event_dicts.receiver_info
        assert receiver_desc.has_key('name')
        context_desc = event_dicts.context_info
        assert context_desc.has_key('name')

        template_keyword = {
            '%NodeName%': node_desc['name'],
            '%HiddenService%': node_desc['hidden_service'],
            '%PublicSite%': node_desc['public_site'],
            '%ReceiverName%': receiver_desc['name'],
            '%ReceiverUsername%': receiver_desc['username'],
            # context_name contains localized data, ad the moment
            # exported only with default language, because Receiver
            # can't yet configure its hown lang.
            '%ContextName%' : context_desc['name'],
        }

        if event_dicts.type == u'tip':

            tip_template_keyword = {}

            if len(node_desc['hidden_service']):
                tip_template_keyword.update({
                    '%TipTorURL%':
                        '%s/#/status/%s' %
                            ( node_desc['hidden_service'],
                              event_dicts.trigger_info['id']),
                    })
            else:
                tip_template_keyword.update({
                    '%TipTorURL%':
                        'ADMIN, CONFIGURE YOUR HIDDEN SERVICE (Advanced configuration)!'
                    })

            if not GLSetting.memory_copy.tor2web_tip:
                tip_template_keyword.update({
                    '%TipT2WURL%': "Ask to your admin about Tor"})
                    # https://github.com/globaleaks/GlobaLeaks/issues/268
            elif len(node_desc['public_site']):
                tip_template_keyword.update({
                    '%TipT2WURL%':
                        '%s/#/status/%s' %
                            ( node_desc['public_site'],
                              event_dicts.trigger_info['id'] ),
                    })
            else:
                tip_template_keyword.update({
                    '%TipT2WURL%':
                        'ADMIN, CONFIGURE YOUR PUBLIC SITE (Advanced configuration)'
                    })

            tip_template_keyword.update({
                '%EventTime%':
                    very_pretty_date_time(event_dicts.trigger_info['creation_date']),
            })

            partial = self._iterkeywords(template, template_keyword)
            body = self._iterkeywords(partial, tip_template_keyword)
            return body

        if event_dicts.type == u'comment':

            comment_template_keyword = {
                '%CommentSource%': event_dicts.trigger_info['source'],
                '%EventTime%':
                       very_pretty_date_time(event_dicts.trigger_info['creation_date']),
            }

            partial = self._iterkeywords(template, template_keyword)
            body = self._iterkeywords(partial, comment_template_keyword)
            return body

        if event_dicts.type == u'file':

            file_template_keyword = {
                '%FileName%': event_dicts.trigger_info['name'],
                '%EventTime%':
                    very_pretty_date_time(event_dicts.trigger_info['creation_date']),
                '%FileSize%': event_dicts.trigger_info['size'],
                '%FileType%': event_dicts.trigger_info['content_type'],
            }

            partial = self._iterkeywords(template, template_keyword)
            body = self._iterkeywords(partial, file_template_keyword)
            return body

        raise AssertionError("Tip/Comment/File at the moment supported")

    def do_notify(self, event):

        # check if exists the conf
        if not self.validate_admin_opt(event.notification_settings):
            log.info('invalid configuration for admin email!')
            return None

        # At the moment the language used is a system language, not
        # Receiver preferences language ?
        if event.type == u'tip':
            body = self.format_template(
                event.notification_settings['tip_template'], event)
            title = self.format_template(
                event.notification_settings['tip_mail_title'], event)
        elif event.type == u'comment':
            body = self.format_template(
                event.notification_settings['comment_template'], event)
            title = self.format_template(
                event.notification_settings['comment_mail_title'], event)
        elif event.type == u'file':
            body = self.format_template(
                event.notification_settings['file_template'], event)
            title = self.format_template(
                event.notification_settings['file_mail_title'], event)
        else:
            raise NotImplementedError("At the moment, only Tip expected")

        # If the receiver has encryption enabled (for notification), encrypt the mail body
        if event.receiver_info['gpg_key_status'] == Receiver._gpg_types[1] and \
           event.receiver_info['gpg_enable_notification']:

            try:
                gpob = GLBGPG(event.receiver_info)

                if not gpob.validate_key(event.receiver_info['gpg_key_armor']):
                    log.err("unable to validated GPG key for receiver %s" %
                            event.receiver_info['username'])
                    return None

                body = gpob.encrypt_message(body)
                gpob.destroy_environment()

            except Exception as excep:
                log.err("Error in GPG interface object (for %s: %s)! (notification+encryption)" %
                        (event.receiver_info['username'], str(excep) ))
                return None

        receiver_mail = event.receiver_info['notification_fields']['mail_address']

        # Compose the email having the system+subject+recipient data
        mail_building = ["Date: %s" % rfc822_date(),
                         "From: \"%s\" <%s>" % (
                             GLSetting.memory_copy.notif_source_name,
                             GLSetting.memory_copy.notif_source_email ),
                         "To: %s" % receiver_mail,
                         "Subject: %s" % title,
                         "Content-Type: text/plain; charset=ISO-8859-1",
                         "Content-Transfer-Encoding: 8bit",
                         None,
                         body]

        # XXX here can be catch the subject (may change if encrypted or whatever)

        # appending 'None' it's used to mean "\n" without being escaped by collapse_mail_content

        message = collapse_mail_content(mail_building)

        if not message:
            log.err("Unable to format (and then notify!) email for %s" % receiver_mail)
            log.debug(mail_building)
            return None

        self.finished = self.mail_flush(event.notification_settings['source_email'],
                                        [ receiver_mail ], message, event)

        return self.finished

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
                        from_address= from_address,
                        to_address= to_address,
                        message_file=message_file,
                        smtp_host=GLSetting.memory_copy.notif_server,
                        smtp_port=GLSetting.memory_copy.notif_port,
                        security=GLSetting.memory_copy.notif_security,
                        event=event)

