# -*- coding: utf-8
#
# Handlers dealing with user preferences
import base64
import os

from nacl.encoding import Base32Encoder, Base64Encoder
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.operation import OperationHandler
from globaleaks.models import get_localized_values
from globaleaks.orm import db_get, transact
from globaleaks.rest import errors, requests
from globaleaks.state import State
from globaleaks.utils.pgp import PGPContext
from globaleaks.utils.crypto import generateOtpSecret, generateRandomKey, totpVerify, GCE
from globaleaks.utils.utility import datetime_now, datetime_null


def set_user_password(tid, user, password, cc):
    # Regenerate the password hash only if different from the best choice on the platform
    if user.hash_alg != 'ARGON2':
        user.hash_alg = 'ARGON2'
        user.salt = GCE.generate_salt()

    password_hash = GCE.hash_password(password, user.salt)

    # Check that the new password is different form the current password
    if user.password == password_hash:
        raise errors.PasswordReuseError

    user.password = password_hash
    user.password_change_date = datetime_now()

    State.log(tid=tid, type='change_password', user_id=user.id, object_id=user.id)

    if not State.tenant_cache[tid].encryption and cc == '':
        return None

    enc_key = GCE.derive_key(password.encode(), user.salt)
    if not cc:
        # The first password change triggers the generation
        # of the user encryption private key and its backup
        cc, user.crypto_pub_key = GCE.generate_keypair()
        user.crypto_bkp_key, user.crypto_rec_key = GCE.generate_recovery_key(cc)

    user.crypto_prv_key = Base64Encoder.encode(GCE.symmetric_encrypt(enc_key, cc))

    if State.tenant_cache[1].crypto_escrow_pub_key:
        user.crypto_escrow_bkp1_key = Base64Encoder.encode(GCE.asymmetric_encrypt(State.tenant_cache[1].crypto_escrow_pub_key, cc))

    if State.tenant_cache[tid].crypto_escrow_pub_key:
        user.crypto_escrow_bkp2_key = Base64Encoder.encode(GCE.asymmetric_encrypt(State.tenant_cache[tid].crypto_escrow_pub_key, cc))

    return cc


def parse_pgp_options(user, request):
    """
    Used for parsing PGP key infos and fill related user configurations.

    :param user: A user model
    :param request: A request to be parsed
    """
    pgp_key_public = request['pgp_key_public']
    remove_key = request['pgp_key_remove']

    k = None
    if not remove_key and pgp_key_public:
        pgpctx = PGPContext(State.settings.tmp_path)

        k = pgpctx.load_key(pgp_key_public)

    if k is not None:
        user.pgp_key_public = pgp_key_public
        user.pgp_key_fingerprint = k['fingerprint']
        user.pgp_key_expiration = k['expiration']
    else:
        user.pgp_key_public = ''
        user.pgp_key_fingerprint = ''
        user.pgp_key_expiration = datetime_null()


def user_serialize_user(session, user, language):
    """
    Serialize user model

    :param user: the user object
    :param language: the language of the data
    :param session: the session on which perform queries.
    :return: a serialization of the object
    """
    picture = session.query(models.File).filter(models.File.name == user.id).one_or_none() is not None

    # take only contexts for the current tenant
    contexts = [x[0] for x in session.query(models.ReceiverContext.context_id)
                                     .filter(models.ReceiverContext.receiver_id == user.id)]
    ret = {
        'id': user.id,
        'creation_date': user.creation_date,
        'username': user.username,
        'password': '',
        'old_password': '',
        'salt': '',
        'role': user.role,
        'state': user.state,
        'last_login': user.last_login,
        'name': user.name,
        'description': user.description,
        'public_name': user.public_name,
        'mail_address': user.mail_address,
        'change_email_address': user.change_email_address,
        'language': user.language,
        'password_change_needed': user.password_change_needed,
        'password_change_date': user.password_change_date,
        'pgp_key_fingerprint': user.pgp_key_fingerprint,
        'pgp_key_public': user.pgp_key_public,
        'pgp_key_expiration': user.pgp_key_expiration,
        'pgp_key_remove': False,
        'picture': picture,
        'can_edit_general_settings': user.can_edit_general_settings,
        'tid': user.tid,
        'notification': user.notification,
        'encryption': user.crypto_pub_key != '',
        'escrow': user.crypto_escrow_prv_key != '',
        'two_factor_enable': user.two_factor_enable,
        'forcefully_selected': user.forcefully_selected,
        'can_postpone_expiration': user.can_postpone_expiration,
        'can_delete_submission': user.can_delete_submission,
        'clicked_recovery_key': user.clicked_recovery_key,
        'send_account_activation_link': False,
        'contexts': contexts
    }

    if user.tid in State.tenant_cache:
        ret.update({
            'can_postpone_expiration': State.tenant_cache[user.tid].can_postpone_expiration or user.can_postpone_expiration,
            'can_delete_submission': State.tenant_cache[user.tid].can_delete_submission or user.can_delete_submission
        })

    return get_localized_values(ret, user, user.localized_keys, language)


def db_get_user(session, tid, user_id):
    """
    Transaction for retrieving a user model given an id

    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: A id of the user to retrieve
    :return: A retrieved model
    """
    return db_get(session,
                  models.User,
                  (models.User.id == user_id,
                   models.User.tid == tid))


@transact
def get_user(session, tid, user_id, language):
    """
    Transaction for retrieving a user model given an id

    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: A id of the user to retrieve
    :param language: The language to be used in the serialization
    :return: A serialization of the retrieved user
    """
    user = db_get_user(session, tid, user_id)

    return user_serialize_user(session, user, language)


