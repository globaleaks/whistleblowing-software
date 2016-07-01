# -*- coding: UTF-8
# User
# ********
#
# Implement the classes handling the requests performed to /user/* URI PATH

from twisted.internet.defer import inlineCallbacks
from cyclone.httpserver import HTTPConnection, HTTPRequest, _BadRequestException

from globaleaks import models, security
from globaleaks.orm import transact, transact_ro
from globaleaks.handlers.base import BaseHandler
from globaleaks.models import User
from globaleaks.rest import requests, errors
from globaleaks.settings import GLSettings
from globaleaks.utils.structures import get_localized_values
from globaleaks.utils.utility import log, datetime_to_ISO8601, datetime_now, datetime_null


def parse_pgp_options(user, request):
    """
    Used for parsing PGP key infos and fill related user configurations.

    @param user: the user orm object
    @param request: the dictionary containing the pgp infos to be parsed
    @return: None
    """
    pgp_key_public = request['pgp_key_public']
    remove_key = request['pgp_key_remove']

    if remove_key:
        # In all the cases below, the key is marked disabled as request
        user.pgp_key_public = ''
        user.pgp_key_fingerprint = ''
        user.pgp_key_expiration = datetime_null()

    elif pgp_key_public != '':
        gnob = security.GLBPGP()

        try:
            result = gnob.load_key(pgp_key_public)

            log.debug("PGP Key imported: %s" % result['fingerprint'])

            user.pgp_key_public = pgp_key_public
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
        'role': user.role,
        'deletable': user.deletable,
        'state': user.state,
        'last_login': datetime_to_ISO8601(user.last_login),
        'name': user.name,
        'public_name': user.public_name,
        'description': user.description,
        'mail_address': user.mail_address,
        'language': user.language,
        'timezone': user.timezone,
        'password_change_needed': user.password_change_needed,
        'password_change_date': datetime_to_ISO8601(user.password_change_date),
        'pgp_key_fingerprint': user.pgp_key_fingerprint,
        'pgp_key_public': user.pgp_key_public,
        'pgp_key_expiration': datetime_to_ISO8601(user.pgp_key_expiration),
        'pgp_key_remove': False,
        'ccrypto_key_public': user.ccrypto_key_public,
        'ccrypto_key_private': user.ccrypto_key_private,
        'picture': user.picture.data if user.picture is not None else ''
    }

    return get_localized_values(ret_dict, user, user.localized_keys, language)


@transact_ro
def get_user_settings(store, user_id, language):
    user = store.find(models.User, models.User.id == user_id).one()

    if not user:
        raise errors.UserIdNotFound

    return user_serialize_user(user, language)


def db_user_update_user(store, user_id, request, language):
    """
    Updates the specified user.
    This version of the function is specific for users that with comparison with
    admins can change only few things:
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
    @BaseHandler.authenticated('*')
    @inlineCallbacks
    def get(self):
        """
        Parameters: None
        Response: ReceiverReceiverDesc
        Errors: UserIdNotFound, InvalidInputFormat, InvalidAuthentication
        """
        user_status = yield get_user_settings(self.current_user.user_id,
                                              self.request.language)

        self.write(user_status)

    @BaseHandler.authenticated('*')
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

        self.write(user_status)


class PassKeyUpdateHandler(BaseHandler):
    """
    This handler exposes the receiver's private key used for client-side encryption
    for post only updates.
    """

    @BaseHandler.transport_security_check('*')
    @BaseHandler.authenticated('*')
    @inlineCallbacks
    def post(self):
        """
        Parameters: KeyUpdateDesc
        """
        request = self.validate_message(self.request.body, requests.PassKeyUpdateDesc)
        success = False 
        try:
          success = yield update_passkey(request, self.current_user.user_id)
        except Exception as err:
          log.warn('Update session threw %s' % err)
        finally:
          yield self.uniform_answers_delay()
          if not success:
            raise errors.ForbiddenOperation

@transact
def update_passkey(store, request, current_session_id):
    user = store.find(User, User.id == current_session_id).one()

    # TODO use side channel safe comparisions
    if (user is None or user.auth_token_hash != request['old_auth_token_hash']
        or request['old_auth_token_hash'] == request['new_auth_token_hash']):
        return False
    log.debug('Found User %s' % user.username)

    # This is the first time a user has ever logged in.
    if (user.ccrypto_key_public == "" and user.password_change_date == datetime_null()):
        if request['ccrypto_key_public'] == "": # TODO and invalid public key
            return False
        log.debug("Setting user's public CC key")
        user.ccrypto_key_public = request['ccrypto_key_public']
    else:
        log.debug("Only updating a user's private key")

    user.auth_token_hash = request['new_auth_token_hash']

    user.password_change_needed = False
    user.password_change_date = datetime_now()

    log.debug('Setting private key')
    # TODO perform validation on the passed pgp private key to assert
    # correspondence with the pub key.
    user.ccrypto_key_private = request['ccrypto_key_private']

    user.update()
    return True

