# -*- coding: utf-8 -*-
from globaleaks import DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED
from globaleaks.db.appdata import load_appdata
from globaleaks.utils.log import log


class MigrationBase(object):
    """
    This is the base class used by every Updater
    """
    skip_model_migration = {}
    skip_count_check = {}
    renamed_attrs = {}

    def __init__(self, migration_mapping, start_version, session_old, session_new):
        self.appdata = load_appdata()

        self.migration_mapping = migration_mapping
        self.start_version = start_version

        self.session_old = session_old
        self.session_new = session_new

        self.model_from = {}
        self.model_to = {}
        self.entries_count = {}

        expected = DATABASE_VERSION + 1 - FIRST_DATABASE_VERSION_SUPPORTED
        for model_name, model_history in migration_mapping.items():
            length = len(model_history)
            if length != expected:
                raise TypeError('Number of status mismatch for table {}, expected:{} actual:{}'.format(model_name, expected, length))

            self.model_from[model_name] = migration_mapping[model_name][start_version - FIRST_DATABASE_VERSION_SUPPORTED]
            self.model_to[model_name] = migration_mapping[model_name][start_version + 1 - FIRST_DATABASE_VERSION_SUPPORTED]

            if self.model_from[model_name] is None or self.model_to[model_name] is None:
                self.entries_count[model_name] = 0
            else:
                self.entries_count[model_name] = self.session_old.query(self.model_from[model_name]).count()

        self.session_new.commit()

    def commit(self):
        self.session_new.commit()

    def close(self):
        self.session_old.close()
        self.session_new.close()

    def prologue(self):
        pass

    def epilogue(self):
        pass

    def generic_migration_function(self, model_name):
        for old_obj in self.session_old.query(self.model_from[model_name]):
            new_obj = self.model_to[model_name]()

            for key in [c.key for c in self.model_to[model_name].__table__.columns]:
                old_key = key

                if model_name in self.renamed_attrs and key in self.renamed_attrs[model_name]:
                    old_key = self.renamed_attrs[model_name][key]

                if hasattr(old_obj, old_key):
                    setattr(new_obj, key, getattr(old_obj, old_key))

            self.session_new.add(new_obj)

    def migrate_model(self, model_name):
        if self.entries_count[model_name] <= 0 or self.skip_model_migration.get(model_name, False):
            return

        log.info(' * %s [#%d]' % (model_name, self.entries_count[model_name]))

        specific_migration_function = getattr(self, 'migrate_%s' % model_name, None)
        if specific_migration_function is None:
            self.generic_migration_function(model_name)
        else:
            specific_migration_function()
