# -*- coding: utf-8
#
# Handlers dealing with user preferences
from globaleaks import models
from globaleaks.handlers.admin.modelimgs import db_get_model_img
from globaleaks.handlers.base import BaseHandler
from globaleaks.orm import transact
from globaleaks.rest import errors, requests
from globaleaks.state import State
from globaleaks.utils.pgp import PGPContext
from globaleaks.utils.security import check_password, hash_password, generateRandomKey
from globaleaks.utils.structures import get_localized_values
from globaleaks.utils.utility import datetime_to_ISO8601, datetime_now, datetime_null


def parse_pgp_options(state, user, request):
    """
    Used for parsing PGP key infos and fill related user configurations.
    """
    pgp_key_public = request['pgp_key_public']
    remove_key = request['pgp_key_remove']

    k = None
    if not remove_key and pgp_key_public:
        pgpctx = PGPContext(state.settings.tmp_path)

        k = pgpctx.load_key(pgp_key_public)

    if k is not None:
        user.pgp_key_public = pgp_key_public
        user.pgp_key_fingerprint = k['fingerprint']
        user.pgp_key_expiration = k['expiration']
    else:
        user.pgp_key_public = ''
        user.pgp_key_fingerprint = ''
        user.pgp_key_expiration = datetime_null()


def user_serialize_user(session, user, language):
    """
    Serialize user description

    :param session: the session on which perform queries.
    :param username: the username of the user to be serialized
    :return: a serialization of the object
    """
    picture = db_get_model_img(session, 'users', user.id)
    user_tenants = db_get_usertenant_associations(session, user)

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
        'change_email_address': user.change_email_address,
        'language': user.language,
        'password_change_needed': user.password_change_needed,
        'password_change_date': datetime_to_ISO8601(user.password_change_date),
        'pgp_key_fingerprint': user.pgp_key_fingerprint,
        'pgp_key_public': user.pgp_key_public,
        'pgp_key_expiration': datetime_to_ISO8601(user.pgp_key_expiration),
        'pgp_key_remove': False,
        'picture': picture,
        'can_edit_general_settings': user.can_edit_general_settings,
        'tid': user.tid,
        'usertenant_assocations': user_tenants
    }

    return get_localized_values(ret_dict, user, user.localized_keys, language)


def serialize_usertenant_association(row):
    '''Serializes the UserTenant associations'''
    return {
        'user_id': row.user_id,
        'tenant_id': row.tenant_id
    }


@transact
def get_user_settings(session, tid, user_id, language):
    user = models.db_get(session, models.User, models.User.id == user_id, models.User.tid == tid)

    return user_serialize_user(session, user, language)


def db_user_update_user(session, state, tid, user_id, request):
    """
    Updates the specified user.
    This version of the function is specific for users that with comparison with
    admins can change only few things:
      - real name
      - email address
      - preferred language
      - the password (with old password check)
      - pgp key
    raises: globaleaks.errors.ResourceNotFound` if the receiver does not exist.
    """
    from globaleaks.handlers.admin.notification import db_get_notification
    from globaleaks.handlers.admin.node import db_admin_serialize_node

    user = models.db_get(session, models.User, models.User.id == user_id, models.User.tid == tid)

    user.language = request.get('language', State.tenant_cache[tid].default_language)
    user.name = request['name']
    new_password = request['password']
    old_password = request['old_password']

    if new_password:
        if user.password_change_needed:
            user.password_change_needed = False
        else:
            if not check_password(old_password,
                                  user.salt,
                                  user.password):
                raise errors.InvalidOldPassword

        user.password = hash_password(new_password, user.salt)
        user.password_change_date = datetime_now()

    # If the email address changed, send a validation email
    if request['mail_address'] != user.mail_address:
        user.change_email_address = request['mail_address']
        user.change_email_date = datetime_now()
        user.change_email_token = generateRandomKey(32)

        user_desc = user_serialize_user(session, user, user.language)

        template_vars = {
            'type': 'email_validation',
            'user': user_desc,
            'new_email_address': request['mail_address'],
            'validation_token': user.change_email_token,
            'node': db_admin_serialize_node(session, 1, user.language),
            'notification': db_get_notification(session, tid, user.language)
        }

        state.format_and_send_mail(session, tid, user_desc, template_vars)

    # If the platform allows users to change PGP keys, process it
    if State.tenant_cache[tid]['enable_user_pgp_key_upload'] is True:
        parse_pgp_options(state, user, request)

    return user


@transact
def update_user_settings(session, state, tid, user_id, request, language):
    user = db_user_update_user(session, state, tid, user_id, request)

    return user_serialize_user(session, user, language)



def db_get_usertenant_associations(session, user):
    usertenants = session.query(models.UserTenant) \
                         .filter(models.UserTenant.user_id == user.id)

    ret = [serialize_usertenant_association(usertenant) for usertenant in usertenants]

    ret.append({'user_id': user.id, 'tenant_id': user.tid})

    return ret


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
        return get_user_settings(self.request.tid,
                                 self.current_user.user_id,
                                 self.request.language)

    def put(self):
        request = self.validate_message(self.request.content.read(), requests.UserUserDesc)

        return update_user_settings(self.state,
                                    self.request.tid,
                                    self.current_user.user_id,
                                    request,
                                    self.request.language)