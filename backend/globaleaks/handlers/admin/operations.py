from twisted.internet.defer import inlineCallbacks, returnValue

from globaleaks import models
from globaleaks.handlers.base import OperationsHandler
from globaleaks.orm import transact
from globaleaks.rest import errors
from globaleaks.utils.utility import log

class OpsHandler(OperationsHandler):
    check_roles = '*'

    def operation_descriptors(self):
        return {
          'toggle_tor':   (self.toggle_tor, {}),
          'toggle_https': (self.toggle_https, {}),
          'dump_logs':    (self.dump_logs, {'period': int}),
        }
 
    @inlineCallbacks
    def toggle_tor(self, request, *args, **kwargs):
        print(self)
        print(request)
        print(args)
        print(kwargs)
        val = yield fake_db_operation()
        log.info('Yay I was called')
        returnValue('Tor activated')

    def toggle_https(self, request, *args, **kwargs):
        raise errors.ResourceNotFound('test failure')

    def dump_logs(self, request, *args, **kwargs):
        raise NotImplementedError

@transact
def fake_db_operation(store):
    return store.find(models.Mail).one()
