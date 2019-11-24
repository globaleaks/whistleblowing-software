# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase


class MigrationScript(MigrationBase):
    def migrate_User(self):
        usernames = {}
        old_objs = self.session_old.query(self.model_from['User'])
        for old_obj in old_objs:
            new_obj = self.model_to['User']()
            for key in [c.key for c in new_obj.__table__.columns]:
                setattr(new_obj, key, getattr(old_obj, key))

            if new_obj.tid not in usernames:
                usernames[new_obj.tid] = {}

            if new_obj.username in usernames[new_obj.tid]:
                new_obj.username = old_obj.id

            usernames[new_obj.tid][new_obj.username] = True

            self.session_new.add(new_obj)
