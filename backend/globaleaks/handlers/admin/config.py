# -*- coding: utf-8
import urlparse

from twisted.internet.defer import inlineCallbacks
from twisted.internet.error import ConnectError
from twisted.web.client import readBody

from txsocksx.errors import HostUnreachable

from globaleaks.handlers.operation import OperationHandler
from globaleaks.handlers.admin.node import check_hostname
from globaleaks.models.config import NodeFactory
from globaleaks.orm import transact
from globaleaks.rest import errors

@transact
def set_config_variable(store, tid, var, val):
    NodeFactory(store, tid).set_val(var, val)


class AdminConfigHandler(OperationHandler):
    """
    This interface exposes the enable to configure and verify the platform hostname
    """
    check_roles = 'admin'
    invalidate_cache = True

    @inlineCallbacks
    def set_hostname(self, req_args, *args, **kwargs):
        yield check_hostname(self.request.tid, req_args['value'])
        yield set_config_variable(self.request.tid, u'hostname', req_args['value'])

    @inlineCallbacks
    def verify_hostname(self, req_args, *args, **kwargs):
        net_agent = self.state.get_agent()

        url = bytes(urlparse.urlunsplit(('http', req_args['value'], 'robots.txt', None, None)))

        try:
            resp = yield net_agent.request('GET', url)
            body = yield readBody(resp)

            server_h = resp.headers.getRawHeaders('Server', [None])[-1].lower()
            if not body.startswith('User-agent: *') or server_h != 'globaleaks':
                raise EnvironmentError('Response unexpected')

        except (EnvironmentError, ConnectError, HostUnreachable) as e:
            raise errors.ExternalResourceError()

    def operation_descriptors(self):
        return {
            'set_hostname': (AdminConfigHandler.set_hostname, {'value': unicode}),
            'verify_hostname': (AdminConfigHandler.verify_hostname, {'value': unicode})
        }
