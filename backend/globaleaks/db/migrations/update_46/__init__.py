# -*- coding: UTF-8
from globaleaks.db.migrations.update import MigrationBase


class MigrationScript(MigrationBase):
    def migrate_FieldOption(self):
        old_objs = self.session_old.query(self.model_from['FieldOption'])
        for old_obj in old_objs:
            new_obj = self.model_to['FieldOption']()
            for key in [c.key for c in new_obj.__table__.columns]:
                setattr(new_obj, key, getattr(old_obj, key))

            if new_obj.score_points != 0:
                new_obj.score_type = 1

            self.session_new.add(new_obj)

    def epilogue(self):
        tenants = self.session_new.query(self.model_from['Tenant'])
        for t in tenants:
            m = self.model_from['Config']
            a = self.session_new.query(m.value).filter(m.tid == t.id, m.var_name == u'ip_filter_authenticated_enable').one_or_none()
            b = self.session_new.query(m.value).filter(m.tid == t.id, m.var_name == u'ip_filter_authenticated').one_or_none()

            if a is None or b is None:
                continue

            for c in ['admin', 'custodian', 'receiver']:
                self.session_new.add(self.model_to['Config'](t.id, u'ip_filter_' + c + '_enable', a[0]))
                self.session_new.add(self.model_to['Config'](t.id, u'ip_filter_' + c, b[0]))
                self.entries_count['Config'] += 2
