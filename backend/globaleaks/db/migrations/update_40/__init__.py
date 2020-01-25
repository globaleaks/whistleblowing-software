# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase


class MigrationScript(MigrationBase):
    def migrate_User(self):
        usernames = {}
        for old_obj in self.session_old.query(self.model_from['User']):
            new_obj = self.model_to['User']()
            for key in new_obj.__table__.columns._data.keys():
                setattr(new_obj, key, getattr(old_obj, key))

            if new_obj.tid not in usernames:
                usernames[new_obj.tid] = {}

            if new_obj.username in usernames[new_obj.tid]:
                new_obj.username = old_obj.id

            usernames[new_obj.tid][new_obj.username] = True

            self.session_new.add(new_obj)
