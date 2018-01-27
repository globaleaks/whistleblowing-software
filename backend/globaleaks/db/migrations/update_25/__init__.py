# -*- coding: utf-8 -*-

from globaleaks.db.migrations.update import MigrationBase
from globaleaks.models import Model
from globaleaks.models.properties import *
from globaleaks.utils.security import sha512


class User_v_24(Model):
    __tablename__ = 'user'
    id = Column(Unicode(36), primary_key=True, default=uuid4, nullable=False)
    creation_date = Column(DateTime)
    username = Column(UnicodeText)
    password = Column(UnicodeText)
    salt = Column(UnicodeText)
    deletable = Column(Boolean)
    name = Column(UnicodeText)
    description = Column(JSON)
    role = Column(UnicodeText)
    state = Column(UnicodeText)
    last_login = Column(DateTime)
    mail_address = Column(UnicodeText)
    language = Column(UnicodeText)
    timezone = Column(Integer)
    password_change_needed = Column(Boolean)
    password_change_date = Column(DateTime)
    pgp_key_info = Column(UnicodeText)
    pgp_key_fingerprint = Column(UnicodeText)
    pgp_key_public = Column(UnicodeText)
    pgp_key_expiration = Column(DateTime)
    pgp_key_status = Column(UnicodeText)


class SecureFileDelete_v_24(Model):
    __tablename__ = 'securefiledelete'
    filepath = Column(UnicodeText, primary_key=True)


class MigrationScript(MigrationBase):
    def migrate_Node(self):
        old_node = self.session_old.query(self.model_from['Node']).one()
        new_node = self.model_to['Node']()

        for key in [c.key for c in new_node.__table__.columns]:
            if key == 'receipt_salt':
                new_node.receipt_salt = sha512(old_node.receipt_salt.encode('utf8'))[:32]
                continue

            setattr(new_node, key, getattr(old_node, key))

        self.session_new.add(new_node)

    def migrate_User(self):
        old_objs = self.session_old.query(self.model_from['User'])
        for old_obj in old_objs:
            new_obj = self.model_to['User']()

            for key in [c.key for c in new_obj.__table__.columns]:
                if key == 'salt':
                    new_obj.salt = sha512(old_obj.salt.encode('utf8'))[:32]
                    continue

                setattr(new_obj, key, getattr(old_obj, key))

            self.session_new.add(new_obj)
