# -*- coding: utf-8
# user
# ********
#
# Implement the classes handling the requests performed to /user/* URI PATH

from globaleaks import models
from globaleaks.handlers.admin.modelimgs import db_get_model_img
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import requests
from globaleaks.security import change_password, parse_pgp_key
from globaleaks.state import State
from globaleaks.utils.structures import get_localized_values
from globaleaks.utils.utility import datetime_to_ISO8601, datetime_now, datetime_null


def parse_pgp_options(user, request):
    """
    Used for parsing PGP key infos and fill related user configurations.

    @param user: the user orm object
    @param request: the dictionary containing the pgp infos to be parsed
    @return: None
    """
    pgp_key_public = request['pgp_key_public']
    remove_key = request['pgp_key_remove']

    k = None
    if not remove_key and pgp_key_public:
        k = parse_pgp_key(pgp_key_public)

    if k is not None:
        user.pgp_key_public = k['public']
        user.pgp_key_fingerprint = k['fingerprint']
        user.pgp_key_expiration = k['expiration']
    else:
        user.pgp_key_public = ''
        user.pgp_key_fingerprint = ''
        user.pgp_key_expiration = datetime_null()


def user_serialize_user(store, user, language):
    """
    Serialize user description

    :param store: the store on which perform queries.
    :param username: the username of the user to be serialized
    :return: a serialization of the object
    """
    picture = db_get_model_img(store, user.tid, 'users', user.id)

    ret_dict = {
        'id': user.id,
        'username': user.username,
        'password': '',
        'old_password': u'',
        'salt': '',
        'role': user.role,
        'deletable': user.deletable,
        'state': user.state,
        'last_login': datetime_to_ISO8601(user.last_login),
        'name': user.name,
        'public_name': user.public_name,
        'description': user.description,
        'mail_address': user.mail_address,
        'language': user.language,
        'password_change_needed': user.password_change_needed,
        'password_change_date': datetime_to_ISO8601(user.password_change_date),
        'pgp_key_fingerprint': user.pgp_key_fingerprint,
        'pgp_key_public': user.pgp_key_public,
        'pgp_key_expiration': datetime_to_ISO8601(user.pgp_key_expiration),
        'pgp_key_remove': False,
        'picture': picture
    }

    return get_localized_values(ret_dict, user, user.localized_keys, language)


@transact
def get_user_settings(store, tid, user_id, language):
    user = models.db_get(store, models.User, models.User.id == user_id, tid=tid)

    return user_serialize_user(store, user, language)


def db_user_update_user(store, tid, user_id, request):
    """
    Updates the specified user.
    This version of the function is specific for users that with comparison with
    admins can change only few things:
      - preferred language
      - the password (with old password check)
      - pgp key
    raises: globaleaks.errors.ReceiverIdNotFound` if the receiver does not exist.
    """
    user = models.db_get(store, models.User, id=user_id, tid=tid)

    user.language = request.get('language', State.tenant_cache[tid].default_language)

    new_password = request['password']
    old_password = request['old_password']

    if new_password and old_password:
        user.password = change_password(user.password,
                                        old_password,
                                        new_password,
                                        user.salt)

        if user.password_change_needed:
            user.password_change_needed = False

        user.password_change_date = datetime_now()

    # The various options related in manage PGP keys are used here.
    parse_pgp_options(user, request)

    return user


@transact
def update_user_settings(store, tid, user_id, request, language):
    user = db_user_update_user(store, tid, user_id, request)

    return user_serialize_user(store, user, language)


class UserInstance(BaseHandler):
    """
    This handler allow users to modify some of their fields:
        - language
        - password
        - notification settings
        - pgp key
    """
    check_roles = {'admin', 'receiver', 'custodian'}
    invalidate_cache = True

    def get(self):
        """
        Parameters: None
        Response: ReceiverReceiverDesc
        Errors: UserIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        return get_user_settings(self.request.tid,
                                 self.current_user.user_id,
                                 self.request.language)

    def put(self):
        """
        Parameters: None
        Request: UserUserDesc
        Response: UserUserDesc
        Errors: UserIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        request = self.validate_message(self.request.content.read(), requests.UserUserDesc)

        return update_user_settings(self.request.tid,
                                    self.current_user.user_id,
                                    request,
                                    self.request.language)
