# -*- coding: utf-8
from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks.db import db_refresh_memory_variables
from globaleaks.handlers.operation import OperationHandler
from globaleaks.handlers.password_reset import generate_password_reset_token_by_user_id
from globaleaks.handlers.rtip import db_delete_itips
from globaleaks.handlers.user import db_get_user, disable_2fa
from globaleaks.models import Config, InternalTip
from globaleaks.models.config import db_set_config_variable
from globaleaks.orm import transact, tw
from globaleaks.rest import errors
from globaleaks.services.onion import set_onion_service_info, get_onion_service_info
from globaleaks.utils.crypto import Base64Encoder, GCE


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
def reset_submissions(session, tid):
    """
    Transaction to reset the submissions of the specified tenant

    :param session: An ORM session
    :param tid: A tenant ID
    """
    session.query(Config).filter(Config.tid == tid, Config.var_name == 'counter_submissions').update({'value': 0})

    itip_ids = [x[0] for x in session.query(InternalTip.id).filter(InternalTip.tid == tid)]

    db_delete_itips(session, itip_ids)


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


class AdminOperationHandler(OperationHandler):
    """
    This interface exposes the enable to configure and verify the platform hostname
    """
    check_roles = 'admin'
    invalidate_cache = True

    def disable_2fa(self, req_args, *args, **kwargs):
        return disable_2fa(self.request.tid, req_args['value'])

    @inlineCallbacks
    def set_hostname(self, req_args, *args, **kwargs):
        yield check_hostname(self.request.tid, req_args['value'])
        yield tw(db_set_config_variable, self.request.tid, 'hostname', req_args['value'])
        yield tw(db_refresh_memory_variables, [self.request.tid])
        self.state.tenant_cache[self.request.tid].hostname = req_args['value']

    def reset_user_password(self, req_args, *args, **kwargs):
        return generate_password_reset_token_by_user_id(self.request.tid,
                                                        req_args['value'])

    @inlineCallbacks
    def reset_onion_private_key(self, req_args, *args, **kargs):
        yield set_onion_service_info(self.request.tid, '', '')
        yield self.state.onion_service_job.add_hidden_service(self.request.tid, '', '')
        yield self.state.onion_service_job.remove_unwanted_hidden_services()

        onion_details = yield get_onion_service_info(self.request.tid)
        returnValue({
            'onionservice': onion_details[1]
        })

    def reset_submissions(self, req_args, *args, **kwargs):
        return reset_submissions(self.request.tid)

    def toggle_escrow(self, req_args, *args, **kwargs):
        return toggle_escrow(self.request.tid, self.current_user, req_args['value'])

    def operation_descriptors(self):
        return {
            'disable_2fa': (AdminOperationHandler.disable_2fa, {'value': str}),
            'reset_onion_private_key': (AdminOperationHandler.reset_onion_private_key, {}),
            'reset_submissions': (AdminOperationHandler.reset_submissions, {}),
            'reset_user_password': (AdminOperationHandler.reset_user_password, {'value': str}),
            'set_hostname': (AdminOperationHandler.set_hostname, {'value': str}),
            'toggle_escrow': (AdminOperationHandler.toggle_escrow, {'value': str})
        }
