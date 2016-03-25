from twisted.internet.defer import inlineCallbacks

from globaleaks.db import db_refresh_memory_variables
from globaleaks.db.appdata import load_appdata
from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import Notification
from globaleaks.rest import requests
from globaleaks.security import GLBPGP
from globaleaks.utils.utility import log, datetime_to_ISO8601
from globaleaks.utils.structures import fill_localized_keys, get_localized_values
from globaleaks.utils.mailutils import sendmail
from globaleaks.settings import GLSettings

def parse_pgp_options(notification, request):
    """
    This is called in a @transact, when an users update their preferences or
    when admins configure keys on their behalf.

    @param user: the user ORM object
    @param request: the dictionary containing the pgp infos to be parsed
    @return: None
    """
    new_pgp_key = request.get('exception_email_pgp_key_public', None)
    remove_key = request.get('exception_email_pgp_key_remove', False)

    # the default
    notification.exception_email_pgp_key_status = u'disabled'

    if remove_key:
        # In all the cases below, the key is marked disabled as request
        notification.exception_email_pgp_key_status = u'disabled'
        notification.exception_email_pgp_key_info = None
        notification.exception_email_pgp_key_public = None
        notification.exception_email_pgp_key_fingerprint = None
        notification.exception_email_pgp_key_expiration = None

    elif new_pgp_key:
        gnob = GLBPGP()

        try:
            result = gnob.load_key(new_pgp_key)

            log.debug("PGP Key imported: %s" % result['fingerprint'])

            notification.exception_email_pgp_key_status = u'enabled'
            notification.exception_email_pgp_key_info = result['info']
            notification.exception_email_pgp_key_public = new_pgp_key
            notification.exception_email_pgp_key_fingerprint = result['fingerprint']
            notification.exception_email_pgp_key_expiration = result['expiration']

        except:
            raise

        finally:
            # the finally statement is always called also if
            # except contains a return or a raise
            gnob.destroy_environment()


def admin_serialize_notification(notif, language):
    ret_dict = {
        'server': notif.server if notif.server else u"",
        'port': notif.port if notif.port else u"",
        'username': notif.username if notif.username else u"",
        # Explicitly do not include password in returned dict. Addresses #1615
        'password': u"",
        'security': notif.security if notif.security else u"",
        'source_name': notif.source_name,
        'source_email': notif.source_email,
        'disable_admin_notification_emails': notif.disable_admin_notification_emails,
        'disable_custodian_notification_emails': notif.disable_custodian_notification_emails,
        'disable_receiver_notification_emails': notif.disable_receiver_notification_emails,
        'send_email_for_every_event': notif.send_email_for_every_event,
        'reset_templates': False,
        'tip_expiration_threshold': notif.tip_expiration_threshold,
        'notification_threshold_per_hour': notif.notification_threshold_per_hour,
        'notification_suspension_time': notif.notification_suspension_time,
        'exception_email_address': notif.exception_email_address,
        'exception_email_pgp_key_info': notif.exception_email_pgp_key_info,
        'exception_email_pgp_key_fingerprint': notif.exception_email_pgp_key_fingerprint,
        'exception_email_pgp_key_public': notif.exception_email_pgp_key_public,
        'exception_email_pgp_key_expiration': datetime_to_ISO8601(notif.exception_email_pgp_key_expiration),
        'exception_email_pgp_key_status': notif.exception_email_pgp_key_status,
        'exception_email_pgp_key_remove': False
    }

    return get_localized_values(ret_dict, notif, notif.localized_keys, language)


def db_get_notification(store, language):
    notif = store.find(Notification).one()
    return admin_serialize_notification(notif, language)


@transact_ro
def get_notification(store, language):
    return db_get_notification(store, language)


@transact
def update_notification(store, request, language):
    notif = store.find(Notification).one()

    fill_localized_keys(request, Notification.localized_keys, language)

    if request['reset_templates']:
        appdata_dict = load_appdata()
        for k in appdata_dict['templates']:
            request[k] = appdata_dict['templates'][k]

    if request['password'] == u'':
      log.debug("No password set. Using pw already in the DB.")
      request['password'] = notif.password

    notif.update(request)

    parse_pgp_options(notif, request)
    # Since the Notification object has been changed refresh the global copy.
    db_refresh_memory_variables(store)

    return admin_serialize_notification(notif, language)


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
        self.set_status(200)
        self.finish(notification_desc)

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
        self.finish(response)

class EmailNotifInstance(BaseHandler):
    """
    Manage Test Email Notifications that the admin would like to handle.
    """

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
      """
      Errors: InvalidAuthentication, ForbiddenOperation, TODOstmpError
      """
      request = self.validate_message(self.request.body, requests.AdminTestMailNotifDesc)
      send_to = ''
      if request['send_to'] == 'err-notif':
        # TODO Get admin email from db.
        send_to = GLSettings.memory_copy.notif_username
      elif request['send_to'] == 'err-notif':
        send_to = GLSettings.memory_copy.notif_username
      elif request['send_to'] == 'reciever':
        # TODO Validate reciever email addr.
        send_to = request['']
      else:
        raise errors.ForbiddenOperation

      print("Attempting to send test email to:", send_to)
      try: 
        result = yield sendmail(send_to, 'Test Email Config', '. . .')  
        print(result)
        self.set_status(200)
      except Exception as e:
        print(e)
        self.set_status(400) # 402 Unprocessable entity threw a strange error.
      self.finish()
