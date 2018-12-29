# -*- coding: utf-8
from six import text_type
from six.moves.urllib.parse import urlunsplit # pylint: disable=import-error

from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.web.client import readBody

from globaleaks.db import db_refresh_memory_variables
from globaleaks.handlers.operation import OperationHandler
from globaleaks.handlers.password_reset import generate_password_reset_token
from globaleaks.models import Config
from globaleaks.models.config import ConfigFactory, db_set_config_variable
from globaleaks.orm import transact, tw
from globaleaks.rest import errors
from globaleaks.services.onion import set_onion_service_info, get_onion_service_info


@transact
def check_hostname(session, tid, input_hostname):
    """
    Ensure the hostname does not collide across tenants or include an origin
    that it shouldn't.
    """
    if input_hostname == '':
        raise errors.InputValidationError('Hostname cannot be empty')

    root_hostname = ConfigFactory(session, 1).get_val(u'hostname')

    forbidden_endings = ['onion', 'localhost']
    if tid != 1 and root_hostname != '':
        forbidden_endings.append(root_hostname)

    for v in forbidden_endings:
        if input_hostname.endswith(v):
            raise errors.InputValidationError('Hostname contains a forbidden origin')

    existing_hostnames = {h.get_v() for h in session.query(Config) \
                                                    .filter(Config.tid != tid,
                                                            Config.var_name == u'hostname')}

    if input_hostname in existing_hostnames:
        raise errors.InputValidationError('Hostname already reserved')


@transact
def set_config_variable(session, tid, var, val):
    db_set_config_variable(session, tid, var, val)

    db_refresh_memory_variables(session, [tid])


class AdminOperationHandler(OperationHandler):
    """
    This interface exposes the enable to configure and verify the platform hostname
    """
    check_roles = 'admin'
    invalidate_cache = True

    @inlineCallbacks
    def set_hostname(self, req_args, *args, **kwargs):
        yield check_hostname(self.request.tid, req_args['value'])
        yield tw(db_set_config_variable, self.request.tid, u'hostname', req_args['value'])

    @inlineCallbacks
    def verify_hostname(self, req_args, *args, **kwargs):
        net_agent = self.state.get_agent()

        url = urlunsplit(('http', req_args['value'], 'robots.txt', None, None)).encode()

        resp = yield net_agent.request(b'GET', url)
        body = yield readBody(resp)

        server_h = resp.headers.getRawHeaders(b'Server', [None])[-1].lower()
        if not body.startswith(b'User-agent: *') or server_h != b'globaleaks':
            raise EnvironmentError('Response unexpected')

    def reset_user_password(self, req_args, *args, **kwargs):
        return generate_password_reset_token(self.state,
                                             self.request.tid,
                                             req_args['value'],
                                             allow_admin_reset=True)

    @inlineCallbacks
    def reset_onion_private_key(self, req_args, *args, **kargs):
        yield set_onion_service_info(self.request.tid, u'', u'')
        yield self.state.onion_service_job.add_hidden_service(self.request.tid, u'', u'')
        yield self.state.onion_service_job.remove_unwanted_hidden_services()

        onion_details = yield get_onion_service_info(self.request.tid)
        returnValue({
            'onionservice': onion_details[1]
        })

    def operation_descriptors(self):
        return {
            'set_hostname': (AdminOperationHandler.set_hostname, {'value': text_type}),
            'verify_hostname': (AdminOperationHandler.verify_hostname, {'value': text_type}),
            'reset_user_password': (AdminOperationHandler.reset_user_password, {'value': text_type}),
            'reset_onion_private_key': (AdminOperationHandler.reset_onion_private_key, {})
        }