def db_user_update_user(session, tid, user_session, request):
    """
    Transaction for updating an existing user

    :param session: An ORM session
    :param tid: A tenant ID
    :param user_session: A session of the user invoking the transaction
    :param request: A user request data
    :return: A user model
    """
    from globaleaks.handlers.admin.notification import db_get_notification
    from globaleaks.handlers.admin.node import db_admin_serialize_node

    user = db_get(session,
                  models.User,
                  models.User.id == user_session.user_id)

    user.language = request.get('language', State.tenant_cache[tid].default_language)
    user.name = request['name']
    user.public_name = request['public_name'] if request['public_name'] else request['name']

    if request['password']:
        if user.password_change_needed:
            user.password_change_needed = False
        else:
            if not GCE.check_password(user.hash_alg,
                                      request['old_password'],
                                      user.salt,
                                      user.password):
                raise errors.InvalidOldPassword

        user_session.cc = set_user_password(tid, user, request['password'], user_session.cc)

    # If the email address changed, send a validation email
    if request['mail_address'] != user.mail_address:
        user.change_email_address = request['mail_address']
        user.change_email_date = datetime_now()
        user.change_email_token = generateRandomKey()

        user_desc = user_serialize_user(session, user, user.language)

        user_desc['mail_address'] = request['mail_address']

        template_vars = {
            'type': 'email_validation',
            'user': user_desc,
            'new_email_address': request['mail_address'],
            'validation_token': user.change_email_token,
            'node': db_admin_serialize_node(session, tid, user.language),
            'notification': db_get_notification(session, tid, user.language)
        }

        State.format_and_send_mail(session, tid, user_desc, template_vars)

    parse_pgp_options(user, request)

    return user


@transact
def update_user_settings(session, tid, user_session, request, language):
    """
    Transaction for updating an existing user

    :param session: An ORM session
    :param tid: A tenant ID
    :param user_session: A session of the user invoking the transaction
    :param request: A user request data
    :param language: A language to be used when serializing the user
    :return: A serialization of user model
    """
    user = db_user_update_user(session, tid, user_session, request)

    return user_serialize_user(session, user, language)


@inlineCallbacks
def can_edit_general_settings_or_raise(handler):
    """Determines if this user has ACL permissions to edit general settings"""
    if handler.session.user_role == 'admin':
        returnValue(True)
    else:
        # Get the full user so we can see what we can access
        user = yield get_user(handler.session.user_tid,
                              handler.session.user_id,
                              handler.request.language)
        if user['can_edit_general_settings'] is True:
            returnValue(True)

    raise errors.InvalidAuthentication


class UserInstance(BaseHandler):
    """
    Handler that enables users to update their own setings
    """
    check_roles = 'user'
    invalidate_cache = True

    def get(self):
        return get_user(self.session.user_tid,
                        self.session.user_id,
                        self.request.language)

    def put(self):
        request = self.validate_message(self.request.content.read(), requests.UserUserDesc)

        return update_user_settings(self.session.user_tid,
                                    self.session,
                                    request,
                                    self.request.language)


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
def enable_2fa_step1(session, tid, user_id):
    """
    Transact for the first step of 2fa enrollment (start)

    :param session:
    :param tid:
    :param user_id:
    :return:
    """
    user = db_get_user(session, tid, user_id)

    if user.two_factor_secret:
        return user.two_factor_secret

    user.two_factor_secret = generateOtpSecret()

    return user.two_factor_secret


@transact
def enable_2fa_step2(session, tid, user_id, user_cc, token):
    """
    Transact for the first step of 2fa enrollment (completion)

    :param session: An ORM session
    :param tid: A tenant ID
    :param user_id: A user ID
    :param user_cc: A user private key
    :param token: A token for OTP authentication
    """
    user = db_get_user(session, tid, user_id)

    # RFC 6238: step size 30 sec; valid_window = 1; total size of the window: 1.30 sec
    try:
        totpVerify(user.two_factor_secret, token)
    except:
        raise errors.InvalidTwoFactorAuthCode

    user.two_factor_enable = True


@transact
def disable_2fa(session, tid, user_id):
    """
    Transaction for disabling the two factor authentication

    :param session:
    :param tid:
    :param user_id:
    """
    user = db_get_user(session, tid, user_id)

    user.two_factor_enable = False
    user.two_factor_secret = ''


class UserOperationHandler(OperationHandler):
    check_roles = 'user'

    def get_recovery_key(self, req_args, *args, **kwargs):
        return get_recovery_key(self.session.user_tid,
                                self.session.user_id,
                                self.session.cc)

    def enable_2fa_step1(self, req_args, *args, **kwargs):
        return enable_2fa_step1(self.session.user_tid,
                                self.session.user_id)

    def enable_2fa_step2(self, req_args, *args, **kwargs):
        return enable_2fa_step2(self.session.user_tid,
                                self.session.user_id,
                                self.session.cc,
                                req_args['value'])

    def disable_2fa(self, req_args, *args, **kwargs):
        return disable_2fa(self.session.user_tid,
                           self.session.user_id)

    def operation_descriptors(self):
        return {
            'get_recovery_key': (UserOperationHandler.get_recovery_key, {}),
            'enable_2fa_step1': (UserOperationHandler.enable_2fa_step1, {}),
            'enable_2fa_step2': (UserOperationHandler.enable_2fa_step2, {'value': str}),
            'disable_2fa': (UserOperationHandler.disable_2fa, {})
        }
