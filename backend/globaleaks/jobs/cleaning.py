# -*- coding: utf-8
# Implementation of the cleaning operations.
import datetime
import fnmatch
import os
from datetime import timedelta

from sqlalchemy import and_, not_
from sqlalchemy.sql.expression import func

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.rtip import db_delete_itips
from globaleaks.handlers.user import user_serialize_user
from globaleaks.jobs.base import LoopingJob
from globaleaks.orm import transact
from globaleaks.state import State
from globaleaks.utils.security import overwrite_and_remove
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import datetime_now, datetime_to_ISO8601, is_expired


__all__ = ['Cleaning']


class Cleaning(LoopingJob):
    interval = 24 * 3600
    monitor_interval = 5 * 60

    def get_start_time(self):
        current_time = datetime_now()
        return (3600 * 24) - (current_time.hour * 3600) - (current_time.minute * 60) - current_time.second

    @transact
    def clean_expired_wbtips(self, session):
        """
        This function checks all the InternalTips and deletes the receipt if the delete threshold is exceeded
        """
        for tid in self.state.tenant_state:
            threshold = datetime_now() - timedelta(days=State.tenant_cache[tid].wbtip_timetolive)

            session.query(models.InternalTip) \
                   .filter(models.InternalTip.tid == tid,
                           models.InternalTip.wb_last_access < threshold).update({'receipt_hash': u''})

    @transact
    def clean_expired_itips(self, session):
        """
        This function, checks all the InternalTips and their expiration date.
        if expired InternalTips are found, it removes that along with
        all the related DB entries comment and tip related.
        """
        itips_ids = [id[0] for id in session.query(models.InternalTip.id).filter(models.InternalTip.expiration_date < datetime_now())]
        if itips_ids:
            db_delete_itips(session, itips_ids)

    @transact
    def check_for_expiring_submissions(self, session):
        for tid in self.state.tenant_state:
            threshold = datetime_now() + timedelta(hours=State.tenant_cache[tid].notification.tip_expiration_threshold)

            for user in session.query(models.User).filter(models.User.tid == tid, models.User.role == u'receiver'):
                itip_ids = [id[0] for id in session.query(models.InternalTip.id) \
                                                 .filter(models.InternalTip.tid == tid,
                                                         models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                                         models.InternalTip.expiration_date < threshold,
                                                         models.ReceiverTip.receiver_id == models.Receiver.id,
                                                         models.Receiver.id == user.id)]

                if not len(itip_ids):
                    continue

                earliest_expiration_date = session.query(func.min(models.InternalTip.expiration_date)) \
                                                .filter(models.InternalTip.id.in_(itip_ids)).one()[0]

                user_desc = user_serialize_user(session, user, user.language)

                data = {
                   'type': u'tip_expiration_summary',
                   'node': db_admin_serialize_node(session, tid, user.language),
                   'notification': db_get_notification(session, tid, user.language),
                   'user': user_desc,
                   'expiring_submission_count': len(itip_ids),
                   'earliest_expiration_date': datetime_to_ISO8601(earliest_expiration_date)
                }

                subject, body = Templating().get_mail_subject_and_body(data)

                session.add(models.Mail({
                    'tid': tid,
                    'address': user_desc['mail_address'],
                    'subject': subject,
                    'body': body
                 }))

    @transact
    def clean_db(self, session):
        # delete stats older than 3 months
        session.query(models.Stats).filter(models.Stats.start < datetime_now() - timedelta(3*(365/12))).delete(synchronize_session='fetch')

        # delete anomalies older than 1 months
        session.query(models.Anomalies).filter(models.Anomalies.date < datetime_now() - timedelta(365/12)).delete(synchronize_session='fetch')

        # delete archived schemas not used by any existing submission
        hashes = [x[0] for x in session.query(models.InternalTip.questionnaire_hash)]
        if hashes:
            session.query(models.ArchivedSchema).filter(not_(models.ArchivedSchema.hash.in_(hashes))).delete(synchronize_session='fetch')

    @transact
    def get_files_to_secure_delete(self, session):
        return [x[0] for x in session.query(models.SecureFileDelete.filepath)]

    @transact
    def commit_files_deletion(self, session, filepaths):
        session.query(models.SecureFileDelete).filter(models.SecureFileDelete.filepath.in_(filepaths)).delete(synchronize_session='fetch')

    @inlineCallbacks
    def perform_secure_deletion_of_files(self):
        # Delete files that are marked for secure deletion
        files_to_delete = yield self.get_files_to_secure_delete()
        for file_to_delete in files_to_delete:
            overwrite_and_remove(file_to_delete)

        if files_to_delete:
            yield self.commit_files_deletion(files_to_delete)

        # Delete the outdated AES files older than 1 day
        files_to_remove = [f for f in os.listdir(self.state.settings.attachments_path) if fnmatch.fnmatch(f, '*.aes')]
        for f in files_to_remove:
            path = os.path.join(self.state.settings.attachments_path, f)
            timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(path))
            if is_expired(timestamp, days=1):
                os.remove(path)

        # Delete the backups older than 15 days
        for f in os.listdir(self.state.settings.backups_path):
            path = os.path.join(self.state.settings.backups_path, f)
            timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(path))
            if is_expired(timestamp, days=15):
                os.remove(path)

    @inlineCallbacks
    def operation(self):
        yield self.clean_expired_wbtips()

        yield self.clean_expired_itips()

        yield self.check_for_expiring_submissions()

        yield self.clean_db()

        yield self.perform_secure_deletion_of_files()
