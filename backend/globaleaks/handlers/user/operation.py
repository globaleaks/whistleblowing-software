# -*- coding: utf-8
#
# Handlers dealing with user operations
from nacl.encoding import Base32Encoder, Base64Encoder

from globaleaks import models
from globaleaks.handlers.operation import OperationHandler
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.state import State
from globaleaks.transactions import db_get_user
from globaleaks.utils.crypto import GCE


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

    # RFC 6238: step size 30 sec; valid_window = 1; total size of the window: 1.30 sec
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
            'get_users_names': UserOperationHandler.get_users_names,
            'get_recovery_key': UserOperationHandler.get_recovery_key,
            'enable_2fa': UserOperationHandler.enable_2fa,
            'disable_2fa': UserOperationHandler.disable_2fa
        }
