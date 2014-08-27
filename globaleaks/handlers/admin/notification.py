import os
import shutil

from twisted.internet.defer import inlineCallbacks

from globaleaks.settings import transact, transact_ro, GLSetting
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.rest import errors, requests
from globaleaks.models import Receiver, Context, Node, Notification, User, ApplicationData
from globaleaks import security, models
from globaleaks.utils import structures
from globaleaks.utils.utility import log, datetime_now, datetime_null, seconds_convert, datetime_to_ISO8601
from globaleaks.db.datainit import import_memory_variables
from globaleaks.security import gpg_options_parse
from globaleaks import LANGUAGES_SUPPORTED_CODES, LANGUAGES_SUPPORTED
from globaleaks.third_party import rstr


def admin_serialize_notification(notif, language=GLSetting.memory_copy.default_language):
    notification_dict = {
        'server': notif.server if notif.server else u"",
        'port': notif.port if notif.port else u"",
        'username': notif.username if notif.username else u"",
        'password': notif.password if notif.password else u"",
        'security': notif.security if notif.security else u"",
        'source_name' : notif.source_name,
        'source_email' : notif.source_email,
        'disable': GLSetting.notification_temporary_disable,
    }

    mo = structures.Rosetta()
    mo.acquire_storm_object(notif)
    for attr in mo.get_localized_attrs():
        notification_dict[attr] = mo.dump_translated(attr, language)

    return notification_dict

@transact_ro
def get_notification(store, language=GLSetting.memory_copy.default_language):
    try:
        notif = store.find(Notification).one()
    except Exception as excep:
        log.err("Database error when getting Notification table: %s" % str(excep))
        raise excep

    return admin_serialize_notification(notif, language)

@transact
def update_notification(store, request, language=GLSetting.memory_copy.default_language):

    try:
        notif = store.find(Notification).one()
    except Exception as excep:
        log.err("Database error or application error: %s" % excep )
        raise excep

    mo = structures.Rosetta()
    mo.acquire_request(language, request, Notification)
    for attr in mo.get_localized_attrs():
        request[attr] = mo.get_localized_dict(attr)

    if request['security'] in Notification._security_types:
        notif.security = request['security']
    else:
        log.err("Invalid request: Security option not recognized")
        log.debug("Invalid Security value: %s" % request['security'])
        raise errors.InvalidInputFormat("Security selection not recognized")

    try:
        notif.update(request)
    except Exception as dberror:
        log.err("Unable to update Notification: %s" % dberror)
        raise errors.InvalidInputFormat(dberror)

    if request['disable'] != GLSetting.notification_temporary_disable:
        log.msg("Switching notification mode: was %s and now is %s" %
                ("DISABLE" if GLSetting.notification_temporary_disable else "ENABLE",
                 "DISABLE" if request['disable'] else "ENABLE")
        )
        GLSetting.notification_temporary_disable = request['disable']

    return admin_serialize_notification(notif, language)


class NotificationInstance(BaseHandler):
    """
    Manage Notification settings (account details and template)
    """

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, *uriargs):
        """
        Parameters: None
        Response: adminNotificationDesc
        Errors: None (return empty configuration, at worst)
        """
        notification_desc = yield get_notification(self.request.language)
        self.set_status(200)
        self.finish(notification_desc)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, *uriargs):
        """
        Request: adminNotificationDesc
        Response: adminNotificationDesc
        Errors: InvalidInputFormat

        Changes the node notification settings.
        """

        request = self.validate_message(self.request.body,
            requests.adminNotificationDesc)

        response = yield update_notification(request, self.request.language)

        # align the memory variables with the new updated data
        yield import_memory_variables()

        self.set_status(202) # Updated
        self.finish(response)
