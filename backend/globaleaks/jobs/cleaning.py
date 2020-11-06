# -*- coding: utf-8
# Implementation of the daily operations.
import fnmatch
import os
from datetime import datetime, timedelta

from sqlalchemy import not_
from sqlalchemy.sql.expression import func

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.rtip import db_delete_itips
from globaleaks.handlers.user import user_serialize_user
from globaleaks.jobs.job import DailyJob
from globaleaks.orm import db_del, db_query, transact, tw
from globaleaks.utils.fs import overwrite_and_remove
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import datetime_now, is_expired


__all__ = ['Cleaning']


class Cleaning(DailyJob):
    monitor_interval = 5 * 60

    def db_clean_expired_itips(self, session):
        """
        This function, checks all the InternalTips and their expiration date.
        if expired InternalTips are found, it removes that along with
        all the related DB entries comment and tip related.
        """
        itips_ids = [id[0] for id in session.query(models.InternalTip.id).filter(models.InternalTip.expiration_date < datetime_now())]
        if itips_ids:
            db_delete_itips(session, itips_ids)

    def db_clean_expired_wbtips(self, session):
        """
        This function checks all the InternalTips and deletes the receipt if the delete threshold is exceeded
        """
        threshold = datetime_now() - timedelta(days=self.state.tenant_cache[1].wbtip_timetolive)

        subquery = session.query(models.InternalTip.id) \
                          .filter(models.InternalTip.wb_last_access < threshold) \
                          .subquery()

        db_del(session, models.WhistleblowerTip, models.WhistleblowerTip.id.in_(subquery))

    def db_check_for_expiring_submissions(self, session, tid):
        threshold = datetime_now() + timedelta(hours=self.state.tenant_cache[tid].notification.tip_expiration_threshold)

        result = session.query(models.User, func.count(models.InternalTip.id), func.min(models.InternalTip.expiration_date)) \
                        .filter(models.InternalTip.tid == tid,
                                models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                models.InternalTip.expiration_date < threshold,
                                models.User.id == models.ReceiverTip.receiver_id) \
                        .group_by(models.User.id) \
                        .having(func.count(models.InternalTip.id) > 0) \
                        .all()

        for x in result:
            user = x[0]
            expiring_submission_count = x[1]
            earliest_expiration_date = x[2]

            user_desc = user_serialize_user(session, user, user.language)

            data = {
                'type': 'tip_expiration_summary',
                'node': db_admin_serialize_node(session, tid, user.language),
                'notification': db_get_notification(session, tid, user.language),
                'user': user_desc,
                'expiring_submission_count': expiring_submission_count,
                'earliest_expiration_date': earliest_expiration_date
            }

            subject, body = Templating().get_mail_subject_and_body(data)

            session.add(models.Mail({
                'tid': tid,
                'address': user_desc['mail_address'],
                'subject': subject,
                'body': body
            }))

    @transact
    def clean(self, session):
        self.db_clean_expired_itips(session)
        self.db_clean_expired_wbtips(session)

        # delete emails older than two weeks
        db_del(session, models.Mail, models.Mail.creation_date < datetime_now() - timedelta(7))

        # delete stats older than 1 year
        db_del(session, models.Stats, models.Stats.start < datetime_now() - timedelta(365))

        # delete anomalies older than 1 year
        db_del(session, models.Anomalies, models.Anomalies.date < datetime_now() - timedelta(365))

        # delete archived questionnaire schemas not used by any existing submission
        subquery = session.query(models.InternalTipAnswers.questionnaire_hash).subquery()
        db_del(session, models.ArchivedSchema, not_(models.ArchivedSchema.hash.in_(subquery)))

        # delete the tenants created via signup that has not been completed in 24h
        subquery = session.query(models.Tenant.id).filter(models.Subscriber.activation_token != '',
                                                          models.Subscriber.tid == models.Tenant.id,
                                                          models.Tenant.id == models.Config.tid,
                                                          models.Tenant.creation_date < datetime.timestamp(datetime_now() - timedelta(days=1))) \
                                                  .subquery()
        db_del(session, models.Tenant, models.Tenant.id.in_(subquery))

    @transact
    def get_attachments_list(self, session):
        return [x[0] for x in db_query(session, models.InternalFile.filename)] + \
               [x[0] for x in db_query(session, models.ReceiverFile.filename)] + \
               [x[0] for x in db_query(session, models.WhistleblowerFile.filename)]

    def perform_secure_deletion_of_attachments(self, valid_files):
        # Delete the attachment files associated to deleted tips
        for f in os.listdir(self.state.settings.attachments_path):
            if f in valid_files:
                continue

            path = os.path.join(self.state.settings.attachments_path, f)
            timestamp = datetime.fromtimestamp(os.path.getmtime(path))
            if is_expired(timestamp, days=1):
                overwrite_and_remove(path)

    def perform_secure_deletion_of_temporary_files(self):
        # Delete the outdated temp files if older than 1 day
        for f in os.listdir(self.state.settings.tmp_path):
            path = os.path.join(self.state.settings.tmp_path, f)
            timestamp = datetime.fromtimestamp(os.path.getmtime(path))
            if is_expired(timestamp, days=1):
                overwrite_and_remove(path)

    @inlineCallbacks
    def operation(self):
        yield self.clean()

        for tid in self.state.tenant_state:
            yield tw(self.db_check_for_expiring_submissions, tid)

        valid_files = yield self.get_attachments_list()

        self.perform_secure_deletion_of_attachments(valid_files)

        self.perform_secure_deletion_of_temporary_files()
