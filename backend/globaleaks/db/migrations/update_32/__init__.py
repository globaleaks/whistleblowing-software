# -*- encoding: utf-8 -*-

from storm.locals import Int, Bool, Unicode, DateTime, JSON, ReferenceSet

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model


class User_v_31(Model):
    __storm_table__ = 'user'
    creation_date = DateTime()
    username = Unicode()
    password = Unicode()
    salt = Unicode()
    deletable = Bool()
    name = Unicode()
    description = JSON()
    role = Unicode()
    state = Unicode()
    last_login = DateTime()
    mail_address = Unicode()
    language = Unicode()
    timezone = Int()
    password_change_needed = Bool()
    password_change_date = DateTime()
    pgp_key_info = Unicode()  # dropped in v_32
    pgp_key_fingerprint = Unicode()
    pgp_key_public = Unicode()
    pgp_key_expiration = DateTime()
    pgp_key_status = Unicode()  # dropped in v_32
    img_id = Unicode()


class Notification_v_31(Model):
    __storm_table__ = 'notification'
    server = Unicode()
    port = Int()
    username = Unicode()
    password = Unicode()
    source_name = Unicode()
    source_email = Unicode()
    security = Unicode()
    admin_pgp_alert_mail_title = JSON()
    admin_pgp_alert_mail_template = JSON()
    admin_anomaly_mail_template = JSON()
    admin_anomaly_mail_title = JSON()
    admin_anomaly_disk_low = JSON()
    admin_anomaly_disk_medium = JSON()
    admin_anomaly_disk_high = JSON()
    admin_anomaly_activities = JSON()
    admin_test_static_mail_template = JSON()
    admin_test_static_mail_title = JSON()
    tip_mail_template = JSON()
    tip_mail_title = JSON()
    file_mail_template = JSON()
    file_mail_title = JSON()
    comment_mail_template = JSON()
    comment_mail_title = JSON()
    message_mail_template = JSON()
    message_mail_title = JSON()
    tip_expiration_mail_template = JSON()
    tip_expiration_mail_title = JSON()
    pgp_alert_mail_title = JSON()
    pgp_alert_mail_template = JSON()
    receiver_notification_limit_reached_mail_template = JSON()
    receiver_notification_limit_reached_mail_title = JSON()
    export_template = JSON()  # dropped in v_32
    export_message_recipient = JSON()  # dropped in v_32
    export_message_whistleblower = JSON()  # dropped in v_32
    identity_access_authorized_mail_template = JSON()
    identity_access_authorized_mail_title = JSON()
    identity_access_denied_mail_template = JSON()
    identity_access_denied_mail_title = JSON()
    identity_access_request_mail_template = JSON()
    identity_access_request_mail_title = JSON()
    identity_provided_mail_template = JSON()
    identity_provided_mail_title = JSON()
    disable_admin_notification_emails = Bool()
    disable_custodian_notification_emails = Bool()
    disable_receiver_notification_emails = Bool()
    send_email_for_every_event = Bool()
    tip_expiration_threshold = Int()
    notification_threshold_per_hour = Int()
    notification_suspension_time=Int()
    exception_email_address = Unicode()
    exception_email_pgp_key_info = Unicode() # dropped in v_32
    exception_email_pgp_key_fingerprint = Unicode()
    exception_email_pgp_key_public = Unicode()
    exception_email_pgp_key_expiration = DateTime()
    exception_email_pgp_key_status = Unicode()


class InternalTip_v_31(Model):
    __storm_table__ = 'internaltip'
    creation_date = DateTime()
    update_date = DateTime()
    encrypted = Bool()
    context_id = Unicode()
    questionnaire_hash = Unicode()
    preview = JSON()
    progressive = Int()
    tor2web = Bool()
    total_score = Int()
    expiration_date = DateTime()
    identity_provided = Bool()
    identity_provided_date = DateTime()
    enable_two_way_comments = Bool()
    enable_two_way_messages = Bool()
    enable_attachments = Bool()
    enable_whistleblower_identity = Bool()
    new = Int()


class MigrationScript(MigrationBase):
    def migrate_User(self):
        old_objs = self.store_old.find(self.model_from['User'])
        for old_obj in old_objs:
            new_obj = self.model_to['User']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'ccrypto_key_public' or v.name == 'ccrypto_key_private':
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)

    def migrate_InternalTip(self):
        old_objs = self.store_old.find(self.model_from['InternalTip'])
        for old_obj in old_objs:
            new_obj = self.model_to['InternalTip']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'encrypted':
                    new_obj.encrypted = False
                    continue

                if v.name == 'encrypted_answers':
                    old_obj.encrypted_answers = ''
                    continue

                if v.name == 'ccrypto_key_public' or v.name == 'ccrypto_key_private':
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)
