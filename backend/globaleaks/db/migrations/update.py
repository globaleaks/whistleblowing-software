# -*- coding: utf-8 -*-
from sqlalchemy.ext.declarative import declarative_base

from globaleaks import DATABASE_VERSION, FIRST_DATABASE_VERSION_SUPPORTED
from globaleaks.db.appdata import load_appdata
from globaleaks.settings import Settings
from globaleaks.utils.utility import every_language_dict


class MigrationBase(object):
    """
    This is the base class used by every Updater
    """
    def __init__(self, migration_mapping, start_version, store_old, store_new):
        self.appdata = load_appdata()

        self.migration_mapping = migration_mapping
        self.start_version = start_version

        self.store_old = store_old
        self.store_new = store_new

        self.model_from = {}
        self.model_to = {}
        self.entries_count = {}
        self.fail_on_count_mismatch = {}

        expected = DATABASE_VERSION + 1 - FIRST_DATABASE_VERSION_SUPPORTED
        for model_name, model_history in migration_mapping.items():
            length = len(model_history)
            if length != expected:
                raise TypeError('Number of status mismatch for table {}, expected:{} actual:{}'.format(model_name, expected, length))

            self.fail_on_count_mismatch[model_name] = True

            self.model_from[model_name] = migration_mapping[model_name][start_version - FIRST_DATABASE_VERSION_SUPPORTED]
            self.model_to[model_name] = migration_mapping[model_name][start_version + 1 - FIRST_DATABASE_VERSION_SUPPORTED]

            self.entries_count[model_name] = 0
            if self.model_from[model_name] is not None and self.model_to[model_name] is not None:
                self.entries_count[model_name] = self.store_old.query(self.model_from[model_name]).count()

        self.store_new.commit()

    def commit(self):
        self.store_new.commit()

    def close(self):
        self.store_old.close()
        self.store_new.close()

    def prologue(self):
        pass

    def epilogue(self):
        pass

    def migrate_model_key(self, old_obj, new_obj, key, old_key = None):
        """
        Migrate an existing model key allowing key name change
        """
        if old_key is None:
            old_key = key

        old_keys = [c.key for c in old_obj.__table__.columns]
        if old_key in old_keys:
            setattr(new_obj, key, getattr(old_obj, old_key))

    def update_model_with_new_templates(self, model_obj, var_name, template_list, templates_dict):
        if var_name in template_list:
            # check needed to preserve funtionality if templates will be altered in the future
            if var_name in templates_dict:
                template_text = templates_dict[var_name]
            else:
                template_text = every_language_dict()

            setattr(model_obj, var_name, template_text)
            return True

        return False

    def generic_migration_function(self, model_name):
        old_objects = self.store_old.query(self.model_from[model_name])

        for old_obj in old_objects:
            new_obj = self.model_to[model_name](migrate=True)

            for k in [c.key for c in new_obj.__table__.columns]:
                self.migrate_model_key(old_obj, new_obj, k)

            self.store_new.add(new_obj)

    def migrate_model(self, model_name):
        objs_count = self.store_old.query(self.model_from[model_name]).count()

        specific_migration_function = getattr(self, 'migrate_%s' % model_name, None)
        if specific_migration_function is not None:
            Settings.print_msg(' ł %s [#%d]' % (model_name, objs_count))
            specific_migration_function()
        else:
            Settings.print_msg(' * %s [#%d]' % (model_name, objs_count))
            self.generic_migration_function(model_name)
