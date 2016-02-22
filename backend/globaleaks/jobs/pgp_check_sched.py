
#
#   pgp_check_sched
#   ***************
#
# Implements periodic checks in order to verify pgp key status and other consistencies:
# 
# to be implemented:
#     if keys configured by receiver are going
#     to expire in short time, if so, send a warning email to the recipient.
#
from datetime import timedelta

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.orm import transact
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.user import db_get_admin_users
from globaleaks.handlers.user import user_serialize_user
from globaleaks.jobs.base import GLJob
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import datetime_now, datetime_null
from globaleaks.utils.templating import Templating


__all__ = ['PGPCheckSchedule']


class PGPCheckSchedule(GLJob):
    name = "PGP Check"

    def prepare_admin_pgp_alerts(self, store, expired_or_expiring):
        for user_desc in db_get_admin_users(store):
            user_language = user_desc['language']

            data = {
                'address': user_desc['mail_address'],
                'type': u'admin_pgp_alert',
                'node': db_admin_serialize_node(store, user_language),
                'notification': db_get_notification(store, user_language),
                'users': expired_or_expiring
            }

            Templating().db_prepare_mail(store, data)


    def prepare_user_pgp_alerts(self, store, user_desc):
        user_language = user_desc['language']

        data = {
            'address': user_desc['mail_address'],
            'type': u'pgp_alert',
            'node': db_admin_serialize_node(store, user_language),
            'notification': db_get_notification(store, user_language),
            'user': user_desc
        }

        Templating().db_prepare_mail(store, data)

    @transact
    def perform_pgp_validation_checks(self, store):
        expired_or_expiring = []

        for user in store.find(models.User):
            if user.pgp_key_public and user.pgp_key_expiration != datetime_null():
                if user.pgp_key_expiration < datetime_now():
                    expired_or_expiring.append(user_serialize_user(user, GLSettings.memory_copy.default_language))
                    user.pgp_key_status = u'disabled'
                    user.pgp_key_info = None
                    user.pgp_key_public = None
                    user.pgp_key_fingerprint = None
                    user.pgp_key_expiration = None
                elif user.pgp_key_expiration < datetime_now() - timedelta(days=15):
                    expired_or_expiring.append(user_serialize_user(user, GLSettings.memory_copy.default_language))

        if expired_or_expiring:
            if not GLSettings.memory_copy.disable_admin_notification_emails:
                self.prepare_admin_pgp_alerts(store, expired_or_expiring)

            for user_desc in expired_or_expiring:
                self.prepare_user_pgp_alerts(store, user_desc)

    @inlineCallbacks
    def operation(self):
        yield self.perform_pgp_validation_checks()
