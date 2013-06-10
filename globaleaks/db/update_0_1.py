# -*- encoding: utf-8 -*-

from storm.locals import Bool, Pickle, Unicode, Int, DateTime, Storm

from globaleaks.db.updater import TableReplacer
from globaleaks.models import Model, Receiver

class Receiver_version_0(Model):
    """
    Copyed from:
    https://github.com/globaleaks/GLBackend/blob/f9d5aa21b8472cc48f3fb3691c67f0d9b871db86/globaleaks/models.py
    """

    def __new__(cls, *args, **kw):
        cls.__storm_tables__ = 'receiver'

        return Storm.__new__(cls, args, kw)

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
        print "Receivers migration assistant, extension with GPG capabilities: #%d" %\
              self.store_old.find(Receiver_version_0).count()

        old_receivers = self.store_old.find(Receiver_version_0)

        for orcvr in old_receivers:

            new_obj = Receiver()

            new_obj.username = orcvr.username
            new_obj.id = orcvr.id
            new_obj.name = orcvr.name
            new_obj.password = orcvr.password
            new_obj.description = orcvr.description

            new_obj.can_delete_submission = orcvr.can_delete_submission
            new_obj.comment_notification = orcvr.comment_notification
            new_obj.tip_notification = orcvr.tip_notification
            new_obj.file_notification = orcvr.file_notification

            new_obj.creation_date = orcvr.creation_date
            new_obj.last_access = orcvr.last_access
            new_obj.last_update = orcvr.last_update

            new_obj.failed_login = orcvr.failed_login
            new_obj.receiver_level = orcvr.receiver_level
            new_obj.notification_fields = orcvr.notification_fields
            new_obj.tags = orcvr.tags

            # new fields
            new_obj.gpg_key_armor = None
            new_obj.gpg_key_fingerprint = None
            new_obj.gpg_key_info = None
            new_obj.gpg_key_status = Receiver._gpg_types[0] # Disable

            self.store_new.add(new_obj)
