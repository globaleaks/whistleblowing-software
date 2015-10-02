# -*- coding: UTF-8
#
#   user
#   *****
# Implementation of the User model functionalities
#
import os
import shutil

from twisted.internet.defer import inlineCallbacks

from globaleaks import models, security
from globaleaks.handlers.authentication import transport_security_check, authenticated
from globaleaks.handlers.base import BaseHandler
from globaleaks.handlers.user import parse_pgp_options, user_serialize_user
from globaleaks.rest import requests, errors
from globaleaks.rest.apicache import GLApiCache
from globaleaks.settings import GLSettings, transact, transact_ro
from globaleaks.third_party import rstr
from globaleaks.utils.structures import fill_localized_keys, get_localized_values
from globaleaks.utils.utility import log, datetime_now, datetime_null, datetime_to_ISO8601


def db_create_admin(store, request, language):
    """
    Creates a new admin
    Returns:
        (dict) the admin descriptor
    """
    user = db_create_user(store, request, language)

    log.debug("Created new admin")

    return user

@transact
def create_admin(store, request, language):
    """
    Currently this function simply serialize the admin user.
    In the future this will serialize the admin model with its peculiatieis.
    """
    admin = db_create_admin(store, request, language)
    return user_serialize_user(admin, language)

@transact
def create_admin_user(store, request, language):
    admin = db_create_admin(store, request, language)
    return user_serialize_user(admin, language)


def db_create_custodian(store, request, language):
    """
    Creates a new custodian
    Returns:
        (dict) the custodian descriptor
    """
    user = db_create_user(store, request, language)

    fill_localized_keys(request, models.Custodian.localized_strings, language)

    custodian = models.Custodian(request)

    # set custodian.id = user.id
    custodian.id = user.id

    store.add(custodian)

    log.debug("Created new custodian")

    return user


@transact
def create_custodian(store, request, language):
    """
    Currently this function simply serialize the custodian user.
    In the future this will serialize the admin model with its peculiatieis.
    """
    custodian = db_create_custodian(store, request, language)
    return user_serialize_user(custodian, language)


@transact
def create_custodian_user(store, request, language):
    custodian = db_create_custodian(store, request, language)
    return user_serialize_user(custodian, language)


def db_create_receiver(store, request, language):
    """
    Creates a new receiver
    Returns:
        (dict) the receiver descriptor
    """
    user = db_create_user(store, request, language)

    fill_localized_keys(request, models.Receiver.localized_strings, language)

    receiver = models.Receiver(request)

    # set receiver.id user.id
    receiver.id = user.id

    store.add(receiver)

    contexts = request.get('contexts', [])
    for context_id in contexts:
        context = models.Context.get(store, context_id)
        if not context:
            raise errors.ContextIdNotFound
        context.receivers.add(receiver)

    log.debug("Created new receiver")

    return receiver

@transact
def create_receiver_user(store, request, language):
    receiver = db_create_receiver(store, request, language)
    return user_serialize_user(receiver.user, language)


def create_user_picture(user_id):
    """
    Instantiate a copy of the default profile picture for a new user.
    By default take a picture and put in the receiver face,
    """
    try:
        shutil.copy(
            os.path.join(GLSettings.static_source, "default-profile-picture.png"),
            os.path.join(GLSettings.static_path, "%s.png" % user_id)
        )
    except Exception as excep:
        log.err("Unable to copy default user picture! %s" % excep.message)
        raise excep


def db_create_user(store, request, language):
    fill_localized_keys(request, models.User.localized_strings, language)

    password = request['password']
    if len(password) and password != GLSettings.default_password:
        security.check_password_format(password)
    else:
        password = GLSettings.default_password

    password_salt = security.get_salt(rstr.xeger('[A-Za-z0-9]{56}'))
    password_hash = security.hash_password(password, password_salt)

    user_dict = {
        'username': request['username'],
        'password': password_hash,
        'salt': password_salt,
        'role': request['role'],
        'state': u'enabled',
        'name': request['name'],
        'description': request['description'],
        'language': u'en',
        'timezone': 0,
        'password_change_needed': True,
        'mail_address': request['mail_address']
    }

    user = models.User(user_dict)

    # The various options related in manage PGP keys are used here.
    parse_pgp_options(user, request)

    create_user_picture(user.id)

    store.add(user)

    return user


