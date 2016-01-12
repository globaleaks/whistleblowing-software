# -*- encoding: utf-8 -*-
import os
import shutil

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.settings import GLSettings

class MigrationScript(MigrationBase):
    def prologue(self):
        old_logo_path = os.path.abspath(os.path.join(GLSettings.static_path, 'globaleaks_logo.png'))
        if os.path.exists(old_logo_path):
            new_logo_path = os.path.abspath(os.path.join(GLSettings.static_path, 'logo.png'))
            shutil.move(old_logo_path, new_logo_path)
