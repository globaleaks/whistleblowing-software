# -*- encoding: utf-8 -*-

"""
  Changes
    - internaltip: markers simplified to a simple boolean
    - notification: various templates added

"""

from storm.locals import Int, Bool, Unicode, DateTime, JSON, ReferenceSet
from globaleaks.db.base_updater import TableReplacer
from globaleaks.db.datainit import load_appdata
from globaleaks.models import Model
from globaleaks.utils.utility import every_language

class InternalTip_v_19(Model):
    __storm_table__ = 'internaltip'
    context_id = Unicode()
    wb_steps = JSON()
    expiration_date = DateTime()
    last_activity = DateTime()
    access_limit = Int()
    download_limit = Int()
    mark = Unicode()


class Notification_v_19(Model):
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
    admin_pgp_alert_mail_title = JSON()
    admin_pgp_alert_mail_template = JSON()
    pgp_alert_mail_title = JSON()
    pgp_alert_mail_template = JSON()
    zip_description = JSON()
    ping_mail_template = JSON()
    ping_mail_title = JSON()
    disable_admin_notification_emails = Bool()
    disable_receivers_notification_emails = Bool()


class Replacer1920(TableReplacer):

    def migrate_InternalTip(self):
        print "%s InternalTip migration assistant: mark->new" % self.std_fancy

        old_itips = self.store_old.find(self.get_right_model("InternalTip", 19))

        for old_itip in old_itips:

            new_itip = self.get_right_model("InternalTip", 20)()

            for _, v in new_itip._storm_columns.iteritems():

                if v.name == 'new':
                    new_itip.new = False
                    continue

                setattr(new_itip, v.name, getattr(old_itip, v.name))

            self.store_new.add(new_itip)

        self.store_new.commit()


    def migrate_Notification(self):
        print "%s Notification migration assistant: various templates addeed" % self.std_fancy

        appdata_dict = load_appdata()

        old_notification = self.store_old.find(self.get_right_model("Notification", 19)).one()
        new_notification = self.get_right_model("Notification", 20)()

        for _, v in new_notification._storm_columns.iteritems():

            if v.name == 'admin_anomaly_mail_title':
                # check needed to preserve funtionality if templates will be altered in the future
                if v.name in appdata_dict['templates']:
                    new_notification.admin_anomaly_mail_title = appdata_dict['templates'][v.name]
                else:
                    new_notification.admin_anomaly_mail_title = every_language("")
                continue

            if v.name == 'notification_digest_mail_title':
                # check needed to preserve funtionality if templates will be altered in the future
                if v.name in appdata_dict['templates']:
                    new_notification.notification_digest_mail_title = appdata_dict['templates'][v.name]
                else:
                    new_notification.notification_digest_mail_title = every_language("")
                continue

            if v.name == 'upcoming_tip_expiration_mail_title':
                # check needed to preserve funtionality if templates will be altered in the future
                if v.name in appdata_dict['templates']:
                    new_notification.upcoming_tip_expiration_mail_title = appdata_dict['templates'][v.name]
                else:
                    new_notification.upcoming_tip_expiration_mail_title = every_language("")
                continue

            if v.name == 'upcoming_tip_expiration_template':
                # check needed to preserve funtionality if templates will be altered in the future
                if v.name in appdata_dict['templates']:
                    new_notification.upcoming_tip_expiration_template = appdata_dict['templates'][v.name]
                else:
                    new_notification.upcoming_tip_expiration_template = every_language("")
                continue

            setattr(new_notification, v.name, getattr(old_notification, v.name) )

        self.store_new.add(new_notification)
        self.store_new.commit()
