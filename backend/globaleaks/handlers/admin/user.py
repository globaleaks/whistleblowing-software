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
from globaleaks.handlers.user import parse_pgp_options, \
                                     user_serialize_user, \
                                     serialize_usertenant_association

from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.state import State
from globaleaks.utils import security
from globaleaks.utils.structures import fill_localized_keys, get_localized_values
from globaleaks.utils.utility import datetime_now


def admin_serialize_receiver(session, receiver, user, language):
    """
    Serialize the specified receiver

    :param language: the language in which to localize data
    :return: a dictionary representing the serialization of the receiver
    """
    ret_dict = user_serialize_user(session, user, language)

    ret_dict.update({
        'can_delete_submission': receiver.can_delete_submission,
        'can_postpone_expiration': receiver.can_postpone_expiration,
        'can_grant_permissions': receiver.can_grant_permissions,
        'mail_address': user.mail_address,
        'configuration': receiver.configuration,
        'tip_notification': receiver.tip_notification
    })

    return get_localized_values(ret_dict, receiver, receiver.localized_keys, language)


@transact
def create_user(session, state, tid, request, language):
    return user_serialize_user(session, db_create_user(session, state, tid, request, language), language)


def db_create_receiver_user(session, state, tid, request, language):
    """
    Creates a new receiver
    Returns:
        (dict) the receiver descriptor
    """
    fill_localized_keys(request, models.Receiver.localized_keys, language)

    user = db_create_user(session, state, tid, request, language)

    request['id'] = user.id

    receiver = models.db_forge_obj(session, models.Receiver, request)

    return receiver, user


@transact
def create_receiver_user(session, state, tid, request, language):
    receiver, user = db_create_receiver_user(session, state, tid, request, language)
    return admin_serialize_receiver(session, receiver, user, language)


def create(state, tid, request, language):
    if request['role'] not in ['admin', 'receiver', 'custodian']:
        raise errors.InputValidationError

    if request['role'] == 'receiver':
        d = create_receiver_user(state, tid, request, language)
    else:
        d = create_user(state, tid, request, language)

    return d


def db_create_user(session, state, tid, request, language):
    request['tid'] = tid

    fill_localized_keys(request, models.User.localized_keys, language)

    if request['username']:
        user = session.query(models.User).filter(models.User.tid == tid, models.User.username == text_type(request['username'])).one_or_none()
        if user is not None:
            raise errors.InputValidationError('Username already in use')

    user = models.User({
        'tid': tid,
        'username': request['username'],
        'role': request['role'],
        'state': u'enabled',
        'name': request['name'],
        'description': request['description'],
        'name': request['name'],
        'language': language,
        'password_change_needed': request['password_change_needed'],
        'mail_address': request['mail_address'],
        'can_edit_general_settings': request['can_edit_general_settings']
    })

    if request['password']:
        password = request['password']
    elif user.role == 'receiver':
        # code necessary because the user.role for recipient is receiver
        password = 'recipient'
    else:
        password = user.role

    user.salt = security.generateRandomSalt()
    user.password = security.hash_password(password, user.salt)

    # The various options related in manage PGP keys are used here.
    parse_pgp_options(state, user, request)

    session.add(user)

    session.flush()

    if not request['username']:
        user.username = user.id

    return user


def db_admin_update_user(session, state, tid, user_id, request, language):
    """
    Updates the specified user.
    """
    fill_localized_keys(request, models.User.localized_keys, language)

    user = models.db_get(session, models.User, models.User.tid == tid, models.User.id == user_id)

    if user.username != request['username']:
        check = session.query(models.User).filter(models.User.tid == tid, models.User.username == text_type(request['username'])).one_or_none()
        if check is not None:
            raise errors.InputValidationError('Username already in use')

    user.update(request)

    password = request['password']
    if password:
        user.password = security.hash_password(password, user.salt)
        user.password_change_date = datetime_now()

    # The various options related in manage PGP keys are used here.
    parse_pgp_options(state, user, request)

    if user.role == 'admin':
        db_refresh_memory_variables(session, [tid])

    return user


@transact
def admin_update_user(session, state, tid, user_id, request, language):
    return user_serialize_user(session, db_admin_update_user(session, state, tid, user_id, request, language), language)


@transact
def get_user(session, tid, user_id, language):
    user = models.db_get(session, models.User, models.User.tid == tid, models.User.id == user_id)

    return user_serialize_user(session, user, language)


def db_get_admin_users(session, tid):
    return [user_serialize_user(session, user, State.tenant_cache[tid].default_language)
            for user in session.query(models.User).filter(models.User.tid == tid, models.User.role ==u'admin')]


@transact
def get_user_list(session, tid, language):
    """
    Returns:
        (list) the list of users
    """
    users = session.query(models.User).filter(models.User.tid == tid)
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
                                        requests.AdminUserDesc)

        return create(self.state, self.request.tid, request, self.request.language)


class UserInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def put(self, user_id):
        """
        Update the specified user.
        """
        request = self.validate_message(self.request.content.read(), requests.AdminUserDesc)

        return admin_update_user(self.state, self.request.tid, user_id, request, self.request.language)

    def delete(self, user_id):
        """
        Delete the specified user.
        """
        return models.delete(models.User, models.User.tid == self.request.tid, models.User.id == user_id)


@transact
def create_usertenant_association(session, user_id, tenant_id):
    usertenant = models.UserTenant()
    usertenant.user_id = user_id
    usertenant.tenant_id = tenant_id
    session.add(usertenant)
    return serialize_usertenant_association(usertenant)


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