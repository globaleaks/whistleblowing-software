# -*- encoding: utf-8 -*-

import copy
import json
import os

from storm.locals import Int, Bool, Unicode, DateTime, JSON, Reference, ReferenceSet

from globaleaks.db.base_updater import TableReplacer
from globaleaks.models import Model
from globaleaks.settings import GLSettings
from globaleaks.utils.utility import datetime_null

class User_v_23(Model):
    __storm_table__ = 'user'
    creation_date = DateTime()
    username = Unicode()
    password = Unicode()
    salt = Unicode()
    role = Unicode()
    state = Unicode()
    last_login = DateTime()
    mail_address = Unicode()
    language = Unicode()
    timezone = Int()
    password_change_needed = Bool()
    password_change_date = DateTime()


class Receiver_v_23(Model):
    __storm_table__ = 'receiver'
    name = Unicode()
    description = JSON()
    configuration = Unicode()
    pgp_key_info = Unicode()
    pgp_key_fingerprint = Unicode()
    pgp_key_public = Unicode()
    pgp_key_expiration = DateTime()
    pgp_key_status = Unicode()
    ping_mail_address = Unicode()
    can_delete_submission = Bool()
    can_postpone_expiration = Bool()
    tip_notification = Bool()
    ping_notification = Bool()
    tip_expiration_threshold = Int()
    presentation_order = Int()


Receiver_v_23.user = Reference(Receiver_v_23.id, User_v_23.id)


class Replacer2324(TableReplacer):
    def migrate_Receiver(self):
        print "%s Receiver migration assistant" % self.std_fancy

        old_receivers = self.store_old.find(self.get_right_model("Receiver", 23))

        for old_receiver in old_receivers:
            new_user = self.get_right_model("User", 24)()
            new_receiver = self.get_right_model("Receiver", 24)()

            for _, v in new_user._storm_columns.iteritems():
                if v.name == 'pgp_key_status':
                    new_user.pgp_key_status = old_receiver.pgp_key_status
                    continue

                if v.name == 'pgp_key_info':
                    new_user.pgp_key_info = old_receiver.pgp_key_info
                    continue

                if v.name == 'pgp_key_fingerprint':
                    new_user.pgp_key_fingerprint = old_receiver.pgp_key_fingerprint
                    continue

                if v.name == 'pgp_key_public':
                    new_user.pgp_key_public = old_receiver.pgp_key_public
                    continue

                if v.name == 'pgp_key_expiration':
                    new_user.pgp_key_expiration = old_receiver.pgp_key_expiration
                    continue

                setattr(new_user, v.name, getattr(old_receiver.user, v.name))

            for _, v in new_receiver._storm_columns.iteritems():
                setattr(new_receiver, v.name, getattr(old_receiver, v.name))

            # migrating we use old_receiver.id in order to not loose receiver-context associations
            new_receiver.id = new_user.username = new_user.id = old_receiver.id

            self.store_new.add(new_user)
            self.store_new.add(new_receiver)
        self.store_new.commit()


    def migrate_User(self):
        # Receivers and Users are migrated all together this time!
        # The only user to be migrated separately is the admin
        old_user_model = self.get_right_model("User", 23)
        old_admin = self.store_old.find(old_user_model, old_user_model.username == u'admin').one()

        new_admin = self.get_right_model("User", 24)()
        for _, v in new_admin._storm_columns.iteritems():
            if v.name == 'pgp_key_status':
                new_admin.pgp_key_status = 'disabled'
                continue

            if v.name == 'pgp_key_info':
                new_admin.pgp_key_info = ''
                continue

            if v.name == 'pgp_key_fingerprint':
                new_admin.pgp_key_fingerprint = ''
                continue

            if v.name == 'pgp_key_public':
                new_admin.pgp_key_public = ''
                continue

            if v.name == 'pgp_key_expiration':
                new_admin.pgp_key_expiration = datetime_null()
                continue

            setattr(new_admin, v.name, getattr(old_admin, v.name))

        self.store_new.add(new_admin)
        self.store_new.commit()

