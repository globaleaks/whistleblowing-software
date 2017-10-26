# -*- coding: utf-8 -*-
# Implements periodic checks in order to verify pgp key status and other consistencies:

from datetime import timedelta

from globaleaks import models
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.user import db_get_admin_users
from globaleaks.handlers.user import user_serialize_user
from globaleaks.jobs.base import LoopingJob
from globaleaks.orm import transact_sync
from globaleaks.state import State
from globaleaks.transactions import db_schedule_email
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import datetime_now, datetime_null


__all__ = ['PGPCheckSchedule']

XTIDX = 1

def db_get_expired_or_expiring_pgp_users(store):
    threshold = datetime_now() + timedelta(days=15)

    return store.find(models.User, models.User.pgp_key_public != u'',
                                   models.User.pgp_key_expiration != datetime_null(),
                                   models.User.pgp_key_expiration < threshold)


class PGPCheckSchedule(LoopingJob):
    name = "PGP Check"
    interval = 24 * 3600
    monitor_interval = 5 * 60

    def get_start_time(self):
        current_time = datetime_now()
        return (3600 * 24) - (current_time.hour * 3600) - (current_time.minute * 60) - current_time.second

    def prepare_admin_pgp_alerts(self, store, expired_or_expiring):
        for user_desc in db_get_admin_users(store):
            user_language = user_desc['language']

            data = {
                'type': u'admin_pgp_alert',
                'node': db_admin_serialize_node(store, XTIDX, user_language),
                'notification': db_get_notification(store, user_language),
                'users': expired_or_expiring,
                'user': user_desc,
            }

            subject, body = Templating().get_mail_subject_and_body(data)

            db_schedule_email(store, user_desc['mail_address'], subject, body)

    def prepare_user_pgp_alerts(self, store, user_desc):
        user_language = user_desc['language']

        data = {
            'type': u'pgp_alert',
            'node': db_admin_serialize_node(store, XTIDX, user_language),
            'notification': db_get_notification(store, user_language),
            'user': user_desc
        }

        subject, body = Templating().get_mail_subject_and_body(data)

        db_schedule_email(store, user_desc['mail_address'], subject, body)

    @transact_sync
    def perform_pgp_validation_checks(self, store):
        expired_or_expiring = []

        for user in db_get_expired_or_expiring_pgp_users(store):
            expired_or_expiring.append(user_serialize_user(store, user, State.tenant_cache[1].default_language))

            if user.pgp_key_expiration < datetime_now():
                user.pgp_key_public = ''
                user.pgp_key_fingerprint = ''
                user.pgp_key_expiration = datetime_null()

        if expired_or_expiring:
            if not State.tenant_cache[1].notif.disable_admin_notification_emails:
                self.prepare_admin_pgp_alerts(store, expired_or_expiring)

            for user_desc in expired_or_expiring:
                self.prepare_user_pgp_alerts(store, user_desc)

    def operation(self):
        self.perform_pgp_validation_checks()
