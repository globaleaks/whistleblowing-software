# -*- encoding: utf-8 -*-

"""
  Changes

    Receiver table:
      - introduced ping_mail_address 

    Notification table:
      - introduced two boolean TODO - write what they are 
      - introduced ping templates
"""

from storm.locals import JSON, Int, Bool, Unicode, DateTime

from globaleaks import LANGUAGES_SUPPORTED_CODES
from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model


class Receiver_version_15(Model):
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
    can_delete_submission = Bool()
    postpone_superpower = Bool()
    last_update = DateTime()
    tip_notification = Bool()
    comment_notification = Bool()
    file_notification = Bool()
    message_notification = Bool()
    presentation_order = Int()



class Replacer1516(TableReplacer):

    def migrate_Receiver(self):
        print ("%s Receiver migration assistant: added ping_(mail_address|notification)" %
                self.std_fancy)

        old_receivers = self.store_old.find(self.get_right_model("Receiver", 15))

        for ore in old_receivers:

            new_receiver = self.get_right_model("Receiver", 16)()

            for _, v in new_receiver._storm_columns.iteritems():

                if v.name == 'ping_mail_address':
                    new_receiver.ping_mail_address = ore.mail_address
                    continue

                if v.name == 'ping_notification':
                    new_receiver.ping_notification = False

                setattr(new_receiver, v.name, getattr(ore, v.name))

            self.store_new.add(new_receiver)

        self.store_new.commit()

