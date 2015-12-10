# -*- encoding: utf-8 -*-

import string

from storm.expr import And
from storm.locals import Int, Bool, Unicode, DateTime, JSON, Reference

from globaleaks import models, __version__, DATABASE_VERSION
from globaleaks.db.migrations.update import MigrationBase
from globaleaks.db.appdata import load_default_fields
from globaleaks.models import Model
from globaleaks.security import sha512
from globaleaks.utils.structures import fill_localized_keys
from globaleaks.utils.utility import datetime_null


class User_v_24(Model):
    __storm_table__ = 'user'
    creation_date = DateTime()
    username = Unicode()
    password = Unicode()
    salt = Unicode()
    deletable = Bool()
    name = Unicode()
    description = JSON()
    role = Unicode()
    state = Unicode()
    last_login = DateTime()
    mail_address = Unicode()
    language = Unicode()
    timezone = Int()
    password_change_needed = Bool()
    password_change_date = DateTime()
    pgp_key_info = Unicode()
    pgp_key_fingerprint = Unicode()
    pgp_key_public = Unicode()
    pgp_key_expiration = DateTime()
    pgp_key_status = Unicode()


class MigrationScript(MigrationBase):
    def migrate_Node(self):
        old_node = self.store_old.find(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for _, v in new_node._storm_columns.iteritems():
            if v.name == 'receipt_salt':
                new_node.receipt_salt = sha512(old_node.receipt_salt.encode('utf8'))[:32]
                continue

            setattr(new_node, v.name, getattr(old_node, v.name))

        self.store_new.add(new_node)


    def migrate_User(self):
        old_objs = self.store_old.find(self.model_from['User'])
        for old_obj in old_objs:
            new_obj = self.model_to['User']()

            for _, v in new_obj._storm_columns.iteritems():
                if v.name == 'salt':
                    new_obj.salt = sha512(old_obj.salt.encode('utf8'))[:32]
                    continue

                setattr(new_obj, v.name, getattr(old_obj, v.name))

            self.store_new.add(new_obj)
