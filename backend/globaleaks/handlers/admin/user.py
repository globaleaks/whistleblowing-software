# -*- coding: UTF-8
#
#   user
#   *****
# Implementation of the User model functionalities
#
from globaleaks import models, security
from globaleaks.rest import errors
from globaleaks.security import GLBPGP
from globaleaks.settings import GLSettings, transact_ro
from globaleaks.third_party import rstr
from globaleaks.utils.structures import fill_localized_keys, get_localized_values
from globaleaks.utils.utility import log, datetime_now, datetime_null, datetime_to_ISO8601, uuid4


def admin_serialize_user(user, language):
    """
    Serialize user description

    :param store: the store on which perform queries.
    :param username: the username of the user to be serialized
    :return: a serialization of the object
    """
    ret_dict = {
        'username': user.username,
        'password': user.password,
        'salt': user.salt,
        'role': user.role,
        'state': user.state,
        'last_login': datetime_to_ISO8601(user.last_login),
        'language': user.language,
        'timezone': user.timezone,
        'password_change_needed': user.password_change_needed,
        'password_change_date': user.password_change_date
    }

    return get_localized_values(ret_dict, user, user.localized_strings, language)


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
        'username': uuid4(),
        'password': password_hash,
        'salt': password_salt,
        'role': u'receiver',
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

    store.add(user)

    return user


def db_update_user(store, user_id, request, language):
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
