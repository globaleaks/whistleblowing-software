# -*- coding: utf-8
# Implementation of the daily operations.
import os
from datetime import datetime, timedelta

from sqlalchemy import not_
from sqlalchemy.sql.expression import func

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.db import compact_db
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.user import user_serialize_user
from globaleaks.jobs.job import DailyJob
from globaleaks.orm import db_del, db_log, db_query, transact, tw
from globaleaks.utils.fs import srm
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
        itips_ids = []

        results = session.query(models.InternalTip.id, models.InternalTip.tid).filter(models.InternalTip.expiration_date < datetime_now()).all()
        for result in results:
            itips_ids.append(result[0])

        db_del(session, models.InternalTip, models.InternalTip.id.in_(itips_ids))

        for result in results:
            db_log(session, tid=result[1], type='delete_report', user_id='system', object_id=result[0])

    def db_check_for_expiring_submissions(self, session, tid):
        threshold = datetime_now() + timedelta(hours=self.state.tenants[tid].cache.notification.tip_expiration_threshold)

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

        # delete emails older than two weeks
        db_del(session, models.Mail, models.Mail.creation_date < datetime_now() - timedelta(14))

        # delete archived questionnaire schemas not used by any existing submission
        subquery = session.query(models.InternalTipAnswers.questionnaire_hash).subquery()
        db_del(session, models.ArchivedSchema, not_(models.ArchivedSchema.hash.in_(subquery)))

        # delete the tenants created via signup that has not been completed in 24h
        subquery = session.query(models.Subscriber.tid).filter(models.Subscriber.activation_token != '',
                                                               models.Subscriber.tid == models.Tenant.id,
                                                               models.Subscriber.registration_date < datetime_now() - timedelta(days=1)) \
                                                  .subquery()
        db_del(session, models.Tenant, models.Tenant.id.in_(subquery))

    @transact
    def get_files_list(self, session):
        return [x[0] for x in db_query(session, models.File.id)]

    @transact
    def get_attachments_list(self, session):
        return [x[0] for x in db_query(session, models.InternalFile.filename)] + \
               [x[0] for x in db_query(session, models.ReceiverFile.filename)] + \
               [x[0] for x in db_query(session, models.WhistleblowerFile.filename)]

    def perform_secure_deletion_of_files(self, valid_files):
        # Delete the customization files not associated to the database
        for f in os.listdir(self.state.settings.files_path):
            if f in valid_files:
                continue

            path = os.path.join(self.state.settings.files_path, f)
            timestamp = datetime.fromtimestamp(os.path.getmtime(path))
            if is_expired(timestamp, days=1):
                srm(path)

    def perform_secure_deletion_of_attachments(self, valid_files):
        # Delete the attachment files not associated to the database
        for f in os.listdir(self.state.settings.attachments_path):
            if f in valid_files:
                continue

            path = os.path.join(self.state.settings.attachments_path, f)
            timestamp = datetime.fromtimestamp(os.path.getmtime(path))
            if is_expired(timestamp, days=1):
                srm(path)

    def perform_secure_deletion_of_temporary_files(self):
        # Delete the outdated temp files if older than 1 day
        for f in os.listdir(self.state.settings.tmp_path):
            path = os.path.join(self.state.settings.tmp_path, f)
            timestamp = datetime.fromtimestamp(os.path.getmtime(path))
            if is_expired(timestamp, days=1):
                srm(path)

        # Delete the outdated ramdisk tokens older than 1 week
        for f in os.listdir(self.state.settings.ramdisk_path):
            path = os.path.join(self.state.settings.ramdisk_path, f)
            timestamp = datetime.fromtimestamp(os.path.getmtime(path))
            if is_expired(timestamp, days=7):
                srm(path)

    @inlineCallbacks
    def operation(self):
        yield self.clean()

        for tid in self.state.tenants:
            yield tw(self.db_check_for_expiring_submissions, tid)

        valid_files = yield self.get_files_list()
        self.perform_secure_deletion_of_files(valid_files)

        valid_files = yield self.get_attachments_list()
        self.perform_secure_deletion_of_attachments(valid_files)

        self.perform_secure_deletion_of_temporary_files()

        compact_db()
