# -*- coding: utf-8
#
#   user
#   *****
# Implementation of the User model functionalities
#
from six import text_type

from globaleaks import models
from globaleaks.db import db_refresh_memory_variables
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.user import db_get_user, \
                                     parse_pgp_options, \
                                     user_serialize_user, \
                                     serialize_usertenant_association

from globaleaks.models import fill_localized_keys, get_localized_values
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.state import State
from globaleaks.utils.crypto import GCE
from globaleaks.utils.utility import datetime_now, uuid4


def db_create_usertenant_association(session, user_id, tenant_id):
    usertenant = models.UserTenant()
    usertenant.user_id = user_id
    usertenant.tenant_id = tenant_id
    session.add(usertenant)
    return serialize_usertenant_association(usertenant)


@transact
def create_usertenant_association(session, user_id, tenant_id):
    return db_create_usertenant_association(session, user_id, tenant_id)


@transact
def create_user(session, tid, request, language):
    return user_serialize_user(session, db_create_user(session, tid, request, language), language)


def db_create_user(session, tid, request, language):
    request['tid'] = tid

    fill_localized_keys(request, models.User.localized_keys, language)

    if request['username']:
        user = session.query(models.User).filter(models.User.username == text_type(request['username']),
                                                 models.UserTenant.user_id == models.User.id,
                                                 models.UserTenant.tenant_id == tid).one_or_none()
        if user is not None:
            raise errors.InputValidationError('Username already in use')

    user = models.User({
        'tid': tid,
        'username': request['username'],
        'role': request['role'],
        'state': u'enabled',
        'name': request['name'],
        'description': request['description'],
        'language': language,
        'password_change_needed': request['password_change_needed'],
        'mail_address': request['mail_address'],
        'can_edit_general_settings': request['can_edit_general_settings']
    })

    if not request['username']:
        user.username = user.id = uuid4()

    password = u'password'
    if request['password']:
        password = request['password']

    user.hash_alg = GCE.HASH
    user.salt = GCE.generate_salt()
    user.password = GCE.hash_password(password, user.salt)

    # The various options related in manage PGP keys are used here.
    parse_pgp_options(user, request)

    session.add(user)

    session.flush()

    db_create_usertenant_association(session, user.id, tid)

    return user


def db_admin_update_user(session, tid, user_id, request, language):
    """
    Updates the specified user.
    """
    fill_localized_keys(request, models.User.localized_keys, language)

    user = db_get_user(session, tid, user_id)

    if user.username != request['username']:
        check = session.query(models.User).filter(models.User.username == text_type(request['username']),
                                                  models.UserTenant.user_id == models.User.id,
                                                  models.UserTenant.tenant_id == tid).one_or_none()
        if check is not None:
            raise errors.InputValidationError('Username already in use')

    user.update(request)

    password = request['password']
    if password:
        user.hash_alg = GCE.HASH
        user.salt = GCE.generate_salt()
        user.password = GCE.hash_password(password, user.salt)
        user.password_change_date = datetime_now()
        user.crypto_prv_key = b''
        user.crypto_pub_key = b''

    # The various options related in manage PGP keys are used here.
    parse_pgp_options(user, request)

    if user.role == 'admin':
        db_refresh_memory_variables(session, [tid])

    return user


@transact
def admin_update_user(session, tid, user_id, request, language):
    return user_serialize_user(session, db_admin_update_user(session, tid, user_id, request, language), language)



@transact
def delete_user(session, tid, user_id):
    user = db_get_user(session, tid, user_id)

    if user is not None:
        session.delete(user)


def db_get_admin_users(session, tid):
    users = session.query(models.User).filter(models.User.role == u'admin',
                                              models.UserTenant.user_id == models.User.id,
                                              models.UserTenant.tenant_id == tid)

    return [user_serialize_user(session, user, State.tenant_cache[tid].default_language) for user in users]


@transact
def get_receiver_list(session, tid, language):
    """
    Returns:
        (list) the list of recipients
    """
    users = session.query(models.User).filter(models.User.role == u'receiver',
                                              models.UserTenant.user_id == models.User.id,
                                              models.UserTenant.tenant_id == tid)

    return [user_serialize_user(session, user, language) for user in users]


@transact
def get_user_list(session, tid, language):
    """
    Returns:
        (list) the list of users
    """
    users = session.query(models.User).filter(models.UserTenant.user_id == models.User.id,
                                              models.UserTenant.tenant_id == tid)

    return [user_serialize_user(session, user, language) for user in users]


class UsersCollection(BaseHandler):
    check_roles = 'admin'
    cache_resource = True
    invalidate_cache = True

    def get(self):
        """
        Return all the users.
        """
        return get_user_list(self.request.tid, self.request.language)

    def post(self):
        """
        Create a new user
        """
        request = self.validate_message(self.request.content.read(),
                                        requests.UserUserDesc)

        return create_user(self.request.tid, request, self.request.language)


class UserInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def put(self, user_id):
        """
        Update the specified user.
        """
        request = self.validate_message(self.request.content.read(), requests.UserUserDesc)

        return admin_update_user(self.request.tid, user_id, request, self.request.language)

    def delete(self, user_id):
        """
        Delete the specified user.
        """
        return delete_user(self.request.tid, user_id)


class UserTenantCollection(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True
    root_tenant_only = True

    def post(self, user_id):
        """Creates a list of user/tenant associations"""
        request = self.validate_message(self.request.content.read(), requests.UserTenantDesc)
        return create_usertenant_association(user_id, request['tenant_id'])


class UserTenantInstance(BaseHandler):
    check_role = 'admin'
    invalidate_cache = True
    root_tenant_only = True

    def delete(self, user_id, tenant_id):
        return models.delete(models.UserTenant,
                             models.UserTenant.user_id == user_id,
                             models.UserTenant.tenant_id == tenant_id)
