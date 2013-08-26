# -*- encoding: utf-8 -*-

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model, User, ReceiverTip
from storm.locals import Unicode, Int, DateTime

class User_version_4(Model):
    __storm_table__ = 'user'

    username = Unicode()
    password = Unicode()
    salt = Unicode()
    role = Unicode()
    state = Unicode()
    last_login = DateTime()
    first_failed = DateTime()
    failed_login_count = Int()

class Replacer56(TableReplacer):

    def migrate_User(self):
        print "%s User upgrade (bruteforce detection supported): #%d" % (
              self.debug_info, self.store_old.find(self.get_right_model("User", 6)).count() )

        old_users = self.store_old.find(self.get_right_model("User", 5))

        for old_user in old_users:

            new_obj = User()

            # last_failed_attempt is throw away!
            new_obj.id = old_user.id
            new_obj.username = old_user.username
            new_obj.password = old_user.password
            new_obj.salt = old_user.salt
            new_obj.role = old_user.role
            new_obj.state = old_user.state
            new_obj.last_login = old_user.last_login
            new_obj.failed_login_count = old_user.failed_login_count
            new_obj.creation_date = old_user.creation_date

            self.store_new.add(new_obj)
        self.store_new.commit()

    def migrate_ReceiverFile(self):
        """
        This version do not need a new model/SQL, because just had
        enforced and sets the receiver_tip_id, that before was not assigned
        """

        print "%s ReceiverFile migration assistant, (receiver tip reference): #%d" % (
            self.std_fancy, self.store_old.find(self.get_right_model("ReceiverFile", 6)).count() )

        old_rf = self.store_old.find(self.get_right_model("ReceiverFile", 6))

        for orf in old_rf:

            new_obj = self.get_right_model("ReceiverFile", 6)()

            new_obj.id = orf.id
            new_obj.internaltip_id = orf.internaltip_id
            new_obj.internalfile_id = orf.internalfile_id
            new_obj.receiver_id = orf.receiver_id

            # Receiver Tip reference
            rtrf = self.store_old.find(ReceiverTip, ReceiverTip.internaltip_id == orf.internaltip_id,
                              ReceiverTip.receiver_id == orf.receiver_id).one()
            new_obj.receiver_tip_id = rtrf.id
            # XXX perhaps switch with get_right_model for the future versions

            new_obj.status = orf.status
            new_obj.size = orf.size
            new_obj.file_path = orf.file_path
            new_obj.creation_date = orf.creation_date
            new_obj.mark = orf.mark
            new_obj.downloads = orf.downloads

            self.store_new.add(new_obj)
        self.store_new.commit()

