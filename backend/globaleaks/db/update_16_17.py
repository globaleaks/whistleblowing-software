# -*- encoding: utf-8 -*-

"""
  Changes


"""

from storm.locals import Int, Bool, Unicode, DateTime, JSON, ReferenceSet
from globaleaks.db.base_updater import TableReplacer
from globaleaks.db.datainit import load_appdata
from globaleaks.models import Model, Field, Step
from globaleaks.utils.utility import datetime_null, every_language
from globaleaks.security import GLBGPG

class Notification_version_16(Model):
    __storm_table__ = 'notification'
    server = Unicode()
    port = Int()
    username = Unicode()
    password = Unicode()
    source_name = Unicode()
    source_email = Unicode()
    security = Unicode()
    admin_anomaly_template = JSON()
    encrypted_tip_template = JSON()
    encrypted_tip_mail_title = JSON()
    plaintext_tip_template = JSON()
    plaintext_tip_mail_title = JSON()
    encrypted_file_template = JSON()
    encrypted_file_mail_title = JSON()
    plaintext_file_template = JSON()
    plaintext_file_mail_title = JSON()
    encrypted_comment_template = JSON()
    encrypted_comment_mail_title = JSON()
    plaintext_comment_template = JSON()
    plaintext_comment_mail_title = JSON()
    encrypted_message_template = JSON()
    encrypted_message_mail_title = JSON()
    plaintext_message_template = JSON()
    plaintext_message_mail_title = JSON()
    pgp_expiration_alert = JSON()
    pgp_expiration_notice = JSON()
    zip_description = JSON()
    ping_mail_template = JSON()
    ping_mail_title = JSON()
    disable_admin_notification_emails = Bool()
    disable_receivers_notification_emails = Bool()

class Receiver_version_16(Model):
    __storm_table__ = 'receiver'
    user_id = Unicode()
    name = Unicode()
    description = JSON()
    configuration = Unicode()
    gpg_key_info = Unicode()
    gpg_key_fingerprint = Unicode()
    gpg_key_status = Unicode()
    gpg_key_armor = Unicode()
    gpg_enable_notification = Bool()
    mail_address = Unicode()
    ping_mail_address = Unicode()
    can_delete_submission = Bool()
    postpone_superpower = Bool()
    last_update = DateTime()
    tip_notification = Bool()
    comment_notification = Bool()
    file_notification = Bool()
    message_notification = Bool()
    ping_notification = Bool()
    presentation_order = Int()

class Replacer1617(TableReplacer):

    def migrate_Notification(self):
        print "%s Notification migration assistant: (pgp_expiration_alert teplates)" % self.std_fancy


        appdata_dict = load_appdata()

        old_notification = self.store_old.find(self.get_right_model("Notification", 16)).one()
        new_notification = self.get_right_model("Notification", 17)()

        for _, v in new_notification._storm_columns.iteritems():

            if v.name == 'admin_pgp_alert_mail_template':
                # check needed to preserve funtionality if templates will be altered in the future
                if v.name in appdata_dict['templates']:
                    new_notification.admin_pgp_alert_mail_template = appdata_dict['templates'][v.name]
                else:
                    new_notification.admin_pgp_alert_mail_template = every_language("")
                continue

            if v.name == 'admin_pgp_alert_mail_title':
                # check needed to preserve funtionality if templates will be altered in the future
                if v.name in appdata_dict['templates']:
                    new_notification.admin_pgp_alert_mail_title = appdata_dict['templates'][v.name]
                else:
                    new_notification.admin_pgp_alert_mail_title = every_language("")
                continue

            if v.name == 'pgp_alert_mail_template':
                # check needed to preserve funtionality if templates will be altered in the future
                if v.name in appdata_dict['templates']:
                    new_notification.pgp_alert_mail_template = appdata_dict['templates'][v.name]
                else:
                    new_notification.pgp_alert_mail_template = every_language("")
                continue

            if v.name == 'pgp_alert_mail_title':
                # check needed to preserve funtionality if templates will be altered in the future
                if v.name in appdata_dict['templates']:
                    new_notification.pgp_alert_mail_title = appdata_dict['templates'][v.name]
                else:
                    new_notification.pgp_alert_mail_title = every_language("")
                continue

            setattr(new_notification, v.name, getattr(old_notification, v.name) )

        self.store_new.add(new_notification)
        self.store_new.commit()

    def migrate_Receiver(self):
        print "%s Receiver migration assistant" % self.std_fancy

        gpgobj = GLBGPG()

        old_receivers = self.store_old.find(self.get_right_model("Receiver", 16))

        for old_receiver in old_receivers:

            new_receiver = self.get_right_model("Receiver", 17)()

            for _, v in new_receiver._storm_columns.iteritems():

                if v.name == 'gpg_key_expiration':
                    if old_receiver.gpg_key_armor:
                        new_receiver.gpg_key_expiration = gpgobj.load_key(old_receiver.gpg_key_armor)['expiration']
                    else:
                        new_receiver.gpg_key_expiration = datetime_null()
                    continue

                setattr(new_receiver, v.name, getattr(old_receiver, v.name))

            self.store_new.add(new_receiver)

        self.store_new.commit()
