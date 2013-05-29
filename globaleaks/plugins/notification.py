#
# Notification
# ************
#
# This is in fact Mail Notification Plugin, that supports the simplest Mail notification
# operations.
# When new Notification/Delivery will starts to exists, this code would come back to be
# one of the various plugins (used by default, but still an optional adoptions)

from cyclone import mail

from globaleaks.utils import log, sendmail
from globaleaks.plugins.base import Notification
from globaleaks.security import gpg_encrypt
from globaleaks.models import Receiver

class MailNotification(Notification):

    plugin_name = u'Mail'
    plugin_type = u'notification'
    plugin_description = u"Mail notification, with encryption supports"

    # This declaration is not more used, because hardcoded
    # admin_fields = {'server' : 'text', 'port': 'int', 'password' : 'text', 'username':'text', 'ssl' : 'bool' }
    # receiver_fields = {'mail_address' : 'text'}
    # But at the first presence of a different notification plugin, need to be resumed and
    # integrated in the validation messages.

    def __init__(self):
        self.host = None
        self.port = None
        self.username = None
        self.password = None
        self.security = None
        self.finished = None

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
        partial_template = template

        for key, var in keywords.iteritems():
            partial_template =  partial_template.replace(key, var)

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

            if len(node_desc['public_site']):
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
                '%EventTime%': event_dicts.trigger_info['creation_date'],
            })


            partial = self._iterkeywords(template, template_keyword)
            body = self._iterkeywords(partial, tip_template_keyword)
            return body

        if event_dicts.type == u'comment':

            comment_template_keyword = {
                '%CommentSource%': event_dicts.trigger_info['source'],
                '%EventTime%': event_dicts.trigger_info['creation_date'],
            }

            partial = self._iterkeywords(template, template_keyword)
            body = self._iterkeywords(partial, comment_template_keyword)
            return body

        if event_dicts.type == u'file':

            file_template_keyword = {
                '%FileName%': event_dicts.trigger_info['name'],
                '%EventTime%': event_dicts.trigger_info['creation_date'],
                '%FileSize%': event_dicts.trigger_info['size'],
                '%FileType%': event_dicts.trigger_info['content_type'],
            }

            partial = self._iterkeywords(template, template_keyword)
            body = self._iterkeywords(partial, file_template_keyword)
            return body

        raise AssertionError("Only Tip and Comment at the moment supported")

    def do_notify(self, event):

        # check if exists the conf
        if not self.validate_admin_opt(event.notification_settings):
            log.info('invalid configuration for admin email!')
            return None

        # XXX title maybe moved in Admin GUI and digest implemented (beta)
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

        # If the receiver has encryption enabled, change the body encrypting
        if event.receiver_info['gpg_key_status'] == Receiver._gpg_types[1]:
            body = gpg_encrypt(body, event.receiver_info)

        self.host = str(event.notification_settings['server'])
        self.port = int(event.notification_settings['port'])
        self.username = str(event.notification_settings['username'])
        self.password = str(event.notification_settings['password'])
        self.security = str(event.notification_settings['security'])

        # to_addres maybe a list of addresses
        receiver_mail = event.receiver_info['notification_fields']['mail_address']
        to_addrs = [ receiver_mail ]

        # Compose the email having the system+subject+recipient data
        message = mail.Message(from_addr=self.username,
                               to_addrs=to_addrs,
                               subject=title,
                               message=body)

        self.finished = self.mail_flush(self.username, self.password,
                                      message.from_addr, message.to_addrs, message.render(),
                                      self.host, self.port, self.security, event)
        log.debug('Email: connecting to [%s:%d] to notify %s using [%s]' %
                  (self.host, self.port, receiver_mail, self.security))
        return self.finished

    def mail_flush(self, authentication_username, authentication_password, from_address,
                 to_address, message_file, smtp_host, smtp_port, security, event):
        return sendmail(authentication_username, authentication_password, from_address,
                        to_address, message_file, smtp_host, smtp_port, security, event)

