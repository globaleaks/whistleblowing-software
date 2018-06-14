# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase

class MigrationScript(MigrationBase):
    def migrate_Config(self):
        old_objs = self.session_old.query(self.model_from['Config'])
        for old_obj in old_objs:
            new_obj = self.model_to['Config'](migrate=True)
            for key in [c.key for c in new_obj.__table__.columns]:
                setattr(new_obj, key, getattr(old_obj, key))

            if old_obj.var_name == 'disable_security_awareness_badge':
                new_obj.var_name = 'enable_disclaimer'
                new_obj.value = not old_obj.value

            self.session_new.add(new_obj)

    def migrate_ConfigL10N(self):
        old_objs = self.session_old.query(self.model_from['ConfigL10N'])
        for old_obj in old_objs:
            new_obj = self.model_to['ConfigL10N']()
            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'var_name':
                    if old_obj.var_name == 'security_awareness_title':
                        new_obj.var_name = 'disclaimer_title'
                    elif old_obj.var_name == 'security_awareness_text':
                        new_obj.var_name = 'disclaimer_text'
                    else:
                        new_obj.var_name = old_obj.var_name
                else:
                    setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)

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
