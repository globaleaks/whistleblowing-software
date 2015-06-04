from twisted.internet.defer import inlineCallbacks

from globaleaks.db.datainit import db_update_memory_variables, load_appdata
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.models import Notification
from globaleaks.rest import requests
from globaleaks.settings import transact, transact_ro
from globaleaks.utils.structures import fill_localized_keys, get_localized_values


def admin_serialize_notification(notif, language):
    ret_dict = {
        'server': notif.server if notif.server else u"",
        'port': notif.port if notif.port else u"",
        'username': notif.username if notif.username else u"",
        'password': notif.password if notif.password else u"",
        'security': notif.security if notif.security else u"",
        'source_name' : notif.source_name,
        'source_email' : notif.source_email,
        'disable_admin_notification_emails': notif.disable_admin_notification_emails,
        'disable_receivers_notification_emails': notif.disable_receivers_notification_emails,
        'send_email_for_every_event': notif.send_email_for_every_event,
        'reset_templates': False,
        'tip_expiration_threshold': notif.tip_expiration_threshold,
        'notification_threshold_per_hour': notif.notification_threshold_per_hour,
        'notification_suspension_time': notif.notification_suspension_time
    }

    return get_localized_values(ret_dict, notif, notif.localized_strings, language)


@transact_ro
def get_notification(store, language):
    notif = store.find(Notification).one()
    return admin_serialize_notification(notif, language)


@transact
def update_notification(store, request, language):
    notif = store.find(Notification).one()

    fill_localized_keys(request, Notification.localized_strings, language)

    if request['reset_templates']:
        appdata_dict = load_appdata()
        for k in appdata_dict['templates']:
            request[k] = appdata_dict['templates'][k]

    notif.update(request)

    db_update_memory_variables(store)

    return admin_serialize_notification(notif, language)


class NotificationInstance(BaseHandler):
    """
    Manage Notification settings (account details and template)
    """

    @transport_security_check('admin')
    @authenticated('admin')
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

    @transport_security_check('admin')
    @authenticated('admin')
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
