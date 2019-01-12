# -*- coding: utf-8 -*-
from twisted.internet.defer import inlineCallbacks

from globaleaks.db import db_refresh_memory_variables
from globaleaks.db.appdata import load_appdata
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.user import get_user
from globaleaks.models.config import ConfigFactory, ConfigL10NFactory
from globaleaks.orm import transact, tw
from globaleaks.rest import requests
from globaleaks.state import State
from globaleaks.utils.sets import merge_dicts
from globaleaks.utils.templating import Templating


def admin_serialize_notification(session, tid, language):
    config_dict = ConfigFactory(session, tid).serialize('admin_notification')

    conf_l10n_dict = ConfigL10NFactory(session, tid).serialize('notification', language)

    cmd_flags = {
        'reset_templates': False,
        'exception_email_pgp_key_remove': False,
        'smtp_password': '',
    }

    return merge_dicts(config_dict, cmd_flags, conf_l10n_dict)


def db_get_notification(session, tid, language):
    return admin_serialize_notification(session, tid, language)


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

    return admin_serialize_notification(session, tid, language)


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


class NotificationTestInstance(BaseHandler):
    """
    Send test email notifications to the admin that clicked the button.
    This post takes no arguments and generates an empty response to both
    successful and unsucessful requests. This handler does not return
    until both the db query and the SMTP round trip return.
    """
    check_roles = 'admin'

    @inlineCallbacks
    def post(self):
        tid = self.request.tid
        user = yield get_user(tid,
                              self.current_user.user_id,
                              State.tenant_cache[tid].default_language)

        language = user['language']

        data = {
            'type': 'admin_test',
            'node': (yield tw(db_admin_serialize_node, tid, language)),
            'notification': (yield tw(db_get_notification, tid, language)),
            'user': user,
        }

        subject, body = Templating().get_mail_subject_and_body(data)

        yield self.state.sendmail(tid, user['mail_address'], subject, body)
