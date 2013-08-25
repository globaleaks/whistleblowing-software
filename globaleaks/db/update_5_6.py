# -*- encoding: utf-8 -*-

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model, User
from globaleaks.utils import datetime_null
from storm.locals import Bool, Pickle, Unicode, Int, DateTime

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
            new_obj.id = old_user.id
            new_obj.username = old_user.username
            new_obj.password = old_user.password
            new_obj.salt = old_user.salt
            new_obj.role = old_user.role
            new_obj.state = old_user.state
            new_obj.last_login = old_user.last_login
            
            # first_failed field has been removed
            # new_obj.first_failed = old_user.first_failed
            
            new_obj.failed_login_count = old_user.failed_login_count
            new_obj.creation_date = old_user.creation_date

            self.store_new.add(new_obj)
        self.store_new.commit()

