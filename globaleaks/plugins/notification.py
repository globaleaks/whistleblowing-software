import string

from cyclone import mail
from twisted.internet.defer import Deferred
from twisted.mail.smtp import ESMTPSenderFactory
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint

from globaleaks.utils import log
from globaleaks import models
from globaleaks.settings import transact
from globaleaks.plugins.base import Notification


class MailNotification(Notification):

    _title = {
            'comment':  'New comment from GLBNode',
            'tip': 'New tip from GLBNode',
    }
    plugin_name = u'Mail'
    plugin_type = u'notification'
    plugin_description = u"Mail notification, with encryption supports"
    admin_fields = {'server' : 'text', 'port': 'int', 'password' : 'text', 'username':'text', 'ssl' : 'bool' }
    receiver_fields = {'mail_address' : 'text'}

    def __init__(self, notification_settings):
        self.body = notification_settings['email_template']

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


    def _append_email(self):
        """
        TODO use http://docs.python.org/2/library/email
        """
        pass

    def _create_email(self, data_type, data, source, dest, subject):
        """
        TODO use http://docs.python.org/2/library/email
        """

        body = '\nEsteemed users,\n'

        if data_type == u'comment':
            body += "In %s You've received a new comment in one of your tip\n" % data['creation_time']
            body += "The comment has been produced by %s\n" % data['source']
            body += "and, by the way, the content is:\n%s\n" % data['content']

        if data_type == u'tip':
            log.err('porco dio')

        return string.join(("From: GLBackend postino <%s>" % source,
                            "To: Estimeed Receiver <%s>" % dest,
                            "Subject: %s" % subject, body), "\r\n")

    # NYI, would use _append_email and continously checking the time delta
    #      admin fields need the digest time delta specified inside.
    def digest_check(self, settings, stored_data, new_data):
        pass

    def do_notify(self, event):
        print 'diocane'
        # validation
        if not self.validate_admin_opt(af):
            return False

        # email fields
        title = self._title[event.type]
        body = self.body # % event.tip_id
        host = event.af['server']
        port = int(event.af['port'])
        u = event.af['username']
        p = event.af['password']
        tls = event.af.get('ssl')
        to_addrs = [event.rf['mail_address']]
        if tls:
            contextFactory = ClientContextFactory()
            contextFactory.method = SSLv3_METHOD
        else:
            contextFactory = None
        message = mail.Message(from_addr=u,
                               to_addrs=to_addrs,
                               subject=title,
                               message=body,
        )

        # send email
        log.debug('about to send an email..')
        result = Deferred()
        def drugs(result):
            success, smtpcode = result
            log.debug('mail sent to ')
            if success != 1:
                pass
                # retry later?
            # could check the smtp code

        result.addBoth(drugs)
        factory = ESMTPSenderFactory(u, p,
                                     message.from_addr,
                                     message.to_addrs,
                                     message.render(),
                                     result,
                                     contextFactory=contextFactory,
                                     requireAuthentication=(u and p),
                                     requireTransportSecurity=tls)

        ep = TCP4ClientEndpoint(reactor, host, port)
        ep.connect(factory)
        return result
