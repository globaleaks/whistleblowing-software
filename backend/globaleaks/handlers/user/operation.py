# -*- coding: utf-8
#
# Handlers dealing with user operations
import os
from nacl.encoding import Base32Encoder, Base64Encoder

from globaleaks import models
from globaleaks.handlers.operation import OperationHandler
from globaleaks.orm import db_log, transact
from globaleaks.rest import errors
from globaleaks.state import State
from globaleaks.transactions import db_get_user
from globaleaks.utils.crypto import GCE
from globaleaks.utils.fs import srm
from globaleaks.utils.utility import datetime_now


def check_password_strength(password):
    return len(password) >= 10 and \
           any(char.isdigit() for char in password) and \
           any(char.isupper() for char in password) and \
           any(char.islower() for char in password) and \
           any(not char.isalnum() for char in password)


@transact
def change_password(session, tid, user_session, password, old_password):
    user = db_get_user(session, tid, user_session.user_id)

    if not user.password_change_needed:
        if not GCE.check_password(old_password,
                                  user.salt,
                                  user.password):
           raise errors.InvalidOldPassword

    config = models.config.ConfigFactory(session, tid)

    # Regenerate the password hash only if different from the best choice on the platform
    if user.hash_alg != 'ARGON2':
        user.hash_alg = 'ARGON2'
        user.salt = GCE.generate_salt()

    if not check_password_strength(password):
        raise errors.InputValidationError("The password is too weak")

    # Check that the new password is different form the current password
    password_hash = GCE.hash_password(password, user.salt)
    if user.password == password_hash:
        raise errors.PasswordReuseError

    user.password = password_hash
    user.password_change_date = datetime_now()
    user.password_change_needed = False

    cc = ''
    if config.get_val('encryption'):
        enc_key = GCE.derive_key(password.encode(), user.salt)
        cc = user_session.cc
        if not cc:
            # The first password change triggers the generation
            # of the user encryption private key and its backup
            cc, user.crypto_pub_key = GCE.generate_keypair()
            user.crypto_bkp_key, user.crypto_rec_key = GCE.generate_recovery_key(cc)

        user.crypto_prv_key = Base64Encoder.encode(GCE.symmetric_encrypt(enc_key, cc))

        root_config = models.config.ConfigFactory(session, 1)
        crypto_escrow_pub_key_tenant_1 = root_config.get_val('crypto_escrow_pub_key')
        if crypto_escrow_pub_key_tenant_1:
            user.crypto_escrow_bkp1_key = Base64Encoder.encode(GCE.asymmetric_encrypt(crypto_escrow_pub_key_tenant_1, cc))

        if tid != 1:
            crypto_escrow_pub_key_tenant_n = config.get_val('crypto_escrow_pub_key')
            if crypto_escrow_pub_key_tenant_n:
                user.crypto_escrow_bkp2_key = Base64Encoder.encode(GCE.asymmetric_encrypt(crypto_escrow_pub_key_tenant_n, cc))

    reset_token = user_session.properties.get('reset_token')
    if reset_token:
        srm(os.path.abspath(os.path.join(State.settings.ramdisk_path, reset_token)))
        del user_session.properties['reset_token']

    db_log(session, tid=tid, type='change_password', user_id=user.id, object_id=user.id)

    user_session.cc = cc


@transact
def get_users_names(session, tid, user_id):
    ret = {}

    for user_id, user_name in session.query(models.User.id, models.User.name).filter(models.User.tid == tid):
        ret[user_id] = user_name

    return ret


@transact
def get_recovery_key(session, tid, user_id, user_cc):
    """
    Transaction to get a user recovery key

    :param session: An ORM session
    :param tid: The tenant ID
    :param user_id: The user ID
    :param user_cc: The user key
    :return: The recovery key encoded base32
    """
    user = db_get_user(session, tid, user_id)

    if not user.crypto_rec_key:
        return ''

    user.clicked_recovery_key = True

    return Base32Encoder.encode(GCE.asymmetric_decrypt(user_cc, Base64Encoder.decode(user.crypto_rec_key.encode()))).replace(b'=', b'')


@transact
def enable_2fa(session, tid, user_id, secret, token):
    """
    Transact for the first step of 2fa enrollment (completion)

    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: A user ID
    :param secret: A two factor secret
    :param token: The current two factor token
    """
    user = db_get_user(session, tid, user_id)

    try:
        State.totp_verify(secret, token)
    except Exception:
        raise errors.InvalidTwoFactorAuthCode

    user.two_factor_secret = secret


@transact
def disable_2fa(session, tid, user_id):
    """
    Transaction for disabling the two factor authentication

    :param session:
    :param tid:
    :param user_id:
    """
    user = db_get_user(session, tid, user_id)

    user.two_factor_secret = ''


class UserOperationHandler(OperationHandler):
    check_roles = 'user'

    require_confirmation = [
        'disable_2fa',
        'get_recovery_key'
    ]

    def change_password(self, req_args, *args, **kwargs):
        return change_password(self.session.user_tid,
                               self.session,
                               req_args['password'],
                               req_args['current'])

    def get_users_names(self, req_args, *args, **kwargs):
        return get_users_names(self.session.user_tid,
                               self.session.user_id)

    def get_recovery_key(self, req_args, *args, **kwargs):
        return get_recovery_key(self.session.user_tid,
                                self.session.user_id,
                                self.session.cc)

    def enable_2fa(self, req_args, *args, **kwargs):
        return enable_2fa(self.session.user_tid,
                          self.session.user_id,
                          req_args['secret'],
                          req_args['token'])

    def disable_2fa(self, req_args, *args, **kwargs):
        return disable_2fa(self.session.user_tid,
                           self.session.user_id)

    def operation_descriptors(self):
        return {
            'change_password': UserOperationHandler.change_password,
            'get_users_names': UserOperationHandler.get_users_names,
            'get_recovery_key': UserOperationHandler.get_recovery_key,
            'enable_2fa': UserOperationHandler.enable_2fa,
            'disable_2fa': UserOperationHandler.disable_2fa
        }
