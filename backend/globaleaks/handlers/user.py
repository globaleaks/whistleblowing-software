# -*- coding: UTF-8
# receiver
# ********
#
# Implement the classes handling the requests performed to /receiver/* URI PATH
# Used by receivers to update personal preferences and access to personal data

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.handlers.authentication import authenticated, transport_security_check
from globaleaks.handlers.base import BaseHandler
from globaleaks.rest import requests, errors
from globaleaks.rest.apicache import GLApiCache
from globaleaks.security import change_password, GLBPGP
from globaleaks.settings import transact, transact_ro, GLSettings
from globaleaks.utils.structures import Rosetta, get_localized_values
from globaleaks.utils.utility import log, datetime_to_ISO8601, datetime_now


def parse_pgp_options(user, request):
    """
    Used for parsing PGP key infos and fill related user configurations.

    @param user: the user orm object
    @param request: the dictionary containing the pgp infos to be parsed
    @return: None
    """
    new_pgp_key = request.get('pgp_key_public', None)
    remove_key = request.get('pgp_key_remove', False)

    # the default
    user.pgp_key_status = u'disabled'

    if remove_key:
        # In all the cases below, the key is marked disabled as request
        user.pgp_key_status = u'disabled'
        user.pgp_key_info = None
        user.pgp_key_public = None
        user.pgp_key_fingerprint = None
        user.pgp_key_expiration = None

    elif new_pgp_key:
        gnob = GLBPGP()

        try:
            result = gnob.load_key(new_pgp_key)

            log.debug("PGP Key imported: %s" % result['fingerprint'])

            user.pgp_key_status = u'enabled'
            user.pgp_key_info = result['info']
            user.pgp_key_public = new_pgp_key
            user.pgp_key_fingerprint = result['fingerprint']
            user.pgp_key_expiration = result['expiration']
        except:
            raise

        finally:
            # the finally statement is always called also if
            # except contains a return or a raise
            gnob.destroy_environment()


def user_serialize_user(user, language):
    """
    Serialize user description

    :param store: the store on which perform queries.
    :param username: the username of the user to be serialized
    :return: a serialization of the object
    """
    ret_dict = {
        'id': user.id,
        'username': user.username,
        'password': '',
        'old_password': u'',
        'salt': '',
        'role': user.role,
        'state': user.state,
        'last_login': datetime_to_ISO8601(user.last_login),
        'name': user.name,
        'description': user.description,
        'mail_address': user.mail_address,
        'language': user.language,
        'timezone': user.timezone,
        'password_change_needed': user.password_change_needed,
        'password_change_date': datetime_to_ISO8601(user.password_change_date),
        'pgp_key_info': user.pgp_key_info,
        'pgp_key_fingerprint': user.pgp_key_fingerprint,
        'pgp_key_public': user.pgp_key_public,
        'pgp_key_expiration': datetime_to_ISO8601(user.pgp_key_expiration),
        'pgp_key_status': user.pgp_key_status,
        'pgp_key_remove': False,
    }

    return get_localized_values(ret_dict, user, user.localized_strings, language)


@transact_ro
def get_user_settings(store, user_id, language):
    user = store.find(models.User, models.User.id == user_id).one()

    if not user:
        raise errors.UserIdNotFound

    return user_serialize_user(user, language)


def db_user_update_user(store, user_id, request, language):
    """
    Updates the specified user.
    This version of the function is specific forusers that with comparison admins
    admin can change only few things:
      - preferred language
      - preferred timezone
      - the password (with old password check)
      - pgp key
    raises: globaleaks.errors.ReceiverIdNotFound` if the receiver does not exist.
    """
    user = models.User.get(store, user_id)

    if not user:
        raise errors.UserIdNotFound

    user.language = request.get('language', GLSettings.memory_copy.default_language)
    user.timezone = request.get('timezone', GLSettings.memory_copy.default_timezone)

    new_password = request['password']
    old_password = request['old_password']

    if len(new_password) and len(old_password):
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
def update_user_settings(store, user_id, request, language):
    user = db_user_update_user(store, user_id, request, language)

    return user_serialize_user(user, language)


class UserInstance(BaseHandler):
    """
    This handler allow users to modify some of their fields:
        - language
        - timezone
        - password
        - notification settings
        - pgp key
    """
    @authenticated('*')
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: ReceiverReceiverDesc
        Errors: UserIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        user_status = yield get_user_settings(self.current_user.user_id,
                                              self.request.language)

        self.set_status(200)
        self.finish(user_status)


    @authenticated('*')
    @inlineCallbacks
    def put(self):
        """
        Parameters: None
        Request: UserUserDesc
        Response: UserUserDesc
        Errors: UserIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        request = self.validate_message(self.request.body, requests.UserUserDesc)

        user_status = yield update_user_settings(self.current_user.user_id,
                                                 request, self.request.language)
        self.set_status(200)
        self.finish(user_status)
