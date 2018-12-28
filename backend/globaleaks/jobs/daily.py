# -*- coding: utf-8
# Implementation of the daily operations.
import datetime
import fnmatch
import os
import time
from datetime import datetime, timedelta

from sqlalchemy import not_
from sqlalchemy.sql.expression import func

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.file import db_mark_file_for_secure_deletion
from globaleaks.handlers.rtip import db_delete_itips
from globaleaks.handlers.user import user_serialize_user
from globaleaks.jobs.job import LoopingJob
from globaleaks.orm import transact
from globaleaks.utils.backup import backup_name, backup_type, get_records_to_delete
from globaleaks.utils.fs import overwrite_and_remove
from globaleaks.utils.tar import tardir
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import datetime_now, datetime_to_ISO8601, is_expired


__all__ = ['Daily']


class Daily(LoopingJob):
    interval = 24 * 3600
    monitor_interval = 5 * 60

    def get_start_time(self):
        current_time = datetime_now()
        return (3600 * 24) - (current_time.hour * 3600) - (current_time.minute * 60) - current_time.second

    @transact
    def daily_backup(self, session):
        if not self.state.tenant_cache[1].backup:
            return

        timestamp = int(time.time())
        backupfile = backup_name(self.state.tenant_cache[1].version, timestamp)
        backupdst = os.path.join(self.state.settings.backup_path, backupfile)
        backupsrc = self.state.settings.working_path
        excluded_paths = [
            self.state.settings.backup_path,
            self.state.settings.update_path
        ]

        tardir(backupdst, backupsrc, excluded_paths)

        backup = session.query(models.Backup).filter(models.Backup.filename == backupfile).one_or_none()
        if backup is None:
            backup = models.Backup()

        backup.filename = backupfile
        backup.creation_date = datetime.utcfromtimestamp(timestamp)
        backup.local = True
        session.add(backup)

    @transact
    def check_backup_records_to_delete(self, session):
        to_delete = []
        backups = session.query(models.Backup)
        d = self.state.tenant_cache[1].backup_d
        w = self.state.tenant_cache[1].backup_w
        m = self.state.tenant_cache[1].backup_m
        for record in get_records_to_delete(d, w, m, backups):
            record.delete = True
            db_mark_file_for_secure_deletion(session, self.state.settings.backup_path, record.filename)

            to_delete.append({
                'id': record.id,
                'filename': record.filename
            })

        return to_delete

    @transact
    def commit_deletion_of_backup_records(self, session, records_to_delete):
        records_to_delete_ids = [r['id'] for r in records_to_delete]
        session.query(models.Backup).filter(models.Backup.id.in_(records_to_delete_ids))

    def db_clean_expired_wbtips(self, session):
        """
        This function checks all the InternalTips and deletes the receipt if the delete threshold is exceeded
        """
        for tid in self.state.tenant_state:
            threshold = datetime_now() - timedelta(days=self.state.tenant_cache[tid].wbtip_timetolive)

            wbtips_ids = [r[0] for r in session.query(models.InternalTip.id) \
                                               .filter(models.InternalTip.tid == tid,
                                                       models.InternalTip.wb_last_access < threshold)]

            if wbtips_ids:
                session.query(models.WhistleblowerTip).filter(models.WhistleblowerTip.id.in_(wbtips_ids)).delete(synchronize_session = 'fetch')

    def db_clean_expired_itips(self, session):
        """
        This function, checks all the InternalTips and their expiration date.
        if expired InternalTips are found, it removes that along with
        all the related DB entries comment and tip related.
        """
        itips_ids = [id[0] for id in session.query(models.InternalTip.id).filter(models.InternalTip.expiration_date < datetime_now())]
        if itips_ids:
            db_delete_itips(session, itips_ids)

    def db_check_for_expiring_submissions(self, session):
        for tid in self.state.tenant_state:
            threshold = datetime_now() + timedelta(hours=self.state.tenant_cache[tid].notification.tip_expiration_threshold)

            for user in session.query(models.User).filter(models.User.role == u'receiver',
                                                          models.UserTenant.user_id == models.User.id,
                                                          models.UserTenant.tenant_id == tid):
                itip_ids = [id[0] for id in session.query(models.InternalTip.id) \
                                                 .filter(models.InternalTip.tid == tid,
                                                         models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                                         models.InternalTip.expiration_date < threshold,
                                                         models.ReceiverTip.receiver_id == user.id)]

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

    def db_expire_old_passwords(self, session):
        """
        Expires passwords if past the last change date
        """
        for tid in self.state.tenant_state:
            # if the expiration threshold is 0, ignore it
            if self.state.tenant_cache[tid].password_change_period == 0:
                continue

            threshold = datetime_now() - timedelta(days=self.state.tenant_cache[tid].password_change_period)

            ids = [r[0] for r in session.query(models.User.id) \
                                        .join(models.UserTenant) \
                                        .filter(models.User.password_change_date < threshold,
                                                models.UserTenant.user_id == models.User.id,
                                                models.UserTenant.tenant_id == tid)]

            session.query(models.User).filter(models.User.id.in_(ids)).update({'password_change_needed': True}, synchronize_session='fetch')

    def db_clean(self, session):
        # delete stats older than 1 year
        session.query(models.Stats).filter(models.Stats.start < datetime_now() - timedelta(90)).delete(synchronize_session='fetch')

        # delete anomalies older than 1 year
        session.query(models.Anomalies).filter(models.Anomalies.date < datetime_now() - timedelta(365)).delete(synchronize_session='fetch')

        # delete archived schemas not used by any existing submission
        hashes = [x[0] for x in session.query(models.InternalTipAnswers.questionnaire_hash)]
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
        files_to_remove = [f for f in os.listdir(self.state.settings.tmp_path) if fnmatch.fnmatch(f, '*.aes')]
        for f in files_to_remove:
            path = os.path.join(self.state.settings.tmp_path, f)
            timestamp = datetime.fromtimestamp(os.path.getmtime(path))
            if is_expired(timestamp, days=1):
                overwrite_and_remove(path)

        # Delete the update backups older than 15 days
        for f in os.listdir(self.state.settings.update_path):
            path = os.path.join(self.state.settings.update_path, f)
            timestamp = datetime.datetime.fromtimestamp(os.path.getmtime(path))
            if is_expired(timestamp, days=15):
                overwrite_and_remove(path)

    @transact
    def daily_clean(self, session):
        self.db_clean_expired_wbtips(session)

        self.db_clean_expired_itips(session)

        self.db_check_for_expiring_submissions(session)

        self.db_expire_old_passwords(session)

        self.db_clean(session)

    @inlineCallbacks
    def operation(self):
        yield self.daily_backup()

        to_delete = yield self.check_backup_records_to_delete()

        yield self.commit_deletion_of_backup_records(to_delete)

        yield self.daily_clean()

        yield self.perform_secure_deletion_of_files()
