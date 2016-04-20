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
    pgp_key_info = Unicode() # Dropped in v_32
    pgp_key_fingerprint = Unicode()
    pgp_key_public = Unicode()
    pgp_key_expiration = DateTime()
    pgp_key_status = Unicode() # Dropped in v_32
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
    export_template = JSON()
    export_message_recipient = JSON()
    export_message_whistleblower = JSON()
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


class MigrationScript(MigrationBase):
    pass