def db_admin_update_user(store, user_id, request, language):
    """
    Updates the specified user.
    raises: globaleaks.errors.ReceiverIdNotFound` if the receiver does not exist.
    """
    user = models.User.get(store, user_id)

    if not user:
        raise errors.UserIdNotFound

    fill_localized_keys(request, models.User.localized_strings, language)

    user.name = request['name']
    user.description = request['description']

    user.state = request['state']
    user.password_change_needed = request['password_change_needed']
    user.mail_address = request['mail_address']

    user.language = request.get('language', GLSettings.memory_copy.default_language)
    user.timezone = request.get('timezone', GLSettings.memory_copy.default_timezone)

    password = request['password']
    if len(password):
        security.check_password_format(password)
        user.password = security.hash_password(password, user.salt)
        user.password_change_date = datetime_now()

    # The various options related in manage PGP keys are used here.
    parse_pgp_options(user, request)

    return user


@transact
def admin_update_user(store, user_id, request, language):
    user = db_admin_update_user(store, user_id, request, language)
    return user_serialize_user(user, language)


def db_get_user(store, user_id):
    """
    raises :class:`globaleaks.errors.UserIdNotFound` if the user does
    not exist.
    Returns:
        (dict) the user

    """
    user = models.User.get(store, user_id)

    if not user:
        raise errors.UserIdNotFound

    return user


@transact_ro
def get_user(store, user_id, language):
    user = db_get_user(store, user_id)
    return user_serialize_user(user, language)


@transact
def delete_user(store, user_id):
    user = db_get_user(store, user_id)

    user_picture = os.path.join(GLSettings.static_path, "%s.png" % user_id)
    if os.path.exists(user_picture):
        os.remove(user_picture)

    store.remove(user)


@transact_ro
def get_users_list(store, language):
    """
    Returns:
        (list) the list of users
    """
    user_list = []

    users = store.find(models.User)

    for user in users:
        user_list.append(user_serialize_user(user, language))

    return user_list


class UsersCollection(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self):
        """
        Return all the users.

        Parameters: None
        Response: adminUsersList
        Errors: None
        """
        response = yield get_users_list(self.request.language)

        self.set_status(200)
        self.finish(response)


class UserCreate(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def post(self):
        """
        Get the specified user.

        Request: AdminUserDesc
        Response: AdminUserDesc
        Errors: InvalidInputFormat, UserIdNotFound
        """
        request = self.validate_message(self.request.body,
                                        requests.AdminUserDesc)

        if request['role'] == 'receiver':
            response = yield create_receiver_user(request, self.request.language)
        elif request['role'] == 'custodian':
            response = yield create_custodian_user(request, self.request.language)
        elif request['role'] == 'admin':
            response = yield create_admin_user(request, self.request.language)

        GLApiCache.invalidate()

        self.set_status(201) # Created
        self.finish(response)


class UserInstance(BaseHandler):
    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def get(self, user_id):
        """
        Get the specified user.

        Parameters: user_id
        Response: AdminUserDesc
        Errors: InvalidInputFormat, UserIdNotFound
        """
        response = yield get_user(user_id, self.request.language)

        self.set_status(200)
        self.finish(response)

    @transport_security_check('admin')
    @authenticated('admin')
    @inlineCallbacks
    def put(self, user_id):
        """
        Update the specified user.

        Parameters: user_id
        Request: AdminUserDesc
        Response: AdminUserDesc
        Errors: InvalidInputFormat, UserIdNotFound
        """
        request = self.validate_message(self.request.body, requests.AdminUserDesc)

        response = yield admin_update_user(user_id, request, self.request.language)
        GLApiCache.invalidate()

        self.set_status(201)
        self.finish(response)

    @inlineCallbacks
    @transport_security_check('admin')
    @authenticated('admin')
    def delete(self, user_id):
        """
        Delete the specified user.

        Parameters: user_id
        Request: None
        Response: None
        Errors: InvalidInputFormat, UserIdNotFound
        """
        yield delete_user(user_id)

        GLApiCache.invalidate()

        self.set_status(200) # OK and return not content
        self.finish()
