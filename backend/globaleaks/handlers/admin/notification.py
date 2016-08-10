from twisted.internet.defer import inlineCallbacks

from globaleaks.db import db_refresh_memory_variables
from globaleaks.db.appdata import load_appdata
from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.user import get_user_settings
from globaleaks.models import Notification
from globaleaks.models.l10n import Notification_L10N
from globaleaks.models.config import NotificationFactory, PrivateFactory
from globaleaks.models.groups import GLConfig
from globaleaks.rest import requests
from globaleaks.security import GLBPGP
from globaleaks.utils.sets import disjoint_union
from globaleaks.utils.utility import log, datetime_to_ISO8601
from globaleaks.utils.mailutils import sendmail
from globaleaks.settings import GLSettings


def parse_pgp_options(c_notif, request):
    """
    This is called in a @transact, when an users update their preferences or
    when admins configure keys on their behalf.

    @param user: the user ORM object
    @param request: the dictionary containing the pgp infos to be parsed
    @return: None
    """
    new_pgp_key = request.get('exception_email_pgp_key_public', u'')
    remove_key = request.get('exception_email_pgp_key_remove', False)

    if remove_key:
        c_notif.set_val('exception_email_pgp_key_public ', None)
        c_notif.set_val('exception_email_pgp_key_fingerprint ', None)
        c_notif.set_val('exception_email_pgp_key_expiration ', None)
    elif new_pgp_key != u'':
        gnob = GLBPGP()

        try:
            result = gnob.load_key(new_pgp_key)

            log.debug("PGP Key imported: %s" % result['fingerprint'])
            c_notif.set_val('exception_email_pgp_key_public', new_pgp_key)
            c_notif.set_val('exception_email_pgp_key_fingerprint', result['info'])
            c_notif.set_val('exception_email_pgp_key_expiration', result['info'])

        except Exception as e:
            raise e

        finally:
            # the finally statement is always called also if
            # except contains a return or a raise
            gnob.destroy_environment()


def admin_serialize_notification(store, language):
    config_dict = NotificationFactory(store).admin_export()

    cmd_flags = {
        'reset_templates': False,
        'exception_email_pgp_key_remove': False,
    }

    conf_l10n_dict = Notification_L10N(store).build_localized_dict(language)

    return disjoint_union(config_dict, cmd_flags, conf_l10n_dict)


def db_get_notification(store, language):
    return admin_serialize_notification(store, language)


@transact_ro
def get_notification(store, language):
    return db_get_notification(store, language)


@transact
def update_notification(store, request, language):
    notif_l10n = Notification_L10N(store)
    log.debug("Updating lang: %s" % language)
    notif_l10n.update_model(request, language)

    if request['reset_templates']:
        appdata = load_appdata()
        notif_l10n.reset_templates(appdata)

    c_notif = NotificationFactory(store)

    smtp_pw = request.pop('password', u'')
    if smtp_pw != u'':
        PrivateFactory(store).get('smtp_password').set_val(smtp_pw)


    c_notif.update(request)

    parse_pgp_options(c_notif, request)

    # Since the Notification object has been changed refresh the global copy.
    db_refresh_memory_variables(store)

    return admin_serialize_notification(store, language)


class NotificationInstance(BaseHandler):
    """
    Manage Notification settings (account details and template)
    """

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: AdminNotificationDesc
        Errors: None (return empty configuration, at worst)
        """
        notification_desc = yield get_notification(self.request.language)
        self.write(notification_desc)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def put(self):
        """
        Request: AdminNotificationDesc
        Response: AdminNotificationDesc
        Errors: InvalidInputFormat

        Changes the node notification settings.
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminNotificationDesc)

        response = yield update_notification(request, self.request.language)

        self.set_status(202)
        self.write(response)

class EmailNotifInstance(BaseHandler):
    """
    Send Test Email Notifications to the admin that clicked the button.
    This post takes no arguments and generates an empty response to both 
    successful and unsucessful requests. Understand that this handler blocks 
    its thread until both the db query and the SMTP round trip return.
    """

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Parameters: None
        Response: None
        """
        user = yield get_user_settings(self.current_user.user_id, 
                                     GLSettings.memory_copy.default_language)
        notif = yield get_notification(user['language'])

        send_to = user['mail_address']
        # Get the test emails subject line and body internationalized from notif
        subject = notif['admin_test_static_mail_title']
        msg = notif['admin_test_static_mail_template']

        log.debug("Attempting to send test email to: %s" % send_to)
        # If sending the email fails the exception mail address will be mailed.
        # If the failure is due to a bad SMTP config that will fail too, but it 
        # doesn't hurt to try!
        try:
            yield sendmail(send_to, subject, msg)
        except Exception as e:
            log.debug("Sending to admin failed. Trying an exception mail")
            raise e
