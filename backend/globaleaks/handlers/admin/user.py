# -*- coding: utf-8
from globaleaks import models
from globaleaks.db import db_refresh_memory_variables
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.password_reset import db_generate_password_reset_token
from globaleaks.handlers.user import db_get_user, \
                                     parse_pgp_options, \
                                     user_serialize_user

from globaleaks.models import fill_localized_keys
from globaleaks.orm import transact, tw
from globaleaks.rest import requests, errors
from globaleaks.state import State
from globaleaks.utils.crypto import GCE, Base64Encoder
from globaleaks.utils.utility import datetime_now, uuid4


def db_create_user(session, tid, request, language):
    request['tid'] = tid

    fill_localized_keys(request, models.User.localized_keys, language)

    if request['username']:
        user = session.query(models.User).filter(models.User.username == request['username'],
                                                 models.User.tid == tid).one_or_none()
        if user is not None:
            raise errors.InputValidationError('Username already in use')

    user = models.User({
        'tid': tid,
        'username': request['username'],
        'role': request['role'],
        'state': 'enabled',
        'name': request['name'],
        'description': request['description'],
        'public_name': request['public_name'] if request['public_name'] else request['name'],
        'language': language,
        'password_change_needed': request['password_change_needed'],
        'mail_address': request['mail_address'],
        'can_edit_general_settings': request['can_edit_general_settings']
    })

    if not request['username']:
        user.username = user.id = uuid4()

    user.salt = GCE.generate_salt()

    # The various options related in manage PGP keys are used here.
    parse_pgp_options(user, request)

    session.add(user)

    session.flush()

    if request.get('send_account_activation_link', False):
        db_generate_password_reset_token(session, user)

    return user


@transact
def create_user(session, tid, request, language):
    return user_serialize_user(session, db_create_user(session, tid, request, language), language)


def db_admin_update_user(session, tid, user_session, user_id, request, language):
    """
    Updates the specified user.
    """
    fill_localized_keys(request, models.User.localized_keys, language)

    user = db_get_user(session, tid, user_id)

    if user.username != request['username']:
        check = session.query(models.User).filter(models.User.username == request['username'],
                                                  models.User.tid == tid).one_or_none()
        if check is not None:
            raise errors.InputValidationError('Username already in use')

    user.update(request)

    password = request['password']
    if password:
        if not user.crypto_pub_key:
            user.hash_alg = 'ARGON2'
            user.salt = GCE.generate_salt()
        elif user_session.ek:
            enc_key = GCE.derive_key(request['password'].encode(), user.salt)
            crypto_escrow_prv_key = GCE.asymmetric_decrypt(user_session.cc, Base64Encoder.decode(user_session.ek))

            if tid == 1:
                user_cc = GCE.asymmetric_decrypt(crypto_escrow_prv_key, Base64Encoder.decode(user.crypto_escrow_bkp1_key))
            else:
                user_cc = GCE.asymmetric_decrypt(crypto_escrow_prv_key, Base64Encoder.decode(user.crypto_escrow_bkp2_key))

            user.crypto_prv_key = Base64Encoder.encode(GCE.symmetric_encrypt(enc_key, user_cc))

        user.password = GCE.hash_password(password, user.salt)
        user.password_change_date = datetime_now()

    # The various options related in manage PGP keys are used here.
    parse_pgp_options(user, request)

    if user.role == 'admin':
        db_refresh_memory_variables(session, [tid])

    return user_serialize_user(session, user, language)


def db_get_users(session, tid, role=None, language=None):
    if role is None:
        users = session.query(models.User).filter(models.User.tid == tid)
    else:
        users = session.query(models.User).filter(models.User.tid == tid,
                                                  models.User.role == role)

    language = language if language is not None else State.tenant_cache[tid].default_language

    return [user_serialize_user(session, user, language) for user in users]


class UsersCollection(BaseHandler):
    check_roles = 'admin'
    cache_resource = True
    invalidate_cache = True

    def get(self):
        """
        Return all the users.
        """
        return tw(db_get_users, self.request.tid, None, self.request.language)

    def post(self):
        """
        Create a new user
        """
        request = self.validate_message(self.request.content.read(),
                                        requests.AdminUserDesc)

        return create_user(self.request.tid, request, self.request.language)


class UserInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def put(self, user_id):
        """
        Update the specified user.
        """
        request = self.validate_message(self.request.content.read(), requests.AdminUserDesc)

        return tw(db_admin_update_user,
                  self.request.tid,
                  self.current_user,
                  user_id,
                  request,
                  self.request.language)

    def delete(self, user_id):
        """
        Delete the specified user.
        """
        return models.delete(models.User,
                             models.User.tid == self.request.tid,
                             models.User.id == user_id)
