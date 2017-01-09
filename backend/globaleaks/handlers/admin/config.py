import base64
import os

from twisted.internet.defer import inlineCallbacks

from globaleaks import models
from globaleaks.orm import transact
from globaleaks.settings import GLSettings
from globaleaks.headers.Base import BaseHandler
from globaleaks.models.config import PrivateFactory
from globaleaks.rest.apicache import GLApiCache
from globaleaks.rest.api import requests
from globaleaks.rest import errors
from globaleaks.utils.utility import log


def check_ssl(priv_key, cert, chain):
    if (priv_key == 'throw'):
        raise errors.InvalidInputFormat('Dummy exception raised')
    return True


@transact
def configure_ssl(store, request):
    # TODO validate config params with SSL logic

    pk, cert, chain = request['priv_key'], request['cert'], request['chain']
    
    privFact = PrivateFactory(store)

    privFact.set_val('ssl_priv_key', pk)
    privFact.set_val('ssl_cert', cert)
    privFact.set_val('ssl_chain', chain)

    check_ssl(pk, cert, chain)


@transact
def delete_ssl(store):
    privFact = PrivateFactory(store)

    privFact.set_val('ssl_priv_key', u'')
    privFact.set_val('ssl_cert', u'')
    privFact.set_val('ssl_chain', u'')


class SSLSetupWizard(BaseHandler):

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def post(self):
        request = self.validate_message(self.request.body, requests.AdminSSLConfigDesc)

        try:
          yield configure_ssl(request)
        except Exception as e:
          log.err(e)
          self.set_status(400)
          return

        self.set_status(200)

    @BaseHandler.transport_security_check('admin')
    @BaseHandler.authenticated('admin')
    @inlineCallbacks
    def delete(self):
        try:
          yield delete_ssl()
        except Exception as e:
          log.err(e)
          self.set_status(400)
          return

        self.set_status(200)
