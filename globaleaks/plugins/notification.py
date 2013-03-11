#
# Notification
# ************
#
# This is in fact Mail Notification Plugin, that supports the simplest Mail notification
# operations.
# When new Notification/Delivery will starts to exists, this code would come back to be
# one of the various plugins (used by default, but still an optional adoptions)

from cyclone import mail
from twisted.internet.defer import Deferred
from twisted.mail.smtp import ESMTPSenderFactory
from twisted.internet import reactor, ssl
from twisted.internet.endpoints import TCP4ClientEndpoint
from OpenSSL import SSL

from globaleaks.utils import log
from globaleaks.plugins.base import Notification


class MailNotification(Notification):

    _title = {
            'comment': 'From %ContextName% a new comment in %EventTime%',
            'tip': 'From %ContextName% a new Tip in %EventTime%',
            'file': 'From %ContextName% a new file appended in a tip (%EventTime%, %FileType%)'
    }

    plugin_name = u'Mail'
    plugin_type = u'notification'
    plugin_description = u"Mail notification, with encryption supports"

    # This declaration is not more used, because hardcoded
    # admin_fields = {'server' : 'text', 'port': 'int', 'password' : 'text', 'username':'text', 'ssl' : 'bool' }
    # receiver_fields = {'mail_address' : 'text'}
    # But at the first presence of a different notification plugin, need to be resumed and
    # integrated in the validation messages.


    def __init__(self, notification_settings):
        pass

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

            tip_template_keyword = {
                '%TipTorURL%':
                    'http://%s/#/status/%s' %
                        ( node_desc['hidden_service'],
                          event_dicts.trigger_info['id']),
                '%TipT2WURL%':
                    'https://%s.tor2web.org/#/status/%s' %
                        ( node_desc['hidden_service'][:16],
                          event_dicts.trigger_info['id'] ),
                '%EventTime%': event_dicts.trigger_info['creation_date'],
            }

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

        # TODO atm title is calling the same line, but maybe moved in Admin GUI
        if event.type == u'tip':
            body = self.format_template(
                event.notification_settings['tip_template'], event)
            title = self.format_template(self._title[event.type], event)
        elif event.type == u'comment':
            body = self.format_template(
                event.notification_settings['comment_template'], event)
            title = self.format_template(self._title[event.type], event)
        elif event.type == u'file':
            body = self.format_template(
                event.notification_settings['file_template'], event)
            title = self.format_template(self._title[event.type], event)
        else:
            raise NotImplementedError("At the moment, only Tip expected")

        self.host = event.notification_settings['server']
        self.port = int(event.notification_settings['port'])
        self.username = event.notification_settings['username']
        self.password = event.notification_settings['password']
        self.security = event.notification_settings['security']
        self.finished = Deferred()

        # to_addres maybe a list of addresses
        receiver_mail= event.receiver_info['notification_fields']['mail_address']
        to_addrs = [ receiver_mail ]

        # Compose the email having the system+subject+recipient data
        message = mail.Message(from_addr=self.username,
                               to_addrs=to_addrs,
                               subject=title,
                               message=body )
        self.send(message)
        log.debug('Email: connecting to [%s] for deliver to %s' % (self.host, receiver_mail))
        return self.finished

    def send(self, message):
        if self.security == 'SSL':
            contextFactory = ssl.ClientContextFactory()
            contextFactory.method = SSL.SSLv3_METHOD
        else: # TODO support SSL
            contextFactory = None

        factory = ESMTPSenderFactory(self.username, self.password,
                                     message.from_addr,
                                     message.to_addrs,
                                     message.render(),
                                     self.finished,
                                     contextFactory=contextFactory,
                                     requireAuthentication=(self.username and self.password),
                                     requireTransportSecurity=self.security)

        ep = TCP4ClientEndpoint(reactor, self.host, self.port)
        ep.connect(factory)
