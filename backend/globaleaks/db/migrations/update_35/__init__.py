# -*- encoding: utf-8 -*-

from globaleaks.db.migrations.update import MigrationBase

from globaleaks.models.config import NodeFactory
from globaleaks.models.l10n import EnabledLanguage


class MigrationScript(MigrationBase):
    def migrate_User(self):
        default_language = NodeFactory(self.store_old).get_val('default_language')
        enabled_languages = EnabledLanguage.list(self.store_old)

        old_objs = self.store_old.find(self.model_from['User'])
        for old_obj in old_objs:
            new_obj = self.model_to['User']()
            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'language' and getattr(old_obj, v.name) not in enabled_languages:
                    # fix users that have configured a language that has never been there
                    #setattr(new_obj, v.name, default_language)
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)
