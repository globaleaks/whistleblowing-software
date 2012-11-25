from globaleaks.utils import log
import smtplib
import string

from globaleaks.plugins import GLPlugin
from globaleaks.utils import gltime

class MailNotification(GLPlugin):

    def __init__(self):
        self.plugin_name = 'email'
        self.plugin_description = "Mail notification, with encryption options"

        # this is not the right fields description, because would contain also
        # the 'order' of representation, the 'description' and the 'required' boolean flag
        self.admin_fields = {'server' : 'text', 'port': 'int', 'password' : 'text', 'username':'text', 'ssl' : 'bool' }
        self.receiver_fields = {'mail_address' : 'text'}

    def validate_admin_opt(self, pushed_af):

        if self._get_SMTP(pushed_af['server'], pushed_af['port'], pushed_af['ssl'],
                pushed_af['username'], pushed_af['password']):
            return True
        else
            return False

    def validate_receiver_opt(self, admin_fields, receiver_fields):
        log.debug("[%s] receiver_fields %s (with admin %s)" % ( self.__class__.__name__, receiver_fields, admin_fields))
        return True

    def _append_email():
        # TODO use http://docs.python.org/2/library/email
        # before was used:

        body = string.join(("From: GLBackend postino <%s>" % username,
                            "To: Estimeed Receiver <%s>" % receiver_addr,
                            "Subject: %s" % subject, text), "\r\n")
        return body

    def _get_SMTP(server, port, tls, username, password):

        try:
            socket = smtplib.SMTP(server + ':' + port)
            if tls:
                socket.starttls()
            socket.login(username, password)

        except smtplib.SMTPConnectError:
            # XXX log.plugin need to be defined and used from GLPlugin inherit
            log.debug("Error, Connection error to %s:%d" % (server, port) )
            return None
        except smtplib.SMTPAuthenticationError:
            log.debug("Error, Invalid Login/Password provided for server %s (%s)" % (server
                    username) )
            return None

        return socket

    # NYI, would use _append_email and continuosly checking the time delta
    #      admin fields need the digest time delta specified inside.
    def digest_check(self, settings, stored_data, new_data):
        pass

    def do_notify(self, settings, stored_data):

        af = settings['admin_field']
        rf = settings['receiver_field']

        body = self._create_email(stored_data)

        smtpsock = self._get_SMTP(af['server'], af['port'], af['ssl'],
                af['username'], af['password'])

        try:
            smtpsock.sendmail(af['username'], [ rf['mail_addr'] ], body)
            smtpsock.quit()

            log.debug("Success in email %s " % tip_gus)
            retval = True

        except smtplib.SMTPRecipientsRefused, smtplib.SMTPSenderRefused:

            # remind, other error can be handled http://docs.python.org/2/library/smtplib.html
            log.err("[E] error in sending the email to %s %s (%s)" % (receiver_addr, infotext, subject))
            retval = False

        return retval
