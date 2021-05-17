# -*- coding: utf-8
from globaleaks import models
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.password_reset import db_generate_password_reset_token
from globaleaks.handlers.user import db_get_user, \
                                     parse_pgp_options, \
                                     user_serialize_user

from globaleaks.models import fill_localized_keys
from globaleaks.orm import db_del, transact, tw
from globaleaks.rest import requests
from globaleaks.state import State
from globaleaks.utils.crypto import GCE, Base64Encoder
from globaleaks.utils.utility import datetime_now, uuid4


def db_create_user(session, tid, request, language):
    """
    Transaction for creating a new user

    :param session: An ORM session
    :param tid: A tenant ID
    :param request: The request data
    :param language: The language of the request
    :return: The serialized descriptor of the created object
    """
    request['tid'] = tid

    fill_localized_keys(request, models.User.localized_keys, language)

    if not request['public_name']:
        request['public_name'] = request['name']

    user = models.User(request)

    if not request['username']:
        user.username = user.id = uuid4()

    user.salt = GCE.generate_salt()

    user.language = request['language']

    # The various options related in manage PGP keys are used here.
    parse_pgp_options(user, request)

    session.add(user)

    session.flush()

    if request.get('send_account_activation_link', False):
        db_generate_password_reset_token(session, user)

    return user


@transact
def create_user(session, tid, request, language):
    """
    Transaction for creating a new user

    :param session: An ORM session
    :param tid: A tenant ID
    :param request: The request data
    :param language: The language of the request
    :return: The serialized descriptor of the created object
    """
    return user_serialize_user(session, db_create_user(session, tid, request, language), language)


def db_admin_update_user(session, tid, user_session, user_id, request, language):
    """
    Transaction for updating an existing user

    :param session: An ORM session
    :param tid: A tenant ID
    :param user_session: The current user session
    :param user_id: The ID of the user to update
    :param request: The request data
    :param language: The language of the request
    :return: The serialized descriptor of the updated object
    """
    fill_localized_keys(request, models.User.localized_keys, language)

    user = db_get_user(session, tid, user_id)

    user.update(request)

    password = request['password']
    if password and (not user.crypto_pub_key or user_session.ek):
        if user.crypto_pub_key and user_session.ek:
            enc_key = GCE.derive_key(password.encode(), user.salt)
            crypto_escrow_prv_key = GCE.asymmetric_decrypt(user_session.cc, Base64Encoder.decode(user_session.ek))

            if user_session.user_tid == 1:
                user_cc = GCE.asymmetric_decrypt(crypto_escrow_prv_key, Base64Encoder.decode(user.crypto_escrow_bkp1_key))
            else:
                user_cc = GCE.asymmetric_decrypt(crypto_escrow_prv_key, Base64Encoder.decode(user.crypto_escrow_bkp2_key))

            user.crypto_prv_key = Base64Encoder.encode(GCE.symmetric_encrypt(enc_key, user_cc))

        if user.hash_alg != 'ARGON2':
            user.hash_alg = 'ARGON2'
            user.salt = GCE.generate_salt()

        user.password = GCE.hash_password(password, user.salt)
        user.password_change_date = datetime_now()

        State.log(tid=tid, type='change_password', user_id=user_session.user_id, object_id=user_id)

    # The various options related in manage PGP keys are used here.
    parse_pgp_options(user, request)

    return user_serialize_user(session, user, language)


def db_get_users(session, tid, role=None, language=None):
    """
    Transaction for retrieving the list of users defined on a tenant

    :param session: An ORM session
    :param tid: A tenant ID
    :param role: The role of the users to be retriven
    :param language: The language to be used during serialization
    :return: A list of serialized descriptors of the users defined on the specified tenant
    """
    if role is None:
        users = session.query(models.User).filter(models.User.tid == tid)
    else:
        users = session.query(models.User).filter(models.User.tid == tid,
                                                  models.User.role == role)

    language = language if language is not None else State.tenant_cache[tid].default_language

    return [user_serialize_user(session, user, language) for user in users]


class UsersCollection(BaseHandler):
    check_roles = 'admin'
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
                  self.session,
                  user_id,
                  request,
                  self.request.language)

    def delete(self, user_id):
        """
        Delete the specified user.
        """
        return tw(db_del,
                  models.User,
                  (models.User.tid == self.request.tid,
                   models.User.id == user_id))
