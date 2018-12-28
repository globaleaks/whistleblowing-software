# -*- coding: utf-8
# Implementation of the daily operations.
import os
import time
from datetime import datetime

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.file import db_mark_file_for_secure_deletion
from globaleaks.jobs.job import DailyJob
from globaleaks.orm import transact
from globaleaks.settings import Settings
from globaleaks.utils.backup import backup_name, backup_type, get_records_to_delete
from globaleaks.utils.tar import tardir
from globaleaks.utils.utility import datetime_now, datetime_to_ISO8601, is_expired


__all__ = ['Backup']


def db_perform_backup(session, version):
    timestamp = int(time.time())
    backupfile = backup_name(version, timestamp)
    dst = os.path.join(Settings.backup_path, backupfile)

    tardir(dst, Settings.working_path)

    backup = session.query(models.Backup).filter(models.Backup.filename == backupfile).one_or_none()
    if backup is None:
        backup = models.Backup()

    backup.filename = backupfile
    backup.creation_date = datetime.utcfromtimestamp(timestamp)
    backup.local = True
    session.add(backup)


class Backup(DailyJob):
    monitor_interval = 5 * 60

    @transact
    def daily_backup(self, session):
        if not self.state.tenant_cache[1].backup:
            return

        dst = os.path.join(self.state.settings.backup_path, backupfile)
        src = self.state.settings.working_path
        db_perform_backup(self.state.tenant_cache[1].version, dst, src)

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

    @inlineCallbacks
    def operation(self):
        yield self.daily_backup()

        to_delete = yield self.check_backup_records_to_delete()

        yield self.commit_deletion_of_backup_records(to_delete)
