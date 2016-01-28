# -*- coding: UTF-8
#
#   cleaning_sched
#   **************
#
# Implementation of the cleaning operations (delete incomplete submission,
# delete expired tips, etc)
import time

from datetime import timedelta
from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.context import admin_serialize_context
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.admin.receiver import admin_serialize_receiver
from globaleaks.handlers.rtip import db_delete_itips, serialize_rtip
from globaleaks.jobs.base import GLJob
from globaleaks.security import overwrite_and_remove
from globaleaks.settings import GLSettings
from globaleaks.utils.templating import Templating
from globaleaks.utils.utility import log, datetime_now


__all__ = ['CleaningSchedule']

class CleaningSchedule(GLJob):
    name = "Cleaning"

    @transact
    def clean_expired_submissions(self, store):
        """
        This function, checks all the InternalTips and their expiration date.
        if expired InternalTips are found, it removes that along with
        all the related DB entries comment and tip related.
        """
        db_delete_itips(store, store.find(models.InternalTip, models.InternalTip.expiration_date < datetime_now()))

    @transact
    def check_for_expiring_submissions(self, store):
        threshold = datetime_now() - timedelta(GLSettings.memory_copy.tip_expiration_threshold)
        for itip in store.find(models.InternalTip, models.InternalTip.expiration_date < threshold):
            for rtip in itip.receivertips:
                user = rtip.receiver.user
                language = user.language
                node_desc = db_admin_serialize_node(store, language)
                notification_desc = db_get_notification(store, language)
                context_desc = admin_serialize_context(store, rtip.internaltip.context, language)
                receiver_desc = admin_serialize_receiver(rtip.receiver, language)
                tip_desc = serialize_rtip(store, rtip, user.language)

                data = {
                   'type': u'tip_expiration',
                   'node': node_desc,
                   'context': context_desc,
                   'receiver': receiver_desc,
                   'notification': notification_desc,
                   'tip': tip_desc
                }

                subject, body = Templating().get_mail_subject_and_body(data)

                mail = models.Mail({
                   'address': data['receiver']['mail_address'],
                   'subject': subject,
                   'body': body
                })

                store.add(mail)

    @transact
    def clean_db(self, store):
        # delete stats older than 3 months
        store.find(models.Stats, models.Stats.start < datetime_now() - timedelta(3*(365/12))).remove()

        # delete anomalies older than 1 months
        store.find(models.Anomalies, models.Anomalies.date < datetime_now() - timedelta(365/12)).remove()

    @transact_ro
    def get_files_to_secure_delete(self, store):
        return [file_to_delete.filepath for file_to_delete in store.find(models.SecureFileDelete)]

    @transact
    def commit_file_deletion(self, store, filepath):
        store.find(models.SecureFileDelete, models.SecureFileDelete.filepath == filepath).remove()

    @inlineCallbacks
    def perform_secure_deletion_of_files(self):
        files_to_delete = yield self.get_files_to_secure_delete()

        for file_to_delete in files_to_delete:
            self.start_time = time.time()
            log.debug("Starting secure delete of file %s" % file_to_delete)
            overwrite_and_remove(file_to_delete)
            yield self.commit_file_deletion(file_to_delete)
            current_run_time = time.time() - self.start_time
            log.debug("Ending secure delete of file %s (execution time: %.2f)" % (file_to_delete, current_run_time))

    @inlineCallbacks
    def operation(self):
        yield self.clean_expired_submissions()

        yield self.check_for_expiring_submissions()

        yield self.clean_db()

        yield self.perform_secure_deletion_of_files()
