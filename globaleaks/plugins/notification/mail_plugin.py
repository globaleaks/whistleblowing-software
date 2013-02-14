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

    def __init__(self):
        self.plugin_name = u'Mail'
        self.plugin_type = u'notification'
        self.plugin_description = u"Mail notification, with encryption supports"

        # this is not the right fields description, because would contain also
        # the 'order' of representation, the 'description' and the 'required' boolean flag
        self.admin_fields = {'server' : 'text', 'port': 'int', 'password' : 'text', 'username':'text', 'ssl' : 'bool' }
        self.receiver_fields = {'mail_address' : 'text'}

    def validate_admin_opt(self, pushed_af):
        fields = ['server', 'port', 'username', 'password']
        if all(pushed_af[field] for field in fields):
            return True
        else:
            log.info('invalid mail settings for admin')
            return False

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        log.debug("[%s] receiver_fields %s (with admin %s)" % ( self.__class__.__name__, receiver_fields, admin_fields))
        return True

    @transact
    def initialize(self, store, admin_fields):
        node = store.find(models.Node).one()
        self.body = node.notification_settings['email_template']
        return True

    def _append_email(self):
        """
        TODO use http://docs.python.org/2/library/email
        """
        pass

    def _create_title(self, data_type, data):
        if data_type == u'comment':
            return "New comment from GLBNode"
        if data_type == u'tip':
            return "New tip from GLBNode"

        raise Exception("Unsupported notification_struct usage")

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

    def do_notify(self, event, af, rf):
        # validation
        self.validate_admin_opt(af)

        # email fields
        title = self._create_title(data_type, data)
        body = self.body % (data['notification_date'], data['tip_gus'])
        host = af['server']
        port = af['port']
        u = af['username']
        p = af['password']
        tls = af['ssl']
        to_addrs = [rf['email_address']]
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
            return d.callback(None)

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
        return d
