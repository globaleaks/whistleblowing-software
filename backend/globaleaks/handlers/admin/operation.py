# -*- coding: utf-8
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks.db import db_refresh_memory_variables
from globaleaks.db.appdata import load_appdata
from globaleaks.handlers.admin.node import db_admin_serialize_node
from globaleaks.handlers.admin.notification import db_get_notification
from globaleaks.handlers.operation import OperationHandler
from globaleaks.handlers.password_reset import db_generate_password_reset_token
from globaleaks.handlers.user import db_get_user, disable_2fa, get_user
from globaleaks.models import Config, InternalTip, User
from globaleaks.models.config import db_set_config_variable, ConfigFactory, ConfigL10NFactory
from globaleaks.orm import db_del, transact, tw
from globaleaks.rest import errors
from globaleaks.services.onion import set_onion_service_info, get_onion_service_info
from globaleaks.state import State
from globaleaks.utils.crypto import Base64Encoder, GCE
from globaleaks.utils.onion import generate_onion_service_v3
from globaleaks.utils.templating import Templating


class TempKey(object):
    def __init__(self, key):
        self.key = key
        self.expireCall = None


@transact
def check_hostname(session, tid, hostname):
    """
    Ensure the hostname does not collide across tenants or include an origin that it shouldn't.

    :param session: An ORM session
    :param tid: A tenant id
    :param hostname: The hostname to be evaluated
    """
    if hostname == '':
        return

    forbidden_endings = ['onion', 'localhost']

    for v in forbidden_endings:
        if hostname.endswith(v):
            raise errors.InputValidationError('Hostname contains a forbidden origin')

    existing_hostnames = {h.value for h in session.query(Config)
                                                  .filter(Config.tid != tid,
                                                          Config.var_name == 'hostname')}

    if hostname in existing_hostnames:
        raise errors.InputValidationError('Hostname already reserved')


@transact
def reset_submissions(session, tid, user_id):
    """
    Transaction to reset the submissions of the specified tenant

    :param session: An ORM session
    :param tid: A tenant ID
    """
    session.query(Config).filter(Config.tid == tid, Config.var_name == 'counter_submissions').update({'value': 0})

    db_del(session, InternalTip, InternalTip.tid==tid)

    State.log(tid=tid, type='reset_reports', user_id=user_id)


@transact
def toggle_escrow(session, tid, user_session, user_id):
    """
    Transaction to toggle key escrow access for user an user given its id

    :param session: An ORM session
    :param tid: A tenant ID
    :param user_session: The current user session
    :param user_id: The user for which togling the key escrow access
    """
    if user_session.user_id == user_id or not user_session.ek:
        return

    user = db_get_user(session, tid, user_id)
    if not user.crypto_pub_key:
        return

    if not user.crypto_escrow_prv_key:
        crypto_escrow_prv_key = GCE.asymmetric_decrypt(user_session.cc, Base64Encoder.decode(user_session.ek))
        user.crypto_escrow_prv_key = Base64Encoder.encode(GCE.asymmetric_encrypt(user.crypto_pub_key, crypto_escrow_prv_key))
    else:
        user.crypto_escrow_prv_key = ''


def db_reset_smtp_settings(session, tid):
    config = ConfigFactory(session, tid)
    config.set_val('smtp_server', 'mail.globaleaks.org')
    config.set_val('smtp_port', 587)
    config.set_val('smtp_username', 'globaleaks')
    config.set_val('smtp_password', 'globaleaks')
    config.set_val('smtp_source_email', 'notifications@globaleaks.org')
    config.set_val('smtp_security', 'TLS')
    config.set_val('smtp_authentication', True)


@transact
def reset_smtp_settings(session, tid):
    return db_reset_smtp_settings(session, tid)


@transact
def reset_templates(session, tid):
    ConfigL10NFactory(session, tid).reset('notification', load_appdata())


