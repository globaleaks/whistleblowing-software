# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase

class MigrationScript(MigrationBase):
    def migrate_FieldAttr(self):
        old_objs = self.session_old.query(self.model_from['FieldAttr'])
        for old_obj in old_objs:
            new_obj = self.model_to['FieldAttr']()
            for key in [c.key for c in new_obj.__table__.columns]:
                setattr(new_obj, key, getattr(old_obj, key))

            if old_obj.name == 'text_of_confirmation_question_upon_negative_answer':
                setattr(new_obj, 'name', 'text_shown_upon_negative_answer')

            self.session_new.add(new_obj)
