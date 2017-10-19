# -*- coding: utf-8
#
#   user
#   *****
# Implementation of the User model functionalities
#
from globaleaks import models, security
from globaleaks.db import db_refresh_memory_variables
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.user import parse_pgp_options, user_serialize_user
from globaleaks.orm import transact
from globaleaks.rest import requests, errors
from globaleaks.state import State
from globaleaks.utils.structures import fill_localized_keys, get_localized_values
from globaleaks.utils.utility import log, datetime_now


def admin_serialize_receiver(store, receiver, user, language):
    """
    Serialize the specified receiver

    :param language: the language in which to localize data
    :return: a dictionary representing the serialization of the receiver
    """
    ret_dict = user_serialize_user(store, user, language)

    ret_dict.update({
        'can_delete_submission': receiver.can_delete_submission,
        'can_postpone_expiration': receiver.can_postpone_expiration,
        'can_grant_permissions': receiver.can_grant_permissions,
        'mail_address': user.mail_address,
        'configuration': receiver.configuration,
        'tip_notification': receiver.tip_notification
    })

    return get_localized_values(ret_dict, receiver, receiver.localized_keys, language)


def db_create_admin_user(store, request, language):
    """
    Creates a new admin
    Returns:
        (dict) the admin descriptor
    """
    user = db_create_user(store, request, language)

    log.debug("Created new admin")

    db_refresh_memory_variables(store)

    return user


@transact
def create_admin_user(store, request, language):
    return user_serialize_user(store, db_create_admin_user(store, request, language), language)


def db_create_custodian_user(store, request, language):
    """
    Creates a new custodian
    Returns:
        (dict) the custodian descriptor
    """
    user = db_create_user(store, request, language)

    log.debug("Created new custodian")

    return user


@transact
def create_custodian_user(store, request, language):
    return user_serialize_user(store, db_create_custodian_user(store, request, language), language)


def db_create_receiver_user(store, request, language):
    """
    Creates a new receiver
    Returns:
        (dict) the receiver descriptor
    """
    fill_localized_keys(request, models.Receiver.localized_keys, language)

    user = db_create_user(store, request, language)

    receiver = models.db_forge_obj(store, models.Receiver, request)

    # set receiver.id user.id
    receiver.id = user.id

    log.debug("Created new receiver")

    return receiver, user


@transact
def create_receiver_user(store, request, language):
    receiver, user = db_create_receiver_user(store, request, language)
    return admin_serialize_receiver(store, receiver, user, language)


def create(request, language):
    if request['role'] == 'receiver':
        return create_receiver_user(request, language)
    elif request['role'] == 'custodian':
        return create_custodian_user(request, language)
    elif request['role'] == 'admin':
        return create_admin_user(request, language)
    else:
        raise errors.InvalidInputFormat


def db_create_user(store, request, language):
    fill_localized_keys(request, models.User.localized_keys, language)

    user = models.User({
        'username': request['username'],
        'role': request['role'],
        'state': u'enabled',
        'deletable': request['deletable'],
        'name': request['name'],
        'description': request['description'],
        'public_name': request['public_name'] if request['public_name'] else request['name'],
        'language': language,
        'password_change_needed': request['password_change_needed'],
        'mail_address': request['mail_address']
    })

    if not request['username']:
        user.username = user.id

    password = request['password'] if request['password'] else State.tenant_cache[1].default_password

    user.salt = security.generateRandomSalt()
    user.password = security.hash_password(password, user.salt)

    # The various options related in manage PGP keys are used here.
    parse_pgp_options(user, request)

    store.add(user)

    return user


def db_admin_update_user(store, user_id, request, language):
    """
    Updates the specified user.
    raises: globaleaks.errors.UserIdNotFound` if the user does not exist.
    """
    fill_localized_keys(request, models.User.localized_keys, language)

    user = models.db_get(store, models.User, id=user_id)

    user.update(request)

    password = request['password']
    if password:
        user.password = security.hash_password(password, user.salt)
        user.password_change_date = datetime_now()

    # The various options related in manage PGP keys are used here.
    parse_pgp_options(user, request)

    if user.role == 'admin':
        db_refresh_memory_variables(store)

    return user


@transact
def admin_update_user(store, user_id, request, language):
    return user_serialize_user(store, db_admin_update_user(store, user_id, request, language), language)


@transact
def get_user(store, user_id, language):
    user = models.db_get(store, models.User, id=user_id)

    return user_serialize_user(store, user, language)


def db_get_admin_users(store):
    return [user_serialize_user(store, user, State.tenant_cache[1].default_language)
            for user in store.find(models.User, role=u'admin')]


@transact
def delete_user(store, user_id):
    user = models.db_get(store, models.User, id=user_id)

    if not user.deletable:
        raise errors.UserNotDeletable

    store.remove(user)


@transact
def get_user_list(store, language):
    """
    Returns:
        (list) the list of users
    """
    users = store.find(models.User)
    return [user_serialize_user(store, user, language) for user in users]


class UsersCollection(BaseHandler):
    check_roles = 'admin'
    cache_resource = True
    invalidate_cache = True

    def get(self):
        """
        Return all the users.

        Parameters: None
        Response: adminUsersList
        Errors: None
        """
        return get_user_list(self.request.language)

    def post(self):
        """
        Create a new user

        Request: AdminUserDesc
        Response: AdminUserDesc
        Errors: InvalidInputFormat, UserIdNotFound
        """
        request = self.validate_message(self.request.content.read(),
                                        requests.AdminUserDesc)

        return create(request, self.request.language)


class UserInstance(BaseHandler):
    check_roles = 'admin'
    invalidate_cache = True

    def put(self, user_id):
        """
        Update the specified user.

        Parameters: user_id
        Request: AdminUserDesc
        Response: AdminUserDesc
        Errors: InvalidInputFormat, UserIdNotFound
        """
        request = self.validate_message(self.request.content.read(), requests.AdminUserDesc)

        return admin_update_user(user_id, request, self.request.language)

    def delete(self, user_id):
        """
        Delete the specified user.

        Parameters: user_id
        Request: None
        Response: None
        Errors: InvalidInputFormat, UserIdNotFound
        """
        return delete_user(user_id)