@transact
def generate_password_reset_token(session, tid, user_session, user_id):
    user = session.query(User).filter(User.tid == tid, User.id == user_id).one_or_none()
    if user is None:
        return

    db_generate_password_reset_token(session, user)

    if user_session.ek and user.crypto_pub_key:
        crypto_escrow_prv_key = GCE.asymmetric_decrypt(user_session.cc, Base64Encoder.decode(user_session.ek))

        if user_session.user_tid == 1:
            user_cc = GCE.asymmetric_decrypt(crypto_escrow_prv_key, Base64Encoder.decode(user.crypto_escrow_bkp1_key))
        else:
            user_cc = GCE.asymmetric_decrypt(crypto_escrow_prv_key, Base64Encoder.decode(user.crypto_escrow_bkp2_key))

        enc_key = GCE.derive_key(user.reset_password_token.encode(), user.salt)
        key = Base64Encoder.encode(GCE.symmetric_encrypt(enc_key, user_cc))
        State.TempKeys[user_id] = TempKey(key)


class AdminOperationHandler(OperationHandler):
    """
    This interface exposes the enable to configure and verify the platform hostname
    """
    check_roles = 'admin'
    invalidate_cache = True

    def reset_smtp_settings(self, req_args, *args, **kwargs):
        return reset_smtp_settings(self.request.tid)

    def disable_2fa(self, req_args, *args, **kwargs):
        return disable_2fa(self.request.tid, req_args['value'])

    def reset_user_password(self, req_args, *args, **kwargs):
        return generate_password_reset_token(self.request.tid,
                                             self.session,
                                             req_args['value'])

    @inlineCallbacks
    def reset_onion_private_key(self, req_args, *args, **kargs):
        hostname, key = generate_onion_service_v3()
        yield set_onion_service_info(self.request.tid, hostname, key)
        yield self.state.onion_service_job.add_onion_service(self.request.tid, hostname, key)
        yield self.state.onion_service_job.remove_unwanted_onion_services()

        onion_details = yield get_onion_service_info(self.request.tid)
        returnValue({
            'onionservice': onion_details[1]
        })

    def reset_submissions(self, req_args, *args, **kwargs):
        return reset_submissions(self.request.tid, self.session.user_id)

    @inlineCallbacks
    def set_hostname(self, req_args, *args, **kwargs):
        yield check_hostname(self.request.tid, req_args['value'])
        yield tw(db_set_config_variable, self.request.tid, 'hostname', req_args['value'])
        yield tw(db_refresh_memory_variables, [self.request.tid])
        self.state.tenant_cache[self.request.tid].hostname = req_args['value']

    @inlineCallbacks
    def test_mail(self, req_args, *args, **kwargs):
        tid = self.request.tid
        language = self.state.tenant_cache[tid].default_language

        user = yield get_user(tid,
                              self.session.user_id,
                              language)

        data = {
            'type': 'admin_test',
            'node': (yield tw(db_admin_serialize_node, tid, language)),
            'notification': (yield tw(db_get_notification, tid, language)),
            'user': user,
        }

        subject, body = Templating().get_mail_subject_and_body(data)

        yield self.state.sendmail(tid, user['mail_address'], subject, body)

    def toggle_escrow(self, req_args, *args, **kwargs):
        return toggle_escrow(self.request.tid, self.session, req_args['value'])

    def reset_templates(self, req_args):
        return reset_templates(self.request.tid)

    def operation_descriptors(self):
        return {
            'disable_2fa': (AdminOperationHandler.disable_2fa, {'value': str}),
            'reset_onion_private_key': (AdminOperationHandler.reset_onion_private_key, {}),
            'reset_smtp_settings': (AdminOperationHandler.reset_smtp_settings, {}),
            'reset_submissions': (AdminOperationHandler.reset_submissions, {}),
            'reset_user_password': (AdminOperationHandler.reset_user_password, {'value': str}),
            'set_hostname': (AdminOperationHandler.set_hostname, {'value': str}),
            'test_mail': (AdminOperationHandler.test_mail, {}),
            'toggle_escrow': (AdminOperationHandler.toggle_escrow, {'value': str}),
            'reset_templates': (AdminOperationHandler.reset_templates, {})
        }
