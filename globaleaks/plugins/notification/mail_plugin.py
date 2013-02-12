import string

from cyclone import mail
from twisted.internet.defer import Deferred
from twisted.mail.smtp import ESMTPSenderFactory
from twisted.internet import reactor
from twisted.internet.endpoints import TCP4ClientEndpoint

from globaleaks.utils import log
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
        # send a mock email
        return True

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        log.debug("[%s] receiver_fields %s (with admin %s)" % ( self.__class__.__name__, receiver_fields, admin_fields))
        return True

    def initialize(self, admin_fields):
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

        Exception("Unsupported notification_struct usage")

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
            body += "In %s as been created a new Tip for you\n" % data['notification_date']
            body += "You can access using the unique link http://dev.globaleaks.org:8082/#/status/%s\n" % data['tip_gus']
            body += "\n"\
            "This is an E-Mail message to notify you that someone has selected you as a valuable recipient of "\
            "WhistleBlowing material in the form of a Globaleaks tip-off. This message has been created "\
            "by the GlobaLeaks Node [http://dev.globaleaks.org].\nThis tip-off has been sent to you by "\
            "an anonymous whistleblower. She/He would like it for you to"\
            "pay special attention to the information and material contained therein. Please consider"\
            "that whistleblowers often expose themselves to high personal risks in order to protect the public good. Therefore "\
            "the material that they provide with this tip-off should be considered of high importance.\n\n"\
            "Please do not forward or share this e-mail: each tip-off has a limited number of downloads and access before being "\
            "destroyed forever, nobody (even the node administrator) can recover and expired or dead tip-off.\n\n\n"

            body += "\n"\
            "--------------------------------------------------\n"\
            "GENERAL INFO\n"\
            "--------------------------------------------------\n"\
            "1. What is Globaleaks?\n"\
            "GlobaLeaks is the first Open Source Whistleblowing Framework. It empowers anyone to easily setup and "\
            "maintain their own Whistleblowing platform. It is also a collection of what are the best practices for "\
            "people receiveiving and submitting material. GlobaLeaks works in all environments: media, activism, corporations, public agencies.\n\n"\
            "2. Is GlobaLeaks sending me this Mail?\n"\
            "No, this mail has been sent to you by the Node called [http://dev.globaleaks.org]. They are running the GlobaLeaks Platform, but\n"\
            "are not directly tied to the GlobaLeaks organization. GlobaLeaks (http://www.globaleaks.org) will never be directly "\
            "affiliated with any real world WhistleBlowing sites, GlobaLeaks will only provide software and technical support.\n"\
            "3. Why am I receiving this?\n"\
            "You're receiving this communication because an anonymous whistleblower has chosen you as a trustworthy contact"\
            "for releasing confidential and/or important information that could be of utmost importance.\n\n"\
            "For any other inquire please refer to %(sitename)s to the GlobaLeaks website at http://globaleaks.org\n\n"

        body += "\n\nBest regards,\nThe email notification plugin"

        return string.join(("From: GLBackend postino <%s>" % source,
                            "To: Estimeed Receiver <%s>" % dest,
                            "Subject: %s" % subject, body), "\r\n")

    # NYI, would use _append_email and continously checking the time delta
    #      admin fields need the digest time delta specified inside.
    def digest_check(self, settings, stored_data, new_data):
        pass

    def do_notify(self, settings, data_type, data):
        af = settings['admin_settings']
        rf = settings['receiver_settings']

        title = self._create_title(data_type, data)
        body = self._create_email(data_type, data, af['username'], rf['mail_address'], title)

        host = af['server']
        port = af['port']
        u = af['username']
        p = af['password']
        tls = af['ssl']
        if tls:
            contextFactory = ClientContextFactory()
            contextFactory.method = SSLv3_METHOD
        else:
            contextFactory = None
        message = mail.Message(from_addr=af['username'],
                               to_addrs=[rf['mail_address']],
                               subject=title,
                               message=body,
        )
        result = Deferred()
        def drugs(result):
            success, smtpcode = result
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
