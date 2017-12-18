# -*- coding: utf-8
import urlparse

from twisted.internet.defer import inlineCallbacks
from twisted.web.client import readBody

from globaleaks.handlers.operation import OperationHandler
from globaleaks.models.config import NodeFactory, Config
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.utils.utility import is_common_net_error


@transact
def check_hostname(store, tid, input_hostname):
    """
    Ensure the hostname does not collide across tenants or include an origin
    that it shouldn't.
    """
    if input_hostname == u'':
      return

    root_hostname = NodeFactory(store, 1).get_val(u'hostname')

    forbidden_endings = ['.onion', 'localhost']
    if tid != 1 and root_hostname != '':
        forbidden_endings.append(root_hostname)

    if reduce(lambda b, v: b or input_hostname.endswith(v), forbidden_endings, False):
        raise errors.InvalidModelInput('Hostname contains a forbidden origin')

    existing_hostnames = {h.get_v() for h in store.find(Config,
                                                        Config.tid != tid,
                                                        var_name=u'hostname')}

    if input_hostname in existing_hostnames:
        raise errors.InvalidModelInput('Hostname already reserved')


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

        except Exception as e:
            # Convert networking failures into a generic response
            if is_common_net_error(self.state.tenant_cache[self.request.tid], e):
                raise errors.ExternalResourceError()
            raise e

    def operation_descriptors(self):
        return {
            'set_hostname': (AdminConfigHandler.set_hostname, {'value': unicode}),
            'verify_hostname': (AdminConfigHandler.verify_hostname, {'value': unicode})
        }
