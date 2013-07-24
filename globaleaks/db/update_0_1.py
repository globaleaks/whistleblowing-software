# -*- encoding: utf-8 -*-

from storm.locals import Bool, Pickle, Unicode, Int, DateTime

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model, Receiver

class Receiver_version_0(Model):
    """
    Fields source from:
    https://github.com/globaleaks/GLBackend/blob/f9d5aa21b8472cc48f3fb3691c67f0d9b871db86/globaleaks/models.py
    """
    __storm_table__ = 'receiver'

    name = Unicode()
    description = Unicode()
    username = Unicode()
    password = Unicode()
    notification_fields = Pickle()
    can_delete_submission = Bool()
    receiver_level = Int()
    failed_login = Int()
    last_update = DateTime()
    last_access = DateTime()
    tags = Pickle()
    tip_notification = Bool()
    comment_notification = Bool()
    file_notification = Bool()


class Replacer01(TableReplacer):

    def migrate_Receiver(self):
        from globaleaks.db.update_1_2 import Receiver_version_1

        print "%s Receivers migration assistant, extension with GPG capabilities: #%d" % (
              self.std_fancy, self.store_old.find(Receiver_version_0).count() )

        old_receivers = self.store_old.find(Receiver_version_0)

        for orcvr in old_receivers:

            new_obj = Receiver_version_1()

            new_obj.username = unicode(orcvr.username)
            new_obj.id = orcvr.id
            new_obj.name = unicode(orcvr.name)
            new_obj.password = unicode(orcvr.password)
            new_obj.description = unicode(orcvr.description)

            new_obj.can_delete_submission = orcvr.can_delete_submission
            new_obj.comment_notification = orcvr.comment_notification
            new_obj.tip_notification = orcvr.tip_notification
            new_obj.file_notification = orcvr.file_notification

            new_obj.creation_date = orcvr.creation_date
            new_obj.last_access = orcvr.last_access
            new_obj.last_update = orcvr.last_update

            new_obj.failed_login = orcvr.failed_login
            new_obj.receiver_level = orcvr.receiver_level
            new_obj.notification_fields = dict(orcvr.notification_fields)
            new_obj.tags = orcvr.tags

            # new fields
            new_obj.gpg_key_armor = None
            new_obj.gpg_key_fingerprint = None
            new_obj.gpg_key_info = None
            new_obj.gpg_key_status = Receiver._gpg_types[0] # Disable
            new_obj.gpg_enable_notification = False
            new_obj.gpg_enable_files = False

            self.store_new.add(new_obj)

        self.store_new.commit()
