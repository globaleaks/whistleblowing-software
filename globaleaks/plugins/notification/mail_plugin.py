
from globaleaks.utils import log
from globaleaks.plugins.base import Notification
import smtplib
import string

class MailNotification(Notification):

    def __init__(self):
        self.plugin_name = 'email'
        self.plugin_type = 'notification'
        self.plugin_description = "Mail notification, with encryption options"

        # this is not the right fields description, because would contain also
        # the 'order' of representation, the 'description' and the 'required' boolean flag
        self.admin_fields = {'server' : 'text', 'port': 'int', 'password' : 'text', 'username':'text', 'ssl' : 'bool' }
        self.receiver_fields = {'mail_address' : 'text'}

    def validate_admin_opt(self, pushed_af):

        if self._get_SMTP(pushed_af['server'], pushed_af['port'], pushed_af['ssl'],
                pushed_af['username'], pushed_af['password']):
            return True
        else:
            return False

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

    def _create_title(self, notification_struct):

        if notification_struct['type'] == u'comment':
            return "New comment from GLBNode"
        if notification_struct['type'] == u'tip':
            return "New tip from GLBNode"

        Exception("Unsupported notification_struct usage")

    def _create_email(self, notification_struct, source, dest, subject):
        """
        TODO use http://docs.python.org/2/library/email
        """



        body = '\nEsteemed users,\n'

        if notification_struct['type'] == u'comment':
            body += "In %s You've received a new comment in one of your tip\n" % notification_struct['creation_time']
            body += "The comment has been produced by %s\n" % notification_struct['source']
        if notification_struct['type'] == u'tip':
            body += "In %s as been created a new Tip for you\n" % notification_struct['creation_time']
            body += "You can access using the unique link http://dev.globaleaks.org:8082/#/status/%s\n" % notification_struct['tip_gus']
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

    def _get_SMTP(self, server, port, tls, username, password):

        try:
            socket = smtplib.SMTP("%s:%d" % (server, port))
            if tls:
                socket.starttls()
            socket.login(username, password)

        except smtplib.SMTPConnectError:
            # XXX log.plugin need to be defined and used from GLPlugin inherit
            log.debug("Error, Connection error to %s:%d" % (server, port) )
            return None
        except smtplib.SMTPAuthenticationError:
            log.debug("Error, Invalid Login/Password provided for server %s (%s %s)" % (server, username, password) )
            return None

        return socket

    # NYI, would use _append_email and continously checking the time delta
    #      admin fields need the digest time delta specified inside.

    def digest_check(self, settings, stored_data, new_data):
        pass

    def do_notify(self, settings, notification_struct):

        af = settings['admin_fields']
        rf = settings['receiver_fields']

        title = self._create_title(notification_struct)
        body = self._create_email(notification_struct,  af['username'], rf['mail_addr'], title)

        try:
            smtpsock = self._get_SMTP(af['server'], af['port'], af['ssl'],
                af['username'], af['password'])

            if not smtpsock:
                log.err("[E] error in sending the email to %s (username: %s)" % (rf['mail_addr'], af['username']))
                return False

            smtpsock.sendmail(af['username'], [ rf['mail_addr'] ], body)
            smtpsock.quit()

            log.debug("Success in email %s " % rf['mail_addr'])
            return True

        except smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused:

            # remind, other error can be handled http://docs.python.org/2/library/smtplib.html
            log.err("[E] error in sending the email to %s (username: %s)" % (rf['mail_addr'], af['username']))
            return False


