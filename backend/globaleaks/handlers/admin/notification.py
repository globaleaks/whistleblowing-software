# -*- coding: utf-8 -*-
from globaleaks.db import db_refresh_memory_variables
from globaleaks.db.appdata import load_appdata
from globaleaks.handlers.base import BaseHandler
from globaleaks.models.config import ConfigFactory, ConfigL10NFactory
from globaleaks.models.config_desc import ConfigL10NFilters
from globaleaks.orm import transact, tw
from globaleaks.rest import requests
from globaleaks.state import State
from globaleaks.utils.sets import merge_dicts


def db_get_notification(session, tid, language):
    """
    Transaction to get the notification settings for the specified tenant

    :param session: An ORM session
    :param tid: A tenant ID
    :param language: The language to be used in the serialization
    :return: the serialization of notification settings for the specified tenant
    """
    config_dict = ConfigFactory(session, tid).serialize('admin_notification')

    conf_l10n_dict = ConfigL10NFactory(session, tid).serialize('notification', language)

    additional_dict = {
        'reset_templates': False,
        'exception_email_pgp_key_remove': False,
        'smtp_password': '',
        'templates': ConfigL10NFilters['notification']
    }

    return merge_dicts(config_dict, conf_l10n_dict, additional_dict)


@transact
def update_notification(session, tid, request, language):
    config = ConfigFactory(session, tid)
    if request['smtp_password'] == '':
        del request['smtp_password']

    config.update('notification', request)

    config_l10n = ConfigL10NFactory(session, tid)
    config_l10n.update('notification', request, language)

    if request.pop('reset_templates'):
        config_l10n.reset('notification', load_appdata())

    db_refresh_memory_variables(session, [tid])

    return db_get_notification(session, tid, language)


class NotificationInstance(BaseHandler):
    """
    Manage Notification settings (account details and template)
    """
    check_roles = 'admin'

    def get(self):
        return tw(db_get_notification, self.request.tid, self.request.language)

    def put(self):
        """
        Changes the node notification settings.
        """
        request = self.validate_message(self.request.content.read(),
                                        requests.AdminNotificationDesc)

        return update_notification(self.request.tid, request, self.request.language)
