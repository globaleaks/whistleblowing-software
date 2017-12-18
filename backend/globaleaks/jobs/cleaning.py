# -*- coding: utf-8
# Implementation of the cleaning operations.
from datetime import timedelta

from storm.expr import In, Min

from globaleaks import models
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.rtip import db_delete_itip
from globaleaks.handlers.user import user_serialize_user
from globaleaks.jobs.base import LoopingJob
from globaleaks.orm import transact_sync
from globaleaks.security import overwrite_and_remove
from globaleaks.state import State
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import datetime_now


__all__ = ['Cleaning']


def db_clean_expired_wbtips(store):
    threshold = datetime_now() - timedelta(days=State.tenant_cache[1].wbtip_timetolive)

    wbtips = store.find(models.WhistleblowerTip, models.InternalTip.id == models.WhistleblowerTip.id,
                                                 models.InternalTip.wb_last_access < threshold)

    for wbtip in wbtips:
        store.remove(wbtip)


class Cleaning(LoopingJob):
    interval = 24 * 3600
    monitor_interval = 5 * 60

    def get_start_time(self):
        current_time = datetime_now()
        return (3600 * 24) - (current_time.hour * 3600) - (current_time.minute * 60) - current_time.second

    @transact_sync
    def clean_expired_wbtips(self, store):
        """
        This function checks all the InternalTips and deletes WhistleblowerTips
        that have not been accessed after `threshold`.
        """
        db_clean_expired_wbtips(store)

    @transact_sync
    def clean_expired_itips(self, store):
        """
        This function, checks all the InternalTips and their expiration date.
        if expired InternalTips are found, it removes that along with
        all the related DB entries comment and tip related.
        """
        for itip in store.find(models.InternalTip, models.InternalTip.expiration_date < datetime_now()):
            db_delete_itip(store, itip)

    @transact_sync
    def check_for_expiring_submissions(self, store):
        # TODO: perform cleaning based on configuration for specific submissions
        threshold = datetime_now() + timedelta(hours=State.tenant_cache[1].notification.tip_expiration_threshold)

        for user in store.find(models.User, role=u'receiver'):
            itip_ids = [id for id in store.find(models.InternalTip.id,
                                               models.ReceiverTip.internaltip_id == models.InternalTip.id,
                                               models.InternalTip.expiration_date < threshold,
                                               models.ReceiverTip.receiver_id == models.Receiver.id,
                                               models.Receiver.id == user.id)]

            if not len(itip_ids):
                continue

            earliest_expiration_date = store.find(Min(models.InternalTip.expiration_date),
                                                  In(models.InternalTip.id, itip_ids)).one()

            user_desc = user_serialize_user(store, user, user.language)

            data = {
               'type': u'tip_expiration_summary',
               'node': db_admin_serialize_node(store, 1, user.language),
               'notification': db_get_notification(store, 1, user.language),
               'user': user_desc,
               'expiring_submission_count': len(itip_ids),
               'earliest_expiration_date': earliest_expiration_date
            }

            subject, body = Templating().get_mail_subject_and_body(data)

            store.add(models.Mail({
               'address': user_desc['mail_address'],
               'subject': subject,
               'body': body
            }))

    @transact_sync
    def clean_db(self, store):
        # delete stats older than 3 months
        store.find(models.Stats, models.Stats.start < datetime_now() - timedelta(3*(365/12))).remove()

        # delete anomalies older than 1 months
        store.find(models.Anomalies, models.Anomalies.date < datetime_now() - timedelta(365/12)).remove()

    @transact_sync
    def get_files_to_secure_delete(self, store):
        return [file_to_delete.filepath for file_to_delete in store.find(models.SecureFileDelete)]

    @transact_sync
    def commit_file_deletion(self, store, filepath):
        store.find(models.SecureFileDelete, models.SecureFileDelete.filepath == filepath).remove()

    def perform_secure_deletion_of_files(self):
        files_to_delete = self.get_files_to_secure_delete()

        for file_to_delete in files_to_delete:
            overwrite_and_remove(file_to_delete)
            self.commit_file_deletion(file_to_delete)

    def operation(self):
        self.clean_expired_wbtips()

        self.clean_expired_itips()

        self.check_for_expiring_submissions()

        self.clean_db()

        self.perform_secure_deletion_of_files()
